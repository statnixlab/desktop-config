import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('app_compat', ROOT / 'scripts/install-app-compat.py')
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


class AppCompatibilityRestoreTests(unittest.TestCase):
    def test_ab_preserves_target_download_settings_and_authentication(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'new user'
            path = home / '.abdm/config/appSettings.json'
            path.parent.mkdir(parents=True)
            original = {'uiScale': 2, 'autoStartOnBoot': True, 'apiAuthKey': 'target-only',
                        'defaultDownloadFolder': '/custom/downloads', 'threadCount': 12}
            path.write_text(json.dumps(original))
            backup = home / 'backup'
            compat.restore_settings(home, ['abdownloadmanager'], backup)
            expected = dict(original, uiScale=None, autoStartOnBoot=False)
            self.assertEqual(json.loads(path.read_text()), expected)
            self.assertEqual(json.loads((backup / '.abdm/config/appSettings.json').read_text()), original)
            launcher = home / '.local/bin/abdownloadmanager-native-host'
            self.assertNotIn('@HOME@', launcher.read_text())
            self.assertNotIn('/home/nlh', launcher.read_text())

    def test_config_install_refuses_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            outside = root / 'outside'
            home.mkdir()
            outside.mkdir()
            (home / '.config').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'escapes'):
                compat.write_file(home, '.config/test.conf', b'x', 0o644, home / 'backup')
            self.assertEqual(list(outside.iterdir()), [])

    def test_wps_experiment_is_not_in_install_inventory(self):
        profiles = json.loads((ROOT / 'system-reference/app-compat/profiles.json').read_text())
        self.assertFalse(any('repaint' in path for path in profiles['wps']))


if __name__ == '__main__':
    unittest.main()
