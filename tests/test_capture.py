import importlib.util
import unittest
import tempfile
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('capture', ROOT / 'scripts/capture-current.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def test_rebase_and_remove_credentials_without_changing_preferences(self):
        source = {'file': '/home/source/Pictures/image.png', 'dark': True,
                  'nested': {'apiKey': 'do-not-publish', 'password': 'private', 'token': 'private', 'cookie': 'private'},
                  'pinned': ['chatgpt', 'org.gnome.Nautilus'], 'sidebarCookieDialStyle': 'numbers'}
        result = capture.clean_settings(source, Path('/home/source'))
        self.assertEqual(result['file'], '@HOME@/Pictures/image.png')
        self.assertEqual(result['nested'], {'apiKey': '', 'password': '', 'token': '', 'cookie': ''})
        self.assertEqual(result['pinned'], source['pinned'])
        self.assertTrue(result['dark'])
        self.assertEqual(source['nested']['apiKey'], 'do-not-publish')
        self.assertEqual(result['sidebarCookieDialStyle'], 'numbers')

    def test_native_dock_and_groups_capture_without_legacy_dock(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home = base / 'source home'
            root = base / 'snapshot'
            for folder in [home / '.config/clavis', home / '.config/quickshell/clavis/Modules/Dock', root]:
                folder.mkdir(parents=True)
            (home / '.config/quickshell/clavis/Modules/Dock/DockHost.qml').write_text('Item {}\n')
            (root / 'sources.lock.json').write_text('{"clavis":{"commit":"fixed"}}')
            dock = {'schemaVersion': 1, 'options': {'autoHide': True},
                    'pinned': [{'kind': 'app', 'desktopId': 'org.clavis.Launchpad'}]}
            groups = {'schemaVersion': 1, 'entries': [{'kind': 'folder', 'id': 'work',
                      'name': 'Work', 'children': ['editor', 'browser']}]}
            (home / '.config/clavis/dock.json').write_text(json.dumps(dock))
            (home / '.config/clavis/launchpad.json').write_text(json.dumps(groups))
            retired = {
                'bin/dolphin': '.local/bin/dolphin',
                'share/applications/org.kde.dolphin.desktop': '.local/share/applications/org.kde.dolphin.desktop',
                'config/dolphinrc': '.config/dolphinrc',
                'config/nyx-desktop-style/dolphin.qss': '.config/nyx-desktop-style/dolphin.qss',
            }
            for snapshot_path, source_path in retired.items():
                for path in [root / snapshot_path, home / source_path]:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('old Dolphin customization\n')
            effects = home / '.config/niri/clavis/application-effects.kdl'
            effects.parent.mkdir(parents=True)
            effects.write_text('blur { passes 3; }\nwindow-rule { opacity 0.94; }\n')
            panel = effects.with_name('panel-effects.kdl')
            panel.write_text('blur { passes 2; }\n')
            (effects.parent.parent / 'config.kdl').write_text('debug {\n prefer-16bit-output\n keep-previous-frame-buffer\n render-drm-device "/dev/dri/test"\n}\ninclude "clavis/application-effects.kdl"\n')
            capture.capture(home, root)
            self.assertEqual((root / 'config/niri/clavis/panel-effects.kdl').read_bytes(), panel.read_bytes())
            portable = (root / 'config/niri/config.kdl').read_text()
            self.assertIn('include "clavis/panel-effects.kdl"', portable)
            self.assertNotIn('prefer-16bit-output', portable)
            self.assertNotIn('keep-previous-frame-buffer', portable)
            self.assertNotIn('/dev/dri/test', portable)
            reference = (root / 'system-reference/user-home/config/niri/config.kdl').read_text()
            self.assertIn('prefer-16bit-output', reference)
            self.assertIn('keep-previous-frame-buffer', reference)
            self.assertEqual((root / 'config/niri/clavis/application-effects.kdl').read_bytes(), effects.read_bytes())
            self.assertEqual(json.loads((root / 'config/clavis/dock.json').read_text()), dock)
            self.assertEqual(json.loads((root / 'config/clavis/launchpad.json').read_text()), groups)
            self.assertFalse((root / 'config/quickshell/nyx-dock').exists())
            for snapshot_path, source_path in retired.items():
                self.assertFalse((root / snapshot_path).exists())
                self.assertTrue((home / source_path).is_file())
            self.assertEqual(json.loads((root / 'sources.lock.json').read_text())['clavis']['commit'], 'fixed')
