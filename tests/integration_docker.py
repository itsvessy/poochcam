#!/usr/bin/env python3
import base64
import importlib.util
import json
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('server', ROOT / 'server/poochcamctl.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    subprocess.run(['docker', 'info'], check=True, capture_output=True, timeout=15)
    with tempfile.TemporaryDirectory(prefix='poochcam-docker-test-') as temp:
        state = Path(temp) / 'state'
        server.render(state, 'camera.example.com', 'admin@example.com',
                      json.loads((ROOT / 'server/images.json').read_text()))
        plain, https, rtmps = port(), port(), port()
        certdir = state / 'letsencrypt/live/camera.example.com'
        certdir.mkdir(parents=True)
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2',
                        '-subj', '/CN=camera.example.com', '-addext', 'subjectAltName=DNS:localhost,DNS:camera.example.com',
                        '-keyout', str(certdir / 'privkey.pem'), '-out', str(certdir / 'fullchain.pem')],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=20)
        conf = json.loads((state / 'compose.json').read_text())
        conf['name'] = 'poochcam-integration-' + str(https)
        conf['services']['nginx']['ports'] = [f'127.0.0.1:{plain}:80', f'127.0.0.1:{https}:443', f'127.0.0.1:{rtmps}:1936']
        (state / 'compose.json').write_text(json.dumps(conf))
        (state / 'nginx.conf').write_text(server.nginx_config('camera.example.com', True))
        mtx = json.loads((state / 'mediamtx.json').read_text())
        publisher = mtx['authInternalUsers'][0]['pass']
        lines = (state / 'connection.txt').read_text().splitlines()
        viewer = next(line.split(': ', 1)[1] for line in lines if line.startswith('Viewer password:'))
        cli = ['docker', 'compose', '-f', str(state / 'compose.json')]
        source = None
        try:
            subprocess.run(cli + ['up', '-d', 'nginx', 'mediamtx'], check=True, timeout=240)
            version = subprocess.run(cli + ['exec', '-T', 'nginx', 'nginx', '-V'], capture_output=True, text=True, check=True, timeout=15)
            assert '--with-stream_ssl_module' in version.stderr
            context = ssl.create_default_context(cafile=str(certdir / 'fullchain.pem'))
            def fetch(path, authenticated=True):
                headers = {'Authorization': 'Basic ' + base64.b64encode(f'viewer:{viewer}'.encode()).decode()} if authenticated else {}
                return urllib.request.urlopen(urllib.request.Request(f'https://localhost:{https}{path}', headers=headers), context=context, timeout=10)
            for path in ['/watch/', '/dogcam/index.m3u8', '/dogcam/hls.min.js', '/dogcam/']:
                try:
                    fetch(path, False)
                    raise AssertionError('Anonymous access accepted: ' + path)
                except urllib.error.HTTPError as error:
                    assert error.code == 401
            with fetch('/watch/') as response: assert b'Poochcam' in response.read()
            with fetch('/dogcam/hls.min.js') as response: assert len(response.read()) > 1000
            publishing = f'rtmps://localhost:{rtmps}/dogcam?user=camera&pass={publisher}'
            source = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-re', '-f', 'lavfi', '-i',
                                       'testsrc2=size=360x640:rate=15', '-re', '-f', 'lavfi', '-i',
                                       'sine=frequency=440:sample_rate=48000', '-c:v', 'libx264', '-preset', 'ultrafast',
                                       '-tune', 'zerolatency', '-g', '30', '-bf', '0', '-c:a', 'aac', '-b:a', '64k',
                                       '-t', '60', '-f', 'flv', publishing], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + 20
            while True:
                try:
                    with fetch('/dogcam/index.m3u8') as response:
                        if b'#EXTM3U' in response.read(): break
                except (OSError, urllib.error.HTTPError): pass
                if time.monotonic() > deadline: raise RuntimeError('No HLS through TLS proxy')
                time.sleep(.25)
            input_url = f'https://viewer:{viewer}@localhost:{https}/dogcam/index.m3u8'
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-rw_timeout', '5000000',
                            '-tls_verify', '1', '-ca_file', str(certdir / 'fullchain.pem'), '-i', input_url,
                            '-t', '3', '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
            subprocess.run(cli + ['exec', '-T', 'nginx', 'nginx', '-t'], check=True, timeout=10)
            subprocess.run(cli + ['exec', '-T', 'nginx', 'nginx', '-s', 'reload'], check=True, timeout=10)
            with fetch('/watch/') as response: assert response.status == 200
            print('Docker RTMPS → authenticated HTTPS HLS, fallback assets, video/audio decode and Nginx reload passed.')
        finally:
            if source and source.poll() is None:
                source.terminate()
                try: source.wait(timeout=5)
                except subprocess.TimeoutExpired: source.kill(); source.wait(timeout=5)
            subprocess.run(cli + ['down', '--remove-orphans'], check=False, timeout=60)


if __name__ == '__main__':
    main()
