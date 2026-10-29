#!/usr/bin/env python3
"""Download checksum-pinned desktop fonts; default mode only prints the plan."""
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(entry, cache):
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / (entry['sha256'] + '-' + entry['id'])
    if target.is_file() and sha256(target) == entry['sha256']:
        return target
    fd, temporary = tempfile.mkstemp(prefix='.font-', dir=cache)
    os.close(fd)
    try:
        subprocess.run(['curl', '--fail', '--location', '--retry', '2',
                        '--connect-timeout', '20', '--max-time', '300',
                        entry['download'], '-o', temporary], check=True)
        if sha256(Path(temporary)) != entry['sha256']:
            raise ValueError('Font archive checksum mismatch: ' + entry['id'])
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def payloads(entry, archive):
    if entry['format'] == 'ttf':
        return {entry['filename']: archive.read_bytes()}
    result = {}
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            path = Path(member.filename)
            if member.is_dir() or '__MACOSX' in path.parts:
                continue
            is_font = path.suffix.lower() in ('.ttf', '.otf', '.ttc') and any(
                fnmatch.fnmatchcase(member.filename, pattern) for pattern in entry['members'])
            is_license = path.name.lower().startswith(('license', 'ofl', 'copyright'))
            if not (is_font or is_license):
                continue
            data = bundle.read(member)
            if path.name in result and result[path.name] != data:
                if is_font:
                    raise ValueError('Duplicate font name: ' + path.name)
                continue
            result[path.name] = data
    if not any(Path(name).suffix.lower() in ('.ttf', '.otf', '.ttc') for name in result):
        raise ValueError('No matching fonts in ' + entry['id'])
    return result


def install(entry, archive, home, backup):
    directory = home / '.local/share/fonts' / entry['id']
    if not directory.resolve().is_relative_to(home.resolve()):
        raise ValueError('Font directory escapes target home')
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in payloads(entry, archive).items():
        target = directory / name
        if target.is_file() and target.read_bytes() == data:
            continue
        if target.exists() or target.is_symlink():
            saved = backup / entry['id'] / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved, follow_symlinks=False)
        fd, temporary = tempfile.mkstemp(prefix='.font-', dir=directory)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.chmod(temporary, 0o644)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    subprocess.run(['fc-cache', '-f', str(directory)], check=True)
    print('Installed:', entry['family'], '->', directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--only', action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    home = args.target_home.expanduser().absolute()
    entries = json.loads((ROOT / 'system-reference/fonts/install.json').read_text())
    unknown = set(args.only) - {entry['id'] for entry in entries}
    if unknown:
        parser.error('Unknown font IDs: ' + ', '.join(sorted(unknown)))
    entries = [entry for entry in entries if not args.only or entry['id'] in args.only]
    for entry in entries:
        print(entry['family'], entry['download'])
    if not args.apply:
        print('Plan only; add --apply to download and install.')
        return
    cache = args.cache_dir or home / '.cache/desktop-config/fonts'
    backup = home / '.local/state/desktop-config-backups' / datetime.now().strftime('fonts-%Y%m%d-%H%M%S-%f')
    for entry in entries:
        install(entry, download(entry, cache), home, backup)


if __name__ == '__main__':
    main()
