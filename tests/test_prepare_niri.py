import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_niri', ROOT / 'scripts/prepare-niri.py')
prepare_niri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_niri)


class GitSourceFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / 'upstream'
        self.origin.mkdir()
        self.git(self.origin, 'init', '-q')
        (self.origin / 'example.rs').write_text('before\n')
        self.git(self.origin, 'add', 'example.rs')
        self.git(self.origin, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'baseline')
        commit = self.git(self.origin, 'rev-parse', 'HEAD').decode().strip()
        (self.origin / 'example.rs').write_text('after\n')
        patch = self.root / 'change.patch'
        patch.write_bytes(self.git(self.origin, 'diff', '--binary', '--full-index'))
        self.source = {'repository': str(self.origin), 'commit': commit,
                       'patch': str(patch), 'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest()}
        self.checkout = self.root / 'checkout'

    def git(self, path, *args):
        return subprocess.check_output(['git', '-C', str(path), *args], stderr=subprocess.DEVNULL)


class PrepareNiriTests(GitSourceFixture):
    def test_prepare_can_be_repeated_without_changing_staging(self):
        prepare_niri.prepare(self.checkout, self.source)
        self.assertEqual((self.checkout / 'example.rs').read_text(), 'after\n')
        index = (self.checkout / '.git/index').read_bytes()
        prepare_niri.prepare(self.checkout, self.source)
        self.assertEqual((self.checkout / '.git/index').read_bytes(), index)

    def test_local_edits_and_untracked_files_are_preserved(self):
        prepare_niri.prepare(self.checkout, self.source)
        (self.checkout / 'example.rs').write_text('personal edits\n')
        with self.assertRaisesRegex(RuntimeError, 'local changes'):
            prepare_niri.prepare(self.checkout, self.source)
        self.assertEqual((self.checkout / 'example.rs').read_text(), 'personal edits\n')
        (self.checkout / 'example.rs').write_text('after\n')
        (self.checkout / 'personal.txt').write_text('keep me')
        with self.assertRaisesRegex(RuntimeError, 'untracked files'):
            prepare_niri.prepare(self.checkout, self.source)
        self.assertEqual((self.checkout / 'personal.txt').read_text(), 'keep me')

    def test_modified_patch_is_rejected_before_creating_checkout(self):
        Path(self.source['patch']).write_text('corrupted')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            prepare_niri.prepare(self.checkout, self.source)
        self.assertFalse(self.checkout.exists())


class PrepareGitBranchTests(GitSourceFixture):
    def setUp(self):
        super().setUp()
        self.git(self.origin, 'switch', '-c', 'machine/amd-laptop')
        self.git(self.origin, 'add', 'example.rs')
        self.git(self.origin, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'integrate local changes')
        self.source = {
            'source_mode': 'git', 'repository': str(self.origin),
            'branch': 'machine/amd-laptop',
            'commit': self.git(self.origin, 'rev-parse', 'HEAD').decode().strip(),
        }

    def test_checks_out_pinned_commit_with_history_when_remote_advances(self):
        (self.origin / 'example.rs').write_text('newer upstream\n')
        self.git(self.origin, 'add', 'example.rs')
        self.git(self.origin, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'advance remote branch')
        prepare_niri.prepare_git_branch(self.checkout, self.source)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD').decode().strip(), self.source['commit'])
        self.assertEqual(self.git(self.checkout, 'branch', '--show-current').decode().strip(), self.source['branch'])
        self.assertEqual(self.git(self.checkout, 'rev-parse', '--is-shallow-repository').decode().strip(), 'false')
        self.assertEqual((self.checkout / 'example.rs').read_text(), 'after\n')
        prepare_niri.prepare_git_branch(self.checkout, self.source)
        self.assertFalse(self.git(self.checkout, 'status', '--porcelain').strip())

    def test_preserves_staged_unstaged_and_untracked_work(self):
        for kind in ['staged', 'unstaged', 'untracked']:
            with self.subTest(kind=kind):
                checkout = self.root / kind
                prepare_niri.prepare_git_branch(checkout, self.source)
                path = checkout / ('personal.txt' if kind == 'untracked' else 'example.rs')
                path.write_text('keep this work\n')
                if kind == 'staged':
                    self.git(checkout, 'add', path.name)
                status = self.git(checkout, 'status', '--porcelain')
                with self.assertRaisesRegex(RuntimeError, 'local changes'):
                    prepare_niri.prepare_git_branch(checkout, self.source)
                self.assertEqual(path.read_text(), 'keep this work\n')
                self.assertEqual(self.git(checkout, 'status', '--porcelain'), status)

    def test_preserves_other_branch_and_commit(self):
        prepare_niri.prepare_git_branch(self.checkout, self.source)
        self.git(self.checkout, 'switch', '-c', 'review/in-progress')
        with self.assertRaisesRegex(RuntimeError, 'another branch'):
            prepare_niri.prepare_git_branch(self.checkout, self.source)
        self.assertEqual(self.git(self.checkout, 'branch', '--show-current').decode().strip(), 'review/in-progress')
        self.git(self.checkout, 'switch', self.source['branch'])
        (self.checkout / 'example.rs').write_text('local commit\n')
        self.git(self.checkout, 'add', 'example.rs')
        self.git(self.checkout, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'work after pinned commit')
        head = self.git(self.checkout, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(RuntimeError, 'different commit'):
            prepare_niri.prepare_git_branch(self.checkout, self.source)
        self.assertEqual(self.git(self.checkout, 'rev-parse', 'HEAD'), head)


if __name__ == '__main__':
    unittest.main()
