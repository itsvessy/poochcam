import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('server', ROOT / 'server/poochcamctl.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class ServerSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'state'
        self.images = json.loads((ROOT / 'server/images.json').read_text())

    def render(self):
        server.render(self.state, 'camera.example.com', 'admin@example.com', self.images)

    def test_credentials_are_separate_and_publish_url_round_trips(self):
        self.render()
        config = json.loads((self.state / 'mediamtx.json').read_text())
        accounts = config['authInternalUsers']
        url = (self.state / 'connection.txt').read_text().splitlines()[0].split(': ', 1)[1]
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query['pass'][0], accounts[0]['pass'])
        self.assertNotEqual(accounts[0]['pass'], accounts[1]['pass'])
        self.assertEqual(accounts[0]['permissions'], [{'action': 'publish', 'path': 'dogcam'}])
        self.assertEqual(accounts[1]['permissions'], [{'action': 'read', 'path': 'dogcam'}])
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.state / 'connection.txt').stat().st_mode), 0o600)

    def test_setup_refuses_overwrite_and_injection(self):
        for host in ['bad;id', 'camera.example.com\n}', 'https://camera.example.com', '-bad.example.com']:
            with self.assertRaises(ValueError): server.render(self.state, host, 'a@example.com', self.images)
            self.assertFalse(self.state.exists())
        self.render()
        original = (self.state / 'connection.txt').read_bytes()
        with self.assertRaises(ValueError): self.render()
        self.assertEqual(original, (self.state / 'connection.txt').read_bytes())

    def test_only_tls_edge_ports_are_published_and_state_is_not_a_web_root(self):
        self.render()
        config = json.loads((self.state / 'compose.json').read_text())
        self.assertNotIn('ports', config['services']['mediamtx'])
        self.assertTrue(config['networks']['media']['internal'])
        nginx = config['services']['nginx']
        self.assertEqual(nginx['ports'], ['80:80', '443:443', '1936:1936'])
        self.assertFalse(any('/var/run/docker.sock' in mount for mount in nginx['volumes']))
        self.assertFalse(any('/etc/poochcam' in mount for mount in nginx['volumes']))
        self.assertIn('max-size', nginx['logging']['options'])

    def test_certificate_bootstrap_and_all_media_auth(self):
        before = server.nginx_config('camera.example.com', False)
        after = server.nginx_config('camera.example.com', True)
        self.assertNotIn('ssl_certificate ', before)
        self.assertIn('/.well-known/acme-challenge/', before)
        self.assertIn('return 503', before)
        self.assertIn('auth_basic "Poochcam viewer"', after)
        self.assertNotIn('auth_basic off', after)
        self.assertIn('location /dogcam/', after)
        self.assertIn('include /etc/nginx/reader.conf', after)
        self.assertIn('proxy_cookie_flags', after)
        self.assertIn('TLSv1.2 TLSv1.3', after)


if __name__ == '__main__':
    unittest.main()
