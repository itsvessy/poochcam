#!/usr/bin/env python3
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('server', ROOT / 'server/poochcamctl.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def run_test(mediamtx, ffmpeg, ffprobe):
    with tempfile.TemporaryDirectory(prefix='poochcam-media-test-') as tmp:
        directory = Path(tmp)
        state = directory / 'state'
        server.render(state, 'camera.example.com', 'admin@example.com',
                      json.loads((ROOT / 'server/images.json').read_text()))
        config = json.loads((state / 'mediamtx.json').read_text())
        rtmp_port, hls_port = free_port(), free_port()
        config['rtmpAddress'] = f'127.0.0.1:{rtmp_port}'
        config['hlsAddress'] = f'127.0.0.1:{hls_port}'
        (directory / 'mediamtx.json').write_text(json.dumps(config))
        publisher, reader = config['authInternalUsers']
        base = f'http://127.0.0.1:{hls_port}/dogcam/'
        publishing = f'rtmp://127.0.0.1:{rtmp_port}/dogcam?user=camera&pass={publisher["pass"]}'
        logs = (directory / 'server.log').open('w')
        service = subprocess.Popen([mediamtx, str(directory / 'mediamtx.json')], stdout=logs, stderr=logs)
        camera = None
        try:
            deadline = time.monotonic() + 10
            while True:
                if service.poll() is not None:
                    raise RuntimeError('Reference MediaMTX config rejected: ' + (directory / 'server.log').read_text())
                try:
                    with socket.create_connection(('127.0.0.1', rtmp_port), timeout=1): pass
                    break
                except OSError:
                    if time.monotonic() > deadline: raise
                    time.sleep(.1)
            publish_args = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-re', '-f', 'lavfi', '-i',
                            'testsrc2=size=360x640:rate=15', '-re', '-f', 'lavfi', '-i',
                            'sine=frequency=440:sample_rate=48000', '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-tune', 'zerolatency', '-g', '30', '-bf', '0', '-c:a', 'aac', '-b:a', '64k',
                            '-t', '40', '-f', 'flv']
            rejected = subprocess.run(publish_args + [publishing.replace(publisher['pass'], 'incorrect')],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            assert rejected.returncode != 0, 'Unauthenticated publishing succeeded'
            camera = subprocess.Popen(publish_args + [publishing], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            authorization = 'Basic ' + base64.b64encode(f'backend:{reader["pass"]}'.encode()).decode()
            deadline = time.monotonic() + 15
            while True:
                try:
                    req = urllib.request.Request(base + 'index.m3u8', headers={'Authorization': authorization})
                    with urllib.request.urlopen(req, timeout=3) as response: playlist = response.read().decode()
                    if '#EXTM3U' in playlist: break
                except (OSError, urllib.error.HTTPError): pass
                if time.monotonic() > deadline: raise RuntimeError('No playable HLS playlist after publishing')
                time.sleep(.3)
            for credential in [None, 'Basic ' + base64.b64encode(f'camera:{publisher["pass"]}'.encode()).decode()]:
                request = urllib.request.Request(base + 'index.m3u8', headers={'Authorization': credential} if credential else {})
                try:
                    with urllib.request.urlopen(request, timeout=3) as response:
                        raise AssertionError(f'Unauthorized media access returned {response.status}')
                except urllib.error.HTTPError as error:
                    assert error.code in [401, 403], error.code
            input_url = f'http://backend:{reader["pass"]}@127.0.0.1:{hls_port}/dogcam/index.m3u8'
            probe = subprocess.run([ffprobe, '-v', 'error', '-rw_timeout', '5000000', '-show_streams',
                                    '-of', 'json', input_url], capture_output=True, text=True, timeout=15, check=True)
            kinds = {stream['codec_type'] for stream in json.loads(probe.stdout)['streams']}
            assert {'video', 'audio'} <= kinds, kinds
            subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-rw_timeout', '5000000',
                            '-i', input_url, '-t', '3', '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=True)
            print('MediaMTX reference config accepted; publish/read authorization and actual H.264/AAC decoding passed.')
        finally:
            for process in [camera, service]:
                if process and process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=5)
                    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            logs.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mediamtx', required=True)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    run_test(args.mediamtx, args.ffmpeg, args.ffprobe)
