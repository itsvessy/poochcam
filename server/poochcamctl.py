#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'


def run(args, **kwargs):
    return subprocess.run(args, check=True, timeout=kwargs.pop('timeout', 120), **kwargs)


def write_private(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)


def nginx_config(host, tls):
    certificate = f'/etc/letsencrypt/live/{host}'
    secure = f'''
    server {{
        listen 443 ssl;
        server_name {host};
        ssl_certificate {certificate}/fullchain.pem;
        ssl_certificate_key {certificate}/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        auth_basic "Poochcam viewer";
        auth_basic_user_file /etc/nginx/viewer.htpasswd;
        add_header Referrer-Policy no-referrer always;
        add_header X-Content-Type-Options nosniff always;
        add_header Cache-Control "no-store" always;
        location = / {{ return 302 /watch/; }}
        location /watch/ {{ alias /srv/viewer/; index index.html; }}
        location /dogcam/ {{
            include /etc/nginx/reader.conf;
            proxy_pass http://mediamtx:8888;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto https;
            proxy_connect_timeout 5s;
            proxy_read_timeout 20s;
            proxy_send_timeout 20s;
            proxy_buffering off;
            proxy_redirect http://mediamtx:8888/ /;
            proxy_cookie_flags ~ secure httponly samesite=strict;
        }}
        location / {{ return 404; }}
    }}
'''
    stream = f'''
stream {{
    server {{
        listen 1936 ssl;
        ssl_certificate {certificate}/fullchain.pem;
        ssl_certificate_key {certificate}/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_handshake_timeout 10s;
        proxy_connect_timeout 5s;
        proxy_timeout 60s;
        proxy_pass mediamtx:1935;
    }}
}}
'''
    return f'''user nginx;
worker_processes auto;
error_log /dev/stderr warn;
pid /var/run/nginx.pid;
events {{ worker_connections 256; }}
http {{
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log off;
    server_tokens off;
    client_header_timeout 10s;
    client_body_timeout 10s;
    send_timeout 20s;
    keepalive_timeout 20s;
    server {{
        listen 80;
        server_name {host};
        location /.well-known/acme-challenge/ {{ root /var/www/acme; }}
        location / {{ return {'301 https://$host$request_uri' if tls else '503'}; }}
    }}
{secure if tls else ''}}}
{stream if tls else ''}'''


