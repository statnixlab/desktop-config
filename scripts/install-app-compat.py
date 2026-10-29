#!/usr/bin/env python3
"""Restore selected WPS/AB/WeChat compatibility settings; default mode only prints a plan."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def write_file(home, relative, data, mode, backup):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid target path')
    target = home / relative
    if not target.parent.resolve().is_relative_to(home.resolve()):
        raise ValueError('Destination escapes target home')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        saved = backup / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, saved, follow_symlinks=False)
    fd, temporary = tempfile.mkstemp(prefix='.' + target.name, dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def restore_settings(home, selected, backup):
    profiles = json.loads((ROOT / 'system-reference/app-compat/profiles.json').read_text())
    # AB and WeChat share a display service. Back up each destination once,
    # so selecting both cannot overwrite an original backup with restored data.
    files = dict.fromkeys(relative for profile in selected for relative in profiles[profile])
    for relative in files:
        source = ROOT / 'system-reference/app-compat/files' / relative
        data = source.read_text().replace('@HOME@', str(home)).encode()
        write_file(home, relative, data, source.stat().st_mode & 0o777, backup)
    if 'abdownloadmanager' in selected:
        relative = '.abdm/config/appSettings.json'
        existing = home / relative
        settings = json.loads(existing.read_text()) if existing.exists() else {}
        settings.update(json.loads((ROOT / 'system-reference/app-compat/abdownloadmanager-settings.json').read_text()))
        write_file(home, relative, (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode(), 0o600, backup)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wps', action='store_true')
    parser.add_argument('--abdownloadmanager', action='store_true')
    parser.add_argument('--wechat', action='store_true')
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--build-root', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    selected = [name for name in ['wps', 'abdownloadmanager', 'wechat'] if getattr(args, name)]
    if not selected:
        parser.error('Choose --wps, --abdownloadmanager and/or --wechat')
    home = args.target_home.expanduser().absolute()
    if any(char in str(home) for char in '\n\r"\'`$\\'):
        parser.error('Unsupported characters in target home')
    print('Profiles:', ', '.join(selected), '->', home)
    print('Build requirements: Rust, GCC, pkgconf, clang, libxcb, xcb-util-cursor, xorg-xwayland, jq, xorg-xrdb')
    if not args.apply:
        print('Plan only; add --apply after installing the applications and build requirements.')
        return
    if platform.machine() != 'x86_64':
        parser.error('These compatibility builds were verified on x86_64 only')
    if home.resolve() == Path.home().resolve():
        for profile, executable in [('wps', '/usr/bin/wps'),
                                    ('abdownloadmanager', '/opt/abdownloadmanager/bin/ABDownloadManager'),
                                    ('wechat', '/opt/wechat/wechat')]:
            if profile in selected and not Path(executable).is_file():
                parser.error('Install the application first: ' + executable)
        if 'abdownloadmanager' in selected:
            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    executable = (entry / 'exe').resolve(strict=True)
                except OSError:
                    continue
                if str(executable).startswith('/opt/abdownloadmanager/'):
                    parser.error('Quit AB Download Manager before updating its saved settings')
    spec = importlib.util.spec_from_file_location('bridge_build', ROOT / 'scripts/build-app-compat.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_root = args.build_root or home / '.cache/desktop-config/build'
    backup = home / '.local/state/desktop-config-backups' / datetime.now().strftime('apps-%Y%m%d-%H%M%S-%f')
    for kind in dict.fromkeys('wps' if profile == 'wps' else 'chat' for profile in selected):
        binary = Path('.local/libexec') / ('xwayland-satellite-wps' if kind == 'wps' else 'xwayland-satellite-hidpi')
        if (home / binary).is_file():
            saved = backup / binary
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(home / binary, saved)
        module.build(kind, build_root / ('xwayland-' + kind), home)
    if 'wps' in selected:
        metadata = json.loads((ROOT / 'system-reference/wps-compat/sticky-toolbar.json').read_text())
        library = Path('/usr/lib/office6/libkshell.so')
        if home.resolve() == Path.home().resolve() and library.is_file():
            with library.open('rb') as stream:
                compatible = hashlib.file_digest(stream, 'sha256').hexdigest() == metadata['library_sha256']
            if not compatible:
                print('WPS library differs: the launcher will leave the toolbar hook disabled.')
        with tempfile.TemporaryDirectory(prefix='wps-hook-') as temporary:
            output = Path(temporary) / 'libwps-sticky-toolbar.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-o', str(output),
                            str(ROOT / 'system-reference/wps-compat/sticky-toolbar.c'), '-ldl'], check=True)
            write_file(home, '.local/lib/wps-compat/libwps-sticky-toolbar.so', output.read_bytes(), 0o755, backup)
    restore_settings(home, selected, backup)
    if home.resolve() == Path.home().resolve():
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        if 'abdownloadmanager' in selected:
            subprocess.run([str(home / '.local/libexec/abdownloadmanager-native-path')], check=True)
            subprocess.run(['systemctl', '--user', 'enable', '--now', 'abdownloadmanager-native-path.path'], check=True)
    print('Restored. Backup:', backup)
    print('Open the applications normally. Dedicated displays are used only with uniform 200% Niri scaling.')
    if 'wechat' in selected:
        print('Fully quit and reopen WeChat to use the new launcher; the installer does not restart it.')


if __name__ == '__main__':
    main()
