#!/usr/bin/python
"""Generate MIME icons from current GIO defaults, inheriting the user's theme."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk

THEMES = ('Clavis-Default-Apps', 'Clavis-Default-Apps-Refresh')
ICON_ROOT = Path.home() / '.local/share/icons'
STATE = Path.home() / '.local/state/default-app-icons'
BASE = 'Clavis-Reference'
INDEX = f'''[Icon Theme]
Name=Clavis Default App Icons
Comment=File icons follow default applications; other icons inherit Clavis Reference
Inherits={BASE}
Directories=scalable/mimetypes

[scalable/mimetypes]
Size=64
Type=Scalable
MinSize=8
MaxSize=512
Context=MimeTypes
'''


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sync()


def sync():
    # A standalone icon theme can resolve files without a display connection.
    theme = Gtk.IconTheme.new()
    theme.set_theme_name(BASE)
    desired = {}
    resolved = {}
    for mime in sorted(Gio.content_types_get_registered()):
        if mime.startswith(('inode/', 'x-scheme-handler/')):
            continue
        app = Gio.AppInfo.get_default_for_type(mime, False)
        icon = app.get_icon() if app else None
        if icon is None:
            continue
        key = icon.to_string()
        if key not in resolved:
            paint = theme.lookup_by_gicon(icon, 128, 1, Gtk.TextDirection.NONE, 0)
            file = paint.get_file() if paint else None
            path = file.get_path() if file else None
            resolved[key] = Path(path) if path and not Path(path).stem.startswith('image-missing') else None
        source = resolved[key]
        if source is None or not source.is_file() or source.suffix not in ('.png', '.svg', '.xpm'):
            continue
        name = mime.replace('/', '-')
        if name.endswith(('-x-generic', '-symbolic')) or '/' in name or name.startswith('.'):
            continue
        stat = source.stat()
        desired[name + source.suffix] = {
            'app': app.get_id(), 'source': str(source),
            'mtime': stat.st_mtime_ns, 'size': stat.st_size,
        }

    manifest = STATE / 'manifest.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    settings = Gio.Settings.new('org.gnome.desktop.interface')
    current = settings.get_string('icon-theme')
    active_root = ICON_ROOT / previous.get('theme', THEMES[0])
    icons = active_root / 'scalable/mimetypes'
    intact = icons.exists() and {p.name for p in icons.iterdir()} == set(desired)
    if intact:
        intact = all((icons / n).is_symlink() and os.readlink(icons / n) == d['source']
                     for n, d in desired.items())
    if desired == previous.get('icons') and intact and (active_root / 'index.theme').exists() and (active_root / 'index.theme').read_text() == INDEX:
        print(f'Unchanged: {len(desired)} MIME icons')
        return

    # Updating a symlink/cache in place leaves already-open GTK windows with
    # stale paintables. Build the inactive theme, then switch in one operation.
    # Both themes inherit the exact same Clavis base; no fallback-theme flash.
    target = THEMES[1] if current == THEMES[0] else THEMES[0]
    root = ICON_ROOT / target
    icons = root / 'scalable/mimetypes'
    icons.mkdir(parents=True, exist_ok=True)
    for name, data in desired.items():
        dest = icons / name
        if dest.is_symlink() and os.readlink(dest) == data['source']:
            continue
        temp = icons / ('.' + name + '.tmp')
        temp.unlink(missing_ok=True)
        temp.symlink_to(data['source'])
        temp.replace(dest)
    for path in icons.iterdir():
        if path.name not in desired:
            path.unlink()
    index = root / 'index.theme'
    index.write_text(INDEX)
    subprocess.run(['gtk-update-icon-cache', '-f', '-t', str(root)], check=True)
    os.utime(index, None)
    os.utime(root, None)
    # Respect any unrelated icon theme the user intentionally selects later.
    if current in THEMES:
        if not settings.set_string('icon-theme', target):
            raise RuntimeError('Cannot notify the desktop of the updated theme')
        Gio.Settings.sync()
    temp = STATE / 'manifest.json.tmp'
    temp.write_text(json.dumps({'theme': target, 'icons': desired}, ensure_ascii=False, indent=2) + '\n')
    temp.replace(manifest)
    print(f'Synced {len(desired)} MIME icons from default applications')


if __name__ == '__main__':
    main()
