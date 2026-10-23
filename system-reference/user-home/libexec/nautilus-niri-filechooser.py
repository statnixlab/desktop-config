#!/usr/bin/python3
"""Forward file dialogs to Nautilus without Niri's unsupported X11 parenting.

Nautilus 51.1/libgxdp dereferences a NULL x11_interop when Niri rejects the
GNOME file-chooser service channel (type 2). See GNOME/libgxdp issue #5:
https://gitlab.gnome.org/GNOME/libgxdp/-/work_items/5

Only x11: parents in a Niri session are cleared. Application identity,
Wayland parents, options, result variants and request cancellation pass
through unchanged. Existing Niri rules float org.gnome.Nautilus windows.
This does not implement drag-and-drop or modify QQ/Nautilus binaries.
"""

import os
import signal
import sys

from gi.repository import Gio, GLib

NAME = "org.freedesktop.impl.portal.desktop.nautilus_niri"
GNOME = "org.freedesktop.impl.portal.desktop.gnome"
FRONTEND = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"
CHOOSER = "org.freedesktop.impl.portal.FileChooser"
REQUEST = "org.freedesktop.impl.portal.Request"
LONG_TIMEOUT = 2147483647

METHOD_XML = """
  <method name="{name}">
    <arg type="o" name="handle" direction="in"/>
    <arg type="s" name="app_id" direction="in"/>
    <arg type="s" name="parent_window" direction="in"/>
    <arg type="s" name="title" direction="in"/>
    <arg type="a{{sv}}" name="options" direction="in"/>
    <arg type="u" name="response" direction="out"/>
    <arg type="a{{sv}}" name="results" direction="out"/>
  </method>
"""
CHOOSER_INFO = Gio.DBusNodeInfo.new_for_xml(
    '<node><interface name="' + CHOOSER + '">'
    + "".join(METHOD_XML.format(name=m) for m in ("OpenFile", "SaveFile", "SaveFiles"))
    + "</interface></node>"
).interfaces[0]
REQUEST_INFO = Gio.DBusNodeInfo.new_for_xml(
    '<node><interface name="' + REQUEST + '"><method name="Close"/></interface></node>'
).interfaces[0]


class FileChooser:
    def __init__(self):
        self.loop = GLib.MainLoop()
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.pending = {}
        self.niri = "niri" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower().split(":")
        self.registration = self.bus.register_object(PATH, CHOOSER_INFO, self.open, None, None)
        self.owner = Gio.bus_own_name_on_connection(
            self.bus, NAME, Gio.BusNameOwnerFlags.NONE, None, self.name_lost
        )

    def name_lost(self, *_):
        self.loop.quit()

    def authorized(self, sender):
        try:
            result = self.bus.call_sync(
                "org.freedesktop.DBus", "/org/freedesktop/DBus",
                "org.freedesktop.DBus", "GetNameOwner",
                GLib.Variant("(s)", (FRONTEND,)), GLib.VariantType.new("(s)"),
                Gio.DBusCallFlags.NONE, 3000, None,
            )
            return sender == result.unpack()[0]
        except GLib.Error:
            return False

    def open(self, connection, sender, path, interface, method, parameters, invocation):
        if not self.authorized(sender):
            invocation.return_dbus_error(
                "org.freedesktop.DBus.Error.AccessDenied", "Only the desktop portal may call this backend."
            )
            return
        handle = parameters.get_child_value(0).get_string()
        if handle in self.pending:
            invocation.return_dbus_error("org.freedesktop.portal.Error.InvalidArgument", "Duplicate handle.")
            return
        parent = parameters.get_child_value(2).get_string()
        if self.niri and parent.startswith("x11:"):
            # Keep the a{sv} and its nested values as GVariants, without unpacking.
            parameters = GLib.Variant.new_tuple(
                parameters.get_child_value(0), parameters.get_child_value(1),
                GLib.Variant("s", ""), parameters.get_child_value(3), parameters.get_child_value(4),
            )
        registration = self.bus.register_object(handle, REQUEST_INFO, self.close, None, None)
        self.pending[handle] = (registration, invocation, sender)
        self.bus.call(
            GNOME, PATH, CHOOSER, method, parameters, GLib.VariantType.new("(ua{sv})"),
            Gio.DBusCallFlags.NONE, LONG_TIMEOUT, None, self.finished, handle,
        )

    def finished(self, connection, result, handle):
        registration, invocation, _ = self.pending.pop(handle)
        self.bus.unregister_object(registration)
        try:
            invocation.return_value(connection.call_finish(result))
        except GLib.Error as error:
            invocation.return_dbus_error("org.freedesktop.portal.Error.Failed", error.message)

    def close(self, connection, sender, path, interface, method, parameters, invocation):
        request = self.pending.get(path)
        if request is None or sender != request[2]:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied", "Invalid request owner.")
            return
        self.bus.call(
            GNOME, path, REQUEST, "Close", None, GLib.VariantType.new("()"),
            Gio.DBusCallFlags.NONE, 5000, None, self.closed, invocation,
        )

    def closed(self, connection, result, invocation):
        try:
            invocation.return_value(connection.call_finish(result))
        except GLib.Error as error:
            remote = Gio.DBusError.get_remote_error(error)
            # The chooser may have completed just before cancellation arrived.
            if remote in ("org.freedesktop.DBus.Error.UnknownObject", "org.freedesktop.DBus.Error.UnknownMethod"):
                invocation.return_value(GLib.Variant("()", ()))
            else:
                invocation.return_dbus_error("org.freedesktop.portal.Error.Failed", error.message)

    def stop(self):
        for handle in list(self.pending):
            self.bus.call(
                GNOME, handle, REQUEST, "Close", None, None,
                Gio.DBusCallFlags.NONE, 1000, None, None, None,
            )
        self.bus.flush_sync(None)
        self.loop.quit()
        return False

    def run(self):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.stop)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.stop)
        self.loop.run()


if __name__ == "__main__":
    FileChooser().run()
