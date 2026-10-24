#!/usr/bin/env python3
"""Prepare the pinned Niri and patched Smithay sources without replacing local edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(path, *args, env=None):
    return subprocess.check_output(['git', '-C', str(path), *args], env=env)


def prepare(path, source, exclude=None):
    patch = ROOT / source['patch']
    if hashlib.sha256(patch.read_bytes()).hexdigest() != source['patch_sha256']:
        raise RuntimeError(f"Patch checksum mismatch: {source['patch']}")
    if not path.exists():
        path.mkdir(parents=True)
        git(path, 'init', '-q')
        git(path, 'remote', 'add', 'origin', source['repository'])
        git(path, 'fetch', '--depth', '1', 'origin', source['commit'])
        git(path, 'checkout', '--detach', 'FETCH_HEAD')
        git(path, 'apply', '--index', '--whitespace=nowarn', str(patch))
    if git(path, 'rev-parse', 'HEAD').decode().strip() != source['commit']:
        raise RuntimeError(f'Existing source has a different base: {path}; choose another NIRI_SOURCE_DIR')
    # Compare against the expected patched tree using a temporary index. Never
    # reset, stage, or discard the user's working tree or actual index.
    with tempfile.TemporaryDirectory(prefix='niri-expected-index-') as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
        git(path, 'read-tree', 'HEAD', env=env)
        git(path, 'apply', '--cached', '--whitespace=nowarn', str(patch), env=env)
        expected = git(path, 'write-tree', env=env).decode().strip()
        if git(path, 'diff', '--name-only', expected, '--').strip():
            raise RuntimeError(f'Existing source has different local changes: {path}; choose another NIRI_SOURCE_DIR')
    args = ['ls-files', '--others', '--exclude-standard']
    if exclude:
        args += ['--exclude=' + exclude + '/']
    if git(path, *args).strip():
        raise RuntimeError(f'Existing source has untracked files: {path}; preserve them before rebuilding')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    args = parser.parse_args()
    lock = json.loads((ROOT / 'sources.lock.json').read_text())
    source_dir = args.source_dir.expanduser().absolute()
    subdir = lock['smithay']['source_subdirectory']
    if subdir != 'smithay-workaround':
        raise RuntimeError('Unexpected Smithay source directory')
    prepare(source_dir, lock['niri'], exclude=subdir)
    prepare(source_dir / subdir, lock['smithay'])
    print(f'Pinned Niri and Smithay sources verified: {source_dir}')


if __name__ == '__main__':
    main()
