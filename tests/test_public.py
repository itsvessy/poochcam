import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('check_public', Path(__file__).resolve().parents[1] / 'tools/check_public.py')
public = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public)


class PublicSourceTests(unittest.TestCase):
    def test_private_files_even_when_force_tracked(self):
        for name in ['ios/Config/User.xcconfig', 'server/state/connection.txt', 'runtime/status.json',
                     'diagnostics/session.json', 'ios/Design/reference.png', '.env.production',
                     'archive.xcarchive/Info.plist', 'signing.p12',
                     '.wrangler/state/local.json', 'node_modules/example/package.json']:
            with self.subTest(name=name):
                self.assertTrue(public.inspect(name, b''))

    def test_private_content_reports_categories_without_values(self):
        values = [b'/'+b'Users/alice/private/', b'100.'+b'76.1.2',
                  b'DEVELOPMENT_' + b'TEAM = ABCDE12345;', b'hi@'+b'vessy.ca',
                  b'gh' + b'p_' + b'a' * 40, b'-----BEGIN ' + b'PRIVATE KEY-----']
        for value in values:
            with self.subTest(category=value[:3]):
                result = public.inspect('source.txt', value)
                self.assertTrue(result)
                self.assertNotIn(value.decode(), '\n'.join(result))

    def test_public_examples_and_notices_are_allowed(self):
        for name, value in [('.env.example', b'PASSWORD=CHANGE_ME'),
                            ('ios/Config/User.xcconfig.example', b'DEVELOPMENT_TEAM = YOUR_PERSONAL_TEAM_ID\n'),
                            ('NOTICE', b'Copyright authors; support@poochcam.ca'),
                            ('example.txt', b'rtmps://camera.example.com/dogcam')]:
            self.assertEqual(public.inspect(name, value), [])

    def test_index_and_history_cannot_be_hidden_by_working_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'Scanner test')
            git('config', 'user.email', 'test@example.com')
            file = root / 'sample.txt'
            file.write_bytes(b'gh' + b'p_' + b'a' * 40)
            git('add', 'sample.txt')
            file.write_text('clean working copy')
            self.assertEqual(public.audit_entries(public.repository_entries(root), False), [])
            self.assertTrue(public.audit_entries(public.repository_entries(root, 'staged'), False))
            git('commit', '-qm', 'Fixture containing a test token')
            old = git('rev-parse', 'HEAD').decode().strip()
            git('add', 'sample.txt')
            git('commit', '-qm', 'Clean current file')
            self.assertEqual(public.audit_entries(public.repository_entries(root, 'tree', 'HEAD'), False), [])
            self.assertTrue(public.audit_entries(public.repository_entries(root, 'tree', old), False))

    def test_symlinks_fail_without_following_them(self):
        self.assertTrue(public.audit_entries({'link': ('120000', b'elsewhere')}, False))

    def test_required_routes_and_digest_pins_use_audited_data(self):
        entries = {'site/' + name: ('100644', b'') for name in public.REQUIRED_SITE}
        entries['server/images.json'] = ('100644', b'{"server": "image:latest"}')
        self.assertIn('Unpinned server image', public.audit_entries(entries))
        entries['server/images.json'] = ('100644', ('{"server": "image@sha256:' + 'a' * 64 + '"}').encode())
        self.assertEqual(public.audit_entries(entries), [])


if __name__ == '__main__':
    unittest.main()
