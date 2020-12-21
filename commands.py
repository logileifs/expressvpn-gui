import re
import subprocess
import http.client as httplib


def _escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")

    return ansi_escape.sub("", line)


def _remove_whitespace(string, num=2):
    return re.split(r"\s{" + str(num) + ",}", string)


def _parse_all_locations():
    output = subprocess.check_output("expressvpn list all", shell=True)
    result = output.decode().split("\n")
    results = [_remove_whitespace(el) for el in result]
    output = []
    start_key = 0

    for key, element in enumerate(results):
        new_el = []
        element = list(filter(None, element))

        for el in element:
            el_break = el.split(") ", 1)[-1]
            new_el.append(el_break)

            if el_break.startswith("smart"):
                start_key = key

        if new_el:
            output.append(new_el)

    return output[start_key:]


def _get_locations_dict():
    output = _parse_all_locations()
    locations = {}

    for element in output:
        location = (
            element[-1].strip() if element[-1].strip() != "Y" else element[-2].strip()
        )
        key = element[0].strip()
        locations[location] = key

    return locations


def get_locations_list():
    output = _parse_all_locations()
    locations = []

    for element in output:
        location = (
            element[-1].strip() if element[-1].strip() != "Y" else element[-2].strip()
        )
        locations.append(location)

    locations.sort()

    return locations


def get_protocol_list():
    output = subprocess.check_output("expressvpn protocol --list", shell=True)
    result = output.decode().split("\n")

    return [protocol for protocol in result if protocol]


def get_preferences_dict():
    output = subprocess.check_output("expressvpn preferences", shell=True)
    result = output.decode().split("\n")
    preferences = {}

    for element in result:
        if not element:
            continue
        preference = _remove_whitespace(element, 1)
        preferences[preference[0]] = preference[1]

    return preferences


def set_network_lock(lock_type="default"):
    subprocess.Popen(
        [f"expressvpn preferences set network_lock {lock_type}"], shell=True
    )


def set_protocol(protocol_type="default"):
    subprocess.Popen([f"expressvpn protocol {protocol_type}"], shell=True)


def get_location_key(location):
    data = _get_locations_dict()
    key = data.get(location, "smart")

    return key


def check_expressvpn():
    output = subprocess.check_output("expressvpn -v", shell=True)
    result = _escape_ansi(output.decode())

    if result.startswith("expressvpn version"):
        return True

    return False


def check_connection():
    conn = httplib.HTTPConnection("www.example.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()


def connect_command(key):
    subprocess.Popen([f"expressvpn connect {key}"], shell=True)


def disconnect_command():
    subprocess.Popen(["expressvpn disconnect"], shell=True)


def is_activated():
    output = subprocess.check_output("expressvpn status", shell=True)
    result = _escape_ansi(output.decode())

    if "Not Activated" in result:
        return False

    return True


def is_connected():
    output = subprocess.check_output("expressvpn status", shell=True)
    result = _escape_ansi(output.decode())

    if "Connected to" in result:
        return True

    return False
