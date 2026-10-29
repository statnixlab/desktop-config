#!/usr/bin/env python3
"""Restore this portable desktop snapshot. Default mode only prints a plan."""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    manifest = json.loads((root / 'manifest.json').read_text())
    actual = {str(p.relative_to(root)) for directory in ['config', 'share', 'lib', 'libexec', 'bin', 'rime', 'assets', 'hardware', 'system-reference', 'patches', 'components']
              for p in (root / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    actual.add('sources.lock.json')
    if actual != set(manifest['sha256']):
        raise ValueError('Snapshot file inventory differs from manifest')
    for relative, digest in manifest['sha256'].items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Invalid snapshot path: {relative}')
        with path.open('rb') as stream:
            actual_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual_digest != digest:
            raise ValueError(f'Snapshot checksum mismatch: {relative}')


def plan(target_home, same_hardware=False, root=ROOT, keep_target_hardware=False):
    result = {}
    for source_dir, target_dir in [('config', '.config'), ('share', '.local/share'),
                                   ('lib', '.local/lib'), ('libexec', '.local/libexec'), ('bin', '.local/bin'),
                                   ('rime', '.local/share/fcitx5/rime')]:
        for path in sorted((root / source_dir).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            relative = Path(target_dir) / path.relative_to(root / source_dir)
            result[relative] = (path, path.stat().st_mode & 0o777)
    avatar = root / 'assets/avatar'
    if avatar.exists():
        result[Path('.face')] = (avatar, 0o600)
    for path in (root / 'assets').glob('wallpaper.*'):
        result[Path('Pictures/Wallpapers/current' + path.suffix)] = (path, 0o644)
    if same_hardware:
        result[Path('.config/niri/clavis/outputs.kdl')] = (root / 'hardware/outputs.kdl', 0o644)
        result[Path('.config/clavis/primary-display.json')] = (root / 'hardware/primary-display.json', 0o600)
    rendered = {}
    for relative, (source, mode) in result.items():
        if keep_target_hardware and relative in [Path('.config/niri/clavis/outputs.kdl'),
                                                Path('.config/clavis/primary-display.json'),
                                                Path('.config/niri/clavis/mouse.kdl')]:
            if (target_home / relative).exists():
                continue
        data = source.read_bytes()
        if b'\0' not in data:
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                pass
            else:
                data = text.replace('@HOME@', str(target_home)).encode('utf-8')
        if relative == Path('.config/clavis/ui-preferences.json') and same_hardware:
            settings = json.loads(data)
            settings.update(json.loads((root / 'hardware/monitor-metrics.json').read_text()))
            data = (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode()
        if relative == Path('.config/clavis/ui-preferences.json') and keep_target_hardware:
            current = target_home / relative
            if current.is_file():
                settings = json.loads(data)
                previous = json.loads(current.read_text())
                for key in ['systemMonitorGpuId', 'systemMonitorDiskDevice', 'systemMonitorNetworkInterface',
                            'storageCapacityDiskDevice']:
                    if key in previous:
                        settings[key] = previous[key]
                data = (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode()
        if not same_hardware and relative in [Path('.config/gtk-3.0/settings.ini'), Path('.config/gtk-4.0/settings.ini')]:
            data = b'\n'.join(line for line in data.splitlines() if not line.startswith(b'gtk-xft-dpi=')) + b'\n'
            current = target_home / relative
            if keep_target_hardware and current.is_file():
                data += b''.join(line + b'\n' for line in current.read_bytes().splitlines()
                                 if line.startswith(b'gtk-xft-dpi='))
        if not same_hardware and relative == Path('.config/fcitx5/x11-dpi.Xresources'):
            data = b'! Set Xft.dpi here after choosing scaling for this computer.\n'
            if keep_target_hardware and (target_home / relative).is_file():
                data = (target_home / relative).read_bytes()
        if relative.suffix == '.json':
            json.loads(data)
        rendered[relative] = (data, mode)
    return rendered


def destination(target_home, relative):
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Invalid destination: {relative}')
    path = target_home / relative
    if not path.parent.resolve().is_relative_to(target_home.resolve()):
        raise ValueError(f'Destination parent escapes selected home: {path}')
    if path.exists() and path.is_dir():
        raise ValueError(f'A directory occupies a file destination: {path}')
    return path


def restore(target_home, same_hardware=False, apply=False, root=ROOT, keep_target_hardware=False):
    target_home = target_home.expanduser().absolute()
    if any(char in str(target_home) for char in '\n\r"\'`$\\'):
        raise ValueError('The target path must not contain quotes, shell substitutions or line breaks')
    verify(root)
    if same_hardware and keep_target_hardware:
        raise ValueError('Choose source hardware or target hardware, not both')
    files = plan(target_home, same_hardware, root, keep_target_hardware)
    # Check every destination before touching any file.
    for relative in files:
        destination(target_home, relative)
    hardware = 'target preserved' if keep_target_hardware else 'source preserved' if same_hardware else 'reset'
    print(f'{len(files)} files -> {target_home}; hardware={hardware}')
    if not apply:
        print('Plan only. Add --apply to restore. Existing files will be backed up.')
        return None
    active_units = []
    if target_home.resolve() == Path.home().resolve():
        for unit in ['clavis-shell.service', 'clavis-launchpad.service', 'nyx-dock.service', 'fcitx5-niri.service', 'nyx-theme-sync.path', 'nyx-theme-sync.service']:
            if subprocess.run(['systemctl', '--user', 'is-active', '--quiet', unit], check=False).returncode == 0:
                active_units.append(unit)
        # Fcitx may have been started by desktop autostart rather than this unit.
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                if entry.stat().st_uid == os.getuid() and (entry / 'comm').read_text().strip() == 'fcitx5':
                    if 'fcitx5-niri.service' not in active_units:
                        active_units.append('fcitx5 (desktop autostart)')
                    break
            except (OSError, UnicodeError):
                continue
        if active_units:
            raise RuntimeError('Stop these services before restoring to an active desktop: ' + ', '.join(active_units))
    target_home.mkdir(parents=True, exist_ok=True)
    destination(target_home, Path('.local/state/desktop-config-backups/.guard'))
    backup_root = target_home / '.local/state/desktop-config-backups'
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
    # LevelDB snapshots must replace whole databases, never merge stale WAL/SST files.
    databases = {Path(*relative.parts[:index + 1]) for relative in files
                 for index, part in enumerate(relative.parts) if part.endswith('.userdb')}
    for relative in sorted(databases):
        path = destination(target_home, relative / '.guard').parent
        if path.exists():
            old = backup / relative
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(old))
    for relative, (data, mode) in files.items():
        path = destination(target_home, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink():
            old = backup / relative
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, old, follow_symlinks=False)
        fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.chmod(temporary, mode)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
    print(f'Restored. Previous files: {backup}')
    print('Next: build-niri.sh, install-icon-theme.sh, build-clavis.sh, build-launchpad.sh, then enable-services.sh.')
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    hardware = parser.add_mutually_exclusive_group()
    hardware.add_argument('--same-hardware', action='store_true', help='Use hardware settings from the source snapshot')
    hardware.add_argument('--keep-target-hardware', action='store_true', help='Keep this target computer monitor layout, mouse, metric bindings and DPI')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    restore(args.target_home, args.same_hardware, args.apply, keep_target_hardware=args.keep_target_hardware)


if __name__ == '__main__':
    main()
