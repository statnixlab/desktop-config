#!/usr/bin/env python3
"""Prepare pinned Niri sources without replacing local edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(path, *args, env=None):
    return subprocess.check_output(['git', '-C', str(path), *args], env=env)


def prepare_git_branch(path, source):
    """Use the complete maintained branch; no additional patches are applied."""
    branch = source['branch']
    commit = source['commit']
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--no-checkout', '--branch', branch,
                        source['repository'], str(path)], check=True)
        # This is a new checkout, so pinning its branch cannot discard local work.
        git(path, 'checkout', '-B', branch, commit)
        git(path, 'branch', '--set-upstream-to=origin/' + branch, branch)
    if git(path, 'remote', 'get-url', 'origin').decode().strip() != source['repository']:
        raise RuntimeError(f'Existing source has a different origin: {path}')
    if git(path, 'branch', '--show-current').decode().strip() != branch:
        raise RuntimeError(f'Existing source uses another branch: {path}; preserve it before rebuilding')
    if git(path, 'rev-parse', 'HEAD').decode().strip() != commit:
        raise RuntimeError(f'Existing source has a different commit: {path}; update the source pin or choose another NIRI_SOURCE_DIR')
    if git(path, 'status', '--porcelain', '--untracked-files=all').strip():
        raise RuntimeError(f'Existing source has local changes: {path}; preserve them before rebuilding')
    if git(path, 'rev-parse', '--is-shallow-repository').decode().strip() != 'false':
        raise RuntimeError(f'Full Git history is required for future upstream merges: {path}')


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
    if lock['niri'].get('source_mode') == 'git':
        machine = json.loads((ROOT / 'hardware/machine.json').read_text())
        branch = git(ROOT, 'branch', '--show-current').decode().strip()
        if socket.gethostname() != machine['hostname'] or branch != machine['branch']:
            raise RuntimeError('Machine/branch mismatch; prepare only this machine\'s Niri source')
        if lock['niri']['branch'] != machine['branch']:
            raise RuntimeError('Niri source branch does not match the machine branch')
        prepare_git_branch(source_dir, lock['niri'])
        print(f'Integrated Niri source verified (no patch application): {source_dir}')
        return
    subdir = lock['smithay']['source_subdirectory']
    if subdir != 'smithay-workaround':
        raise RuntimeError('Unexpected Smithay source directory')
    prepare(source_dir, lock['niri'], exclude=subdir)
    prepare(source_dir / subdir, lock['smithay'])
    print(f'Pinned Niri and Smithay sources verified: {source_dir}')


if __name__ == '__main__':
    main()
