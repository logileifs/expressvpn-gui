import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf
from time import sleep

from commands import (
    check_connection,
    check_expressvpn,
    connect_command,
    disconnect_command,
    get_location_key,
    get_locations_list,
    get_protocol_list,
    get_preferences_dict,
    is_activated,
    is_connected,
    set_network_lock,
    set_protocol,
)

DIR = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(DIR, "icon.png")
LOGO = os.path.join(DIR, "logo.png")
TITLE = "ExpressVPN GUI"


class AppForm(Gtk.Window):
    def __init__(self):
        super(Gtk.Window, self).__init__(title=TITLE)
        # Create UI elements
        self.set_default_size(400, 500)
        self.set_resizable(False)
        self.set_icon_from_file(ICON)
        self.grid = Gtk.Grid(
            orientation=Gtk.Orientation.VERTICAL,
            column_spacing=10,
            row_spacing=10,
            margin=60,
        )
        self.connect_button = Gtk.Button()
        self.connect_handler = None
        self.location_label = Gtk.Label()
        self.location_combo = Gtk.ComboBoxText()
        self.logo = GdkPixbuf.Pixbuf.new_from_file(LOGO)
        self.logo_image = Gtk.Image()
        self.protocol_label = Gtk.Label()
        self.protocol_combo = Gtk.ComboBoxText()
        self.network_lock_combo = Gtk.ComboBoxText()
        # Event handlers
        self.connect("destroy", self._close_event)
        # Configure App
        self._configure()

    def _configure(self):
        preferences = get_preferences_dict()
        self._connect_button_toggle()
        self.connect_button.set_property("height-request", 48)
        self.network_lock_combo.set_property("height-request", 32)
        for item in ["default", "strict", "off"]:
            self.network_lock_combo.append(item, item)
        self.network_lock_combo.set_active_id(preferences["network_lock"])
        self.network_lock_combo.connect("changed", self._network_lock_change)
        self.protocol_label.set_label("Protocol and network lock:")
        self.protocol_combo.set_property("height-request", 32)
        for item in get_protocol_list():
            self.protocol_combo.append(item, item)
        self.protocol_combo.set_active_id(preferences["preferred_protocol"])
        self.protocol_combo.connect("changed", self._protocol_change)
        if is_connected():
            self.network_lock_combo.set_sensitive(False)
            self.protocol_combo.set_sensitive(False)
        self.location_label.set_label("Select location:")
        self.location_combo.set_property("height-request", 32)
        for item in get_locations_list():
            self.location_combo.append_text(item)
        self.location_combo.set_active(0)
        self.logo = self.logo.scale_simple(280, 200, GdkPixbuf.InterpType.BILINEAR)
        self.logo_image = self.logo_image.new_from_pixbuf(self.logo)
        self.protocol_label.set_margin_top(20)
        self._configure_grid()
        self.add(self.grid)

    def _configure_grid(self):
        self.grid.set_margin_top(40)
        self.grid.set_margin_bottom(40)
        self.grid.attach(self.logo_image, 0, 0, 1, 1)
        self.grid.attach_next_to(
            self.protocol_label, self.logo_image, Gtk.PositionType.BOTTOM, 1, 1
        )
        box = Gtk.Box(spacing=10, homogeneous=True)
        box.pack_start(self.protocol_combo, True, True, 0)
        box.pack_start(self.network_lock_combo, True, True, 0)
        self.grid.attach_next_to(
            box, self.protocol_label, Gtk.PositionType.BOTTOM, 1, 1
        )
        self.grid.attach_next_to(
            self.location_label, box, Gtk.PositionType.BOTTOM, 1, 1
        )
        self.grid.attach_next_to(
            self.location_combo, self.location_label, Gtk.PositionType.BOTTOM, 1, 1
        )
        self.grid.attach_next_to(
            self.connect_button, self.location_combo, Gtk.PositionType.BOTTOM, 1, 1
        )

    def _network_lock_change(self, _):
        set_network_lock(self.network_lock_combo.get_active_text())

    def _protocol_change(self, _):
        set_protocol(self.protocol_combo.get_active_text())

    def _connect_button_toggle(self):
        if is_connected():
            self.connect_button.set_label("Disconnect")
            try:
                if self.connect_handler:
                    self.connect_button.disconnect(self.connect_handler)
            except RuntimeError:
                pass
            self.connect_handler = self.connect_button.connect(
                "clicked", self._disconnect_vpn
            )
        else:
            self.connect_button.set_label("Connect")
            try:
                if self.connect_handler:
                    self.connect_button.disconnect(self.connect_handler)
            except RuntimeError:
                pass
            self.connect_handler = self.connect_button.connect(
                "clicked", self._connect_vpn
            )

    def _connect_vpn(self, _):
        location = self.location_combo.get_active_text()
        self.connect_button.set_label("Connecting...")
        self.connect_button.set_sensitive(False)
        self.network_lock_combo.set_sensitive(False)
        self.protocol_combo.set_sensitive(False)
        self.location_combo.set_sensitive(False)
        self.connect_button.set_sensitive(False)
        self.grid.queue_draw()
        connect_command(get_location_key(location))

        while not is_connected():
            self._sleep_1s()

        self._connect_button_toggle()
        self.connect_button.set_sensitive(True)

    def _disconnect_vpn(self, _):
        self.connect_button.set_label("Disconnecting...")
        self.connect_button.set_sensitive(False)
        self.grid.queue_draw()
        disconnect_command()

        while is_connected():
            self._sleep_1s()

        self._connect_button_toggle()
        self.connect_button.set_sensitive(True)
        self.network_lock_combo.set_sensitive(True)
        self.protocol_combo.set_sensitive(True)
        self.location_combo.set_sensitive(True)

    def _sleep_1s(self):
        for i in range(10):
            sleep(0.1)
            self._update_gui()

    @staticmethod
    def _update_gui():
        while Gtk.events_pending():
            Gtk.main_iteration()

    @staticmethod
    def _close_event(_):
        if is_connected():
            disconnect_command()
        Gtk.main_quit()


def _check_requirements():
    win = Gtk.Window(title=TITLE)
    win.set_resizable(False)
    win.set_icon_from_file(ICON)
    win.connect("destroy", Gtk.main_quit)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
    ok_button = Gtk.Button(label="OK", image=Gtk.Image(stock=Gtk.STOCK_OK))
    ok_button.connect("clicked", Gtk.main_quit)
    text = Gtk.Label()
    box.add(text)
    box.add(ok_button)
    win.add(box)

    if not check_connection():
        text.set_label("Please check your internet connection")
        return win

    if not check_expressvpn():
        text.set_label("Please install expressvpn in order to use GUI")
        return win

    if not is_activated():
        text.set_label("Please activate expressvpn in order to use GUI")
        return win

    return


if __name__ == "__main__":
    error = _check_requirements()
    if error:
        error.show_all()
    else:
        window = AppForm()
        window.show_all()
    Gtk.main()
