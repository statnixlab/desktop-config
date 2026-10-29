#!/usr/bin/env python3
"""Build a pinned WPS, chat/AB or independent WeChat XWayland bridge."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build(profile, source_dir, target_home, prepare_only=False):
    directory = {'wps': 'wps-compat', 'chat': 'xwayland-satellite', 'wechat': 'wechat-compat'}[profile]
    record = json.loads((ROOT / 'system-reference' / directory / 'source.json').read_text())
    spec = importlib.util.spec_from_file_location('prepare_source', ROOT / 'scripts/prepare-niri.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.prepare(source_dir, dict(repository=record['repository'], commit=record['base_commit'],
                                   patch=f"system-reference/{directory}/{record['patch']}",
                                   patch_sha256=record['patch_sha256']))
    if prepare_only:
        return
    subprocess.run(['cargo', 'build', '--manifest-path', str(source_dir / 'Cargo.toml'),
                    '--locked', '--release', '--features', 'systemd', '--jobs', '4',
                    '--target-dir', str(source_dir / 'target')], check=True)
    name = {'wps': 'xwayland-satellite-wps', 'chat': 'xwayland-satellite-hidpi',
            'wechat': 'xwayland-satellite-wechat'}[profile]
    destination = target_home / '.local/libexec' / name
    if not destination.parent.resolve().is_relative_to(target_home.resolve()):
        raise ValueError('Destination escapes target home')
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + name, dir=destination.parent)
    os.close(fd)
    try:
        shutil.copyfile(source_dir / 'target/release/xwayland-satellite', temporary)
        os.chmod(temporary, 0o755)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print('Built:', destination, '(running services were not restarted)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', choices=['wps', 'chat', 'wechat'])
    parser.add_argument('--source-dir', type=Path)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    home = args.target_home.expanduser().absolute()
    source = args.source_dir or home / '.cache/desktop-config/build' / ('xwayland-' + args.profile)
    build(args.profile, source.expanduser().absolute(), home, args.prepare_only)


if __name__ == '__main__':
    main()
