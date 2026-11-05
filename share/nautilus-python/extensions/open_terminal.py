"""Open Kitty at a folder or a selected file's parent (Nautilus 4.1)."""

import logging
import os
import subprocess

import gi

gi.require_version("Nautilus", "4.1")
from gi.repository import GObject, Nautilus


class OpenTerminalExtension(GObject.GObject, Nautilus.MenuProvider):
    @staticmethod
    def _directory(info):
        location = info.get_location()
        if not info.is_directory():
            location = location.get_parent()
        if location is None:
            return None
        path = location.get_path()
        return path if path and os.path.isdir(path) else None

    @staticmethod
    def _open(_item, directory):
        try:
            # Pass the path as an argument, never as shell source. --detach
            # lets Kitty outlive the file manager without a child-process wait.
            subprocess.run(
                ["/usr/bin/kitty", "--detach", "--directory", directory],
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            logging.exception("Unable to open Kitty in %s", directory)

    def _item(self, name, directory):
        item = Nautilus.MenuItem(
            name=name,
            label="在此处打开终端",
            tip="在此目录打开 Kitty 终端",
            icon="utilities-terminal-symbolic",
        )
        item.connect("activate", self._open, directory)
        return [item]

    def get_file_items(self, files):
        if len(files) != 1:
            return []
        directory = self._directory(files[0])
        return self._item("OpenTerminal::Selection", directory) if directory else []

    def get_background_items(self, current_folder):
        if current_folder is None:
            return []
        directory = self._directory(current_folder)
        return self._item("OpenTerminal::CurrentFolder", directory) if directory else []