def render(state, hostname, email, images):
    if not re.fullmatch(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', hostname):
        raise ValueError('Use a public DNS hostname, without a scheme, path or port.')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise ValueError('Enter a valid certificate contact email.')
    if state.exists():
        raise ValueError('Setup already exists. Use rotate or restore; setup never overwrites secrets.')
    state.mkdir(mode=0o700)
    for folder in ['acme', 'letsencrypt', 'certbot-work', 'certbot-logs']:
        (state / folder).mkdir()
    (state / 'acme').chmod(0o755)
    publisher, viewer, reader = [secrets.token_urlsafe(32) for _ in range(3)]
    password_hash = run(['openssl', 'passwd', '-6', '-stdin'], input=viewer + '\n',
                        text=True, capture_output=True).stdout.strip()
    write_private(state / 'viewer.htpasswd', f'viewer:{password_hash}\n')
    (state / 'viewer.htpasswd').chmod(0o644)
    authorization = base64.b64encode(f'backend:{reader}'.encode()).decode()
    write_private(state / 'reader.conf', f'proxy_set_header Authorization "Basic {authorization}";\n')
    config = {
        'logLevel': 'warn', 'logDestinations': ['stdout'],
        'readTimeout': '15s', 'writeTimeout': '15s',
        'authMethod': 'internal', 'authInternalUsers': [
            {'user': 'camera', 'pass': publisher, 'permissions': [{'action': 'publish', 'path': 'dogcam'}]},
            {'user': 'backend', 'pass': reader, 'permissions': [{'action': 'read', 'path': 'dogcam'}]},
        ],
        'api': False, 'metrics': False, 'pprof': False, 'playback': False,
        'rtsp': False, 'webrtc': False, 'srt': False,
        'rtmp': True, 'rtmpEncryption': 'no', 'rtmpAddress': ':1935',
        'hls': True, 'hlsAddress': ':8888', 'hlsAlwaysRemux': True,
        'hlsVariant': 'fmp4', 'hlsSegmentCount': 7, 'hlsSegmentDuration': '2s',
        'hlsAllowOrigins': [f'https://{hostname}'],
        'pathDefaults': {'record': False, 'overridePublisher': False},
        'paths': {'dogcam': {'source': 'publisher'}},
    }
    write_private(state / 'mediamtx.json', json.dumps(config, indent=2) + '\n')
    write_private(state / 'settings.json', json.dumps({'hostname': hostname, 'email': email}, indent=2) + '\n')
    write_private(state / 'connection.txt',
                  f'Publishing URL (secret): rtmps://{hostname}:1936/dogcam?user=camera&pass={quote(publisher, safe="")}\n'
                  f'Viewing URL: https://{hostname}/watch/\nViewer username: viewer\nViewer password: {viewer}\n')
    write_private(state / 'nginx.conf', nginx_config(hostname, False))
    common = {'restart': 'unless-stopped', 'logging': {'driver': 'local', 'options': {'max-size': '5m', 'max-file': '3'}},
              'security_opt': ['no-new-privileges:true']}
    compose = {'name': 'poochcam', 'services': {
        'mediamtx': {**common, 'image': images['bluenviron/mediamtx'],
                    'volumes': [f'{state}/mediamtx.json:/mediamtx.yml:ro'],
                    'networks': ['media'], 'mem_limit': '160m'},
        'nginx': {**common, 'image': images['library/nginx'], 'depends_on': ['mediamtx'],
                  'ports': ['80:80', '443:443', '1936:1936'],
                  'volumes': [f'{state}/nginx.conf:/etc/nginx/nginx.conf:ro',
                              f'{state}/viewer.htpasswd:/etc/nginx/viewer.htpasswd:ro',
                              f'{state}/reader.conf:/etc/nginx/reader.conf:ro',
                              f'{state}/acme:/var/www/acme:ro',
                              f'{state}/letsencrypt:/etc/letsencrypt:ro',
                              f'{ROOT.parent}/viewer:/srv/viewer:ro'],
                  'networks': ['edge', 'media'], 'mem_limit': '64m'},
        'certbot': {'image': images['certbot/certbot'], 'profiles': ['tools'],
                    'volumes': [f'{state}/acme:/var/www/acme',
                                f'{state}/letsencrypt:/etc/letsencrypt',
                                f'{state}/certbot-work:/var/lib/letsencrypt',
                                f'{state}/certbot-logs:/var/log/letsencrypt'],
                    'networks': ['edge'], 'mem_limit': '192m'},
    }, 'networks': {'edge': {}, 'media': {'internal': True}}}
    write_private(state / 'compose.json', json.dumps(compose, indent=2) + '\n')


def compose(*args, **kwargs):
    return run(['docker', 'compose', '-f', str(STATE / 'compose.json'), *args], **kwargs)


def settings():
    return json.loads((STATE / 'settings.json').read_text())


def reload_nginx():
    compose('exec', '-T', 'nginx', 'nginx', '-t')
    compose('exec', '-T', 'nginx', 'nginx', '-s', 'reload')


def activate_tls():
    path = STATE / 'nginx.conf'
    previous = path.read_text()
    write_private(path, nginx_config(settings()['hostname'], True))
    try:
        reload_nginx()
    except Exception:
        write_private(path, previous)
        raise


def main():
    parser = argparse.ArgumentParser(description='Manage the isolated Poochcam Docker server.')
    parser.add_argument('command', choices=['setup', 'start', 'stop', 'restart', 'status', 'renew',
                                          'renew-test', 'doctor', 'rotate', 'credentials', 'backup', 'remove'])
    parser.add_argument('--hostname')
    parser.add_argument('--email')
    parser.add_argument('--accept-acme-terms', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--confirm-remove', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    if args.command == 'setup':
        if not args.hostname or not args.email:
            parser.error('setup needs --hostname and --email')
        render(STATE, args.hostname.lower(), args.email, json.loads((ROOT / 'images.json').read_text()))
        print('Setup saved. Point DNS to this server, then run start --accept-acme-terms. Secrets are in server/state/connection.txt.')
        return
    if not (STATE / 'compose.json').exists():
        parser.error('Run setup first.')
    if args.command == 'start':
        config = settings()
        socket.getaddrinfo(config['hostname'], 443)
        certificate = STATE / 'letsencrypt/live' / config['hostname'] / 'fullchain.pem'
        if not certificate.exists() and not args.accept_acme_terms:
            parser.error('First start requires --accept-acme-terms after reading https://letsencrypt.org/repository/.')
        compose('up', '-d', 'mediamtx', 'nginx')
        result = compose('exec', '-T', 'nginx', 'nginx', '-V', capture_output=True, text=True)
        if '--with-stream_ssl_module' not in result.stderr:
            raise RuntimeError('Pinned Nginx image is missing stream TLS support.')
        if not certificate.exists():
            compose('run', '--rm', 'certbot', 'certonly', '--webroot', '-w', '/var/www/acme',
                    '-d', config['hostname'], '--email', config['email'], '--agree-tos', '--non-interactive',
                    '--logs-dir', '/var/log/letsencrypt', timeout=180)
        activate_tls()
        print('Server started. Install the renewal timer described in docs/SERVER.md.')
    elif args.command in ['renew', 'renew-test']:
        compose('run', '--rm', 'certbot', 'renew', '--webroot', '-w', '/var/www/acme',
                '--non-interactive', *(['--dry-run'] if args.command == 'renew-test' else []), timeout=180)
        reload_nginx()
        for path in (STATE / 'certbot-logs').glob('letsencrypt.log.*'):
            if path.stat().st_mtime < __import__('time').time() - 7 * 86400:
                path.unlink()
    elif args.command == 'stop':
        compose('stop', 'nginx', 'mediamtx')
    elif args.command == 'restart':
        compose('restart', 'mediamtx', 'nginx')
    elif args.command == 'status':
        compose('ps')
        print('Process status does not establish playable picture or sound. Use doctor and the viewer.')
    elif args.command == 'doctor':
        compose('exec', '-T', 'nginx', 'nginx', '-t')
        cert = STATE / 'letsencrypt/live' / settings()['hostname'] / 'fullchain.pem'
        run(['openssl', 'x509', '-in', str(cert), '-noout', '-checkend', str(14 * 86400)])
        print('Configuration and certificate checks passed; media playback still needs checking.')
    elif args.command == 'credentials':
        print((STATE / 'connection.txt').read_text())
    elif args.command == 'rotate':
        config = settings()
        replacement = STATE / 'rotation'
        if replacement.exists():
            raise RuntimeError('An unfinished rotation exists; inspect state/rotation before retrying.')
        render(replacement, config['hostname'], config['email'], json.loads((ROOT / 'images.json').read_text()))
        for name in ['mediamtx.json', 'viewer.htpasswd', 'reader.conf', 'connection.txt']:
            write_private(STATE / name, (replacement / name).read_text())
        (STATE / "viewer.htpasswd").chmod(0o644)
        shutil.rmtree(replacement)
        compose('restart', 'mediamtx', 'nginx')
        print('Credentials rotated; copy the new connection to the camera and sign in again to the viewer.')
    elif args.command == 'backup':
        if not args.output or args.output.exists() or STATE in args.output.resolve().parents:
            parser.error('Use --output with a new archive path outside server/state.')
        with tarfile.open(args.output, 'w:gz') as archive:
            archive.add(STATE, arcname='state')
        args.output.chmod(0o600)
        print('Private backup created. It contains passwords and certificate keys; encrypt before moving it.')
    elif args.command == 'remove':
        if not args.confirm_remove:
            parser.error('Use --confirm-remove to remove containers and local secrets; disable the renewal timer first.')
        compose('down')
        shutil.rmtree(STATE)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError, RuntimeError) as error:
        print(f'Poochcam: {error}', file=sys.stderr)
        sys.exit(1)
