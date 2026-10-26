"""Copy file and folder paths from Nautilus context menus (Nautilus 4.1 API)."""

import os
import subprocess

import gi

gi.require_version("Nautilus", "4.1")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GObject, Nautilus


class CopyPathExtension(GObject.GObject, Nautilus.MenuProvider):
    @staticmethod
    def _address(info):
        location = info.get_location()
        return location.get_path() or location.get_uri()

    @staticmethod
    def _copy(_item, text):
        # wl-copy uses the compositor data-control protocol and keeps the text
        # available even after the Nautilus window has closed.
        if os.environ.get("WAYLAND_DISPLAY"):
            subprocess.run(
                ["/usr/bin/wl-copy", "--type", "text/plain;charset=utf-8"],
                input=text.encode("utf-8"), check=True,
            )
            return
        display = Gdk.Display.get_default()
        if display is not None:
            display.get_clipboard().set(text)

    def _item(self, name, label, text):
        item = Nautilus.MenuItem(
            name=name,
            label=label,
            tip="将完整路径复制到剪贴板；多选时每行一个路径",
            icon="edit-copy-symbolic",
        )
        item.connect("activate", self._copy, text)
        return item

    def get_file_items(self, files):
        if not files:
            return []
        text = "\n".join(self._address(info) for info in files)
        return [self._item("CopyPath::Selection", "复制路径", text)]

    def get_background_items(self, current_folder):
        if current_folder is None:
            return []
        return [self._item(
            "CopyPath::CurrentFolder", "复制当前文件夹路径",
            self._address(current_folder),
        )]
