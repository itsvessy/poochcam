#!/usr/bin/env python3
"""Check candidate files, the exact Git index, or every commit in a public branch.

Reports file names and categories only; never prints matching secrets.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRECTORIES = {'artifacts', 'runtime', 'diagnostics', 'backups', 'publication-private',
                       'xcuserdata', '__pycache__', '.build', '.git'}
PRIVATE_SUFFIXES = {'.mobileprovision', '.p12', '.p8', '.key', '.pem', '.ipa', '.log', '.xcarchive'}
CONTENT_RULES = (
    ('private key or credential', re.compile(
        rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----|'
        rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}')),
    ('personal filesystem path', re.compile(rb'/Users/[A-Za-z0-9._ -]+/|[A-Za-z]:\\Users\\[A-Za-z0-9._ -]+\\')),
    ('private tailnet address', re.compile(
        rb'\b100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.\d+\.\d+\b|tail[a-z0-9]+\.ts\.net')),
    ('hard-coded Apple signing team', re.compile(rb'DEVELOPMENT_TEAM\s*=\s*["\x27]?[A-Z0-9]{10}["\x27]?\s*(?:;|\n|$)')),
    ('private support destination', re.compile(rb'[A-Za-z0-9._%+-]+@vessy\.ca', re.I)),
)
REQUIRED_SITE = ['index.html', 'setup/index.html', 'support/index.html',
                 'privacy/index.html', 'credits/index.html']


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def inspect(name, data):
    path = Path(name)
    failures = []
    if (set(path.parts) & PRIVATE_DIRECTORIES or name.startswith(('server/state/', 'ios/Design/')) or
            any(part.endswith('.xcarchive') for part in path.parts) or
            path.name == 'User.xcconfig' or path.name == '.env' or
            (path.name.startswith('.env.') and path.name != '.env.example') or
            path.suffix.lower() in PRIVATE_SUFFIXES or path.name == '.DS_Store'):
        failures.append(name + ': private or generated file')
    for label, pattern in CONTENT_RULES:
        if pattern.search(data):
            failures.append(name + ': ' + label)
    return failures


def read_blobs(root, entries):
    """Read exact index/tree contents rather than the current working files."""
    # Each entry is (path, mode, object ID); no symlink is followed.
    request = b''.join(oid.encode() + b'\n' for _, _, oid in entries)
    output = subprocess.check_output(['git', '-C', str(root), 'cat-file', '--batch'], input=request)
    position = 0
    result = {}
    for name, mode, expected in entries:
        end = output.index(b'\n', position)
        oid, kind, size = output[position:end].decode().split()
        if oid != expected or kind != 'blob':
            raise ValueError('Unexpected Git object for ' + name)
        size = int(size)
        position = end + 1
        result[name] = (mode, output[position:position + size])
        position += size + 1
    return result


def repository_entries(root, mode='working', revision=None):
    if mode == 'working':
        paths = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0')
        result = {}
        for value in paths:
            if not value:
                continue
            name = value.decode()
            path = root / name
            if path.is_symlink():
                result[name] = ('120000', b'')
            elif path.is_file():
                result[name] = ('100644', path.read_bytes())
        return result
    entries = []
    if mode == 'staged':
        for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
            if not row:
                continue
            metadata, name = row.decode().split('\t', 1)
            file_mode, oid, stage = metadata.split()
            if stage != '0':
                raise ValueError('Unresolved merge in ' + name)
            entries.append((name, file_mode, oid))
    else:
        for row in git(root, 'ls-tree', '-r', '-z', revision).split(b'\0'):
            if not row:
                continue
            metadata, name = row.decode().split('\t', 1)
            file_mode, kind, oid = metadata.split()
            if kind != 'blob':
                raise ValueError('Submodules require a separate audit: ' + name)
            entries.append((name, file_mode, oid))
    return read_blobs(root, entries)


def audit_entries(entries, require_release=True):
    failures = []
    for name, (mode, data) in entries.items():
        if mode not in ('100644', '100755'):
            failures.append(name + ': symlink or unsupported Git entry')
        failures.extend(inspect(name, data))
    if require_release:
        for name in REQUIRED_SITE:
            if 'site/' + name not in entries:
                failures.append('Missing website route: ' + name)
        image_entry = entries.get('server/images.json')
        if image_entry is None:
            failures.append('Missing pinned server image manifest')
        else:
            try:
                images = json.loads(image_entry[1])
                if not images or not all(isinstance(value, str) and re.search(r'@sha256:[0-9a-f]{64}$', value)
                                         for value in images.values()):
                    failures.append('Unpinned server image')
            except (ValueError, AttributeError, TypeError):
                failures.append('Invalid server image manifest')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--staged', action='store_true', help='Inspect the exact Git index')
    mode.add_argument('--history', metavar='REF', help='Inspect every commit reachable from this ref')
    args = parser.parse_args()
    failures = set()
    try:
        if args.history:
            commits = git(ROOT, 'rev-list', '--end-of-options', args.history).decode().splitlines()
            if not commits:
                raise ValueError('No commits found')
            for commit in commits:
                entries = repository_entries(ROOT, 'tree', commit)
                failures.update(commit[:12] + ': ' + failure for failure in audit_entries(entries))
            scope = f'{len(commits)} reachable commit(s)'
        else:
            entries = repository_entries(ROOT, 'staged' if args.staged else 'working')
            failures.update(audit_entries(entries))
            scope = f'{len(entries)} ' + ('staged' if args.staged else 'working') + ' files'
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print('Public scan could not complete: ' + str(error), file=sys.stderr)
        return 1
    for failure in sorted(failures):
        print(failure)
    if failures:
        return 1
    print(f'Public-source scan passed for {scope}. Manual content and asset review is still required.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
