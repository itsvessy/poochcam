#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def generate(checkouts):
    pins = json.loads((ROOT / 'ios/Poochcam.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved').read_text())['pins']
    packages = {path.name.lower(): path for path in checkouts.iterdir() if path.is_dir()}
    sections = ['Poochcam — third-party notices\n\nBased on Moblin by Erik Moqvist. Independent project; not endorsed by Moblin.\n']
    for title, path in [('Moblin — MIT', ROOT / 'ios/LICENSE'),
                        ('Embedded HaishinKit — BSD 3-Clause', ROOT / 'ios/Moblin/Media/HaishinKit/LICENSE.md')]:
        sections.append(title + '\n\n' + path.read_text())
    inventory = []
    for pin in pins:
        package = packages.get(pin['identity'])
        entry = {'name': pin['identity'], 'source': pin['location'], 'revision': pin['state']['revision'], 'notices': []}
        if package:
            revision = subprocess.check_output(['git', '-C', str(package), 'rev-parse', 'HEAD'], text=True).strip()
            if revision != pin['state']['revision']:
                raise RuntimeError('Checkout does not match Package.resolved: ' + pin['identity'])
            files = sorted(path for path in package.rglob('*') if path.is_file() and
                           re.fullmatch(r'(license|licence|copying|notice)(\.[a-z]+)?', path.name, re.I) and
                           '.git' not in path.parts and 'MetalPetalExamples' not in path.parts)
            for path in files:
                relative = str(path.relative_to(package))
                entry['notices'].append(relative)
                sections.append(f"{pin['identity']} — {pin['location']}\nRevision: {revision}\n{relative}\n\n" + path.read_text())
        entry['status'] = 'notice-found' if entry['notices'] else 'license-not-found-review-required'
        inventory.append(entry)
    attribution = (ROOT / 'ios/Moblin/View/Settings/About/AboutAttributionsSettingsView.swift').read_text().split('private let imageAttributions')[0]
    strings = re.findall(r'"([^"\n]+)"', attribution)
    sections.append('Bundled upstream sound attribution\n\n' + '\n'.join(strings) +
                    '\n\nCC0: https://creativecommons.org/publicdomain/zero/1.0/\n'
                    'CC BY 3.0: https://creativecommons.org/licenses/by/3.0/\n'
                    'CC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n')
    sections.append('Native binary dependencies\n\nSrtSwift, Rist and DataChannel reference binary XCFrameworks. '
                    'Their checksums are in the pinned package manifests. Full transitive native-library license '
                    'and source-provision requirements must be verified before distributing an app archive. '
                    'This notice file is not evidence that that review is complete.')
    (ROOT / 'ios/Moblin/Poochcam/ThirdPartyNotices.txt').write_text(('\n\n' + '=' * 72 + '\n\n').join(sections) + '\n')
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'docs/dependency-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'Generated notices for {len(pins)} locked packages; {sum(not p["notices"] for p in inventory)} require license review.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('checkouts', type=Path)
    generate(parser.parse_args().checkouts)
