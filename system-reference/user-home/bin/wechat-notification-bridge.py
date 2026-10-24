#!/usr/bin/python3
"""Fill missing WeChat notifications using only its navigation unread count.

No chat content, conversation names, contacts, screenshots, or chat databases
are read. Native notification bodies are never unpacked. Based on the local
desktop-config bridge's notification/action lifecycle, with an unread source.
"""
import logging
import re
import signal
import time
from collections import deque

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi, Gio, GLib, GLibUnix

NOTIFY = 'org.freedesktop.Notifications'
NOTIFY_PATH = '/org/freedesktop/Notifications'
MARKER = 'x-clavis-wechat-fallback'
GRACE = 1.5


class Bridge:
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.loop = GLib.MainLoop()
        self.monitor = None
        self.button = None
        self.pid = None
        self.previous = None
        self.pending_since = None
        self.pending_count = 0
        self.last_native = float('-inf')
        self.fallback_id = 0
        self.fallback_time = float('-inf')
        self.next_discovery = 0
        self.next_monitor = 0
        self.bus.signal_subscribe(NOTIFY, NOTIFY, None, NOTIFY_PATH, None,
            Gio.DBusSignalFlags.NONE, self.notification_signal, None)
        self.bus.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus',
            'NameOwnerChanged', '/org/freedesktop/DBus', NOTIFY,
            Gio.DBusSignalFlags.NONE, self.owner_changed, None)
        GLib.timeout_add(500, self.tick)
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.stop)
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.stop)

    def call(self, destination, path, interface, method, signature=None, args=()):
        return self.bus.call_sync(destination, path, interface, method,
            GLib.Variant(signature, args) if signature else None, None,
            Gio.DBusCallFlags.NONE, 1500, None).unpack()

    def connect_monitor(self):
        self.next_monitor = time.monotonic() + 10
        conn = None
        try:
            address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
            conn = Gio.DBusConnection.new_for_address_sync(address,
                Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
                Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
            conn.add_filter(self.observe_native, None)
            conn.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus.Monitoring', 'BecomeMonitor',
                GLib.Variant('(asu)', (["type='method_call',interface='org.freedesktop.Notifications',member='Notify'"], 0)),
                None, Gio.DBusCallFlags.NONE, 1500, None)
            self.monitor = conn
            logging.info('Native notification deduplication connected')
        except GLib.Error:
            if conn and not conn.is_closed():
                conn.close_sync(None)
            logging.warning('Native notification monitor unavailable; will retry')

    def observe_native(self, connection, message, incoming, data):
        if (message.get_interface() == NOTIFY and message.get_member() == 'Notify'
                and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL):
            body = message.get_body()
            if body and body.n_children() == 8:
                app = body.get_child_value(0).get_string().lower()
                hints = body.get_child_value(6)
                marker = hints.lookup_value(MARKER, None)
                desktop = hints.lookup_value('desktop-entry', None)
                entry = desktop.get_string().lower() if desktop else ''
                if not marker and (app in ('wechat', 'weixin', '微信')
                                   or entry in ('wechat', 'wechat.desktop')):
                    GLib.idle_add(self.native_arrived)
        # A monitor must never answer observed calls. Letting GDBus dispatch
        # them would send UnknownMethod and cause the bus to disconnect it.
        if incoming and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL:
            return None
        return message

    def native_arrived(self):
        self.last_native = time.monotonic()
        self.pending_since = None
        if self.last_native - self.fallback_time < 3:
            self.close_fallback()
        logging.info('Native WeChat notification observed; fallback suppressed')
        return GLib.SOURCE_REMOVE

    def discover_button(self):
        self.next_discovery = time.monotonic() + 3
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if not app or app.get_name().lower() not in ('wechat', 'weixin', '微信'):
                continue
            queue = deque([(app, 0)])
            visited = 0
            while queue and visited < 200:
                node, depth = queue.popleft()
                visited += 1
                if not node:
                    continue
                if node.get_role() == Atspi.Role.TOOL_BAR and node.get_name() in ('导航', 'Navigation'):
                    for j in range(node.get_child_count()):
                        button = node.get_child_at_index(j)
                        if button and button.get_role() == Atspi.Role.PUSH_BUTTON and button.get_name() in ('微信', 'WeChat'):
                            self.button, self.pid = button, app.get_process_id()
                            self.previous = None
                            self.pending_since = None
                            logging.info('Connected to WeChat unread counter')
                            return
                if depth < 6:
                    for j in range(node.get_child_count()):
                        queue.append((node.get_child_at_index(j), depth + 1))

    def read_count(self):
        self.button.clear_cache()
        if self.button.get_state_set().contains(Atspi.StateType.DEFUNCT):
            raise RuntimeError('Unread counter disconnected')
        description = self.button.get_description().strip()
        if not description or description in ('微信', 'WeChat'):
            return 0
        match = re.fullmatch(r'(\d+)\+?\s*(?:条新消息|new messages?)', description, re.I)
        return int(match.group(1)) if match else None

    def tick(self):
        now = time.monotonic()
        if (not self.monitor or self.monitor.is_closed()) and now >= self.next_monitor:
            self.connect_monitor()
        try:
            if not self.button and now >= self.next_discovery:
                self.discover_button()
            if not self.button:
                return GLib.SOURCE_CONTINUE
            count = self.read_count()
            if count is None:
                self.previous = None
                self.pending_since = None
                return GLib.SOURCE_CONTINUE
            if self.previous is not None and count > self.previous:
                if self.pending_since is None:
                    self.pending_since = now
                self.pending_count = count
            elif self.previous is not None and count < self.previous:
                self.pending_since = None
            self.previous = count
            if self.pending_since is not None and now - self.pending_since >= GRACE:
                if self.last_native >= self.pending_since - 1:
                    self.pending_since = None
                elif self.monitor and not self.monitor.is_closed():
                    self.deliver()
                    self.pending_since = None
        except (GLib.Error, RuntimeError, AttributeError):
            self.button = None
            self.previous = None
            self.pending_since = None
        return GLib.SOURCE_CONTINUE

    def close_fallback(self):
        if self.fallback_id:
            try:
                self.call(NOTIFY, NOTIFY_PATH, NOTIFY, 'CloseNotification', '(u)', (self.fallback_id,))
            except GLib.Error:
                pass
            self.fallback_id = 0

    def deliver(self):
        self.close_fallback()
        hints = {'desktop-entry': GLib.Variant('s', 'wechat'),
                 'urgency': GLib.Variant('y', 1),
                 'transient': GLib.Variant('b', False),
                 MARKER: GLib.Variant('b', True)}
        self.fallback_id = self.call(NOTIFY, NOTIFY_PATH, NOTIFY, 'Notify',
            '(susssasa{sv}i)', ('WeChat', 0, 'wechat',
            '微信有新消息', '点击打开微信查看。', ['default', '打开微信'], hints, 7000))[0]
        self.fallback_time = time.monotonic()
        logging.info('Posted fallback for an unread increase without a native notification')

    def notification_signal(self, connection, sender, path, interface, member, parameters, data):
        args = parameters.unpack()
        if not args or args[0] != self.fallback_id:
            return
        if member == 'NotificationClosed':
            self.fallback_id = 0
        elif member == 'ActionInvoked' and args[1] == 'default' and self.pid:
            names = self.call('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus', 'ListNames')[0]
            for name in names:
                if name.startswith(f'org.kde.StatusNotifierItem-{self.pid}-'):
                    try:
                        self.call(name, '/StatusNotifierItem', 'org.kde.StatusNotifierItem', 'Activate', '(ii)', (0, 0))
                    except GLib.Error:
                        logging.warning('WeChat tray activation unavailable')
                    break

    def owner_changed(self, *args):
        self.fallback_id = 0

    def stop(self):
        self.loop.quit()
        return GLib.SOURCE_REMOVE

    def run(self):
        self.connect_monitor()
        try:
            self.loop.run()
        finally:
            self.close_fallback()
            if self.monitor and not self.monitor.is_closed():
                self.monitor.close_sync(None)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    Bridge().run()
