"""Exercise actual Swift serialization declarations without building the iOS app.

Run with: python3 tests/test_branding_compatibility.py
Only the unrelated SettingsFace dependency is stubbed. The settings classes,
enums, and keyed-container helpers below are extracted from application source.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'ios/Poochcam'


def declaration(path, prefix):
    source = path.read_text()
    start = source.index(prefix)
    opening = source.index('{', start)
    depth = 1
    for offset in range(opening + 1, len(source)):
        if source[offset] == '{':
            depth += 1
        elif source[offset] == '}':
            depth -= 1
            if depth == 0:
                return source[start:offset + 1]
    raise ValueError(f'Unclosed declaration {prefix} in {path}')


SWIFT_CHECKS = r'''
func check(_ condition: Bool, _ message: String = "") {
    precondition(condition, message)
}

let decoder = JSONDecoder()
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]

func decode<T: Decodable>(_ type: T.Type, _ fixture: String) throws -> T {
    try decoder.decode(type, from: Data(fixture.utf8))
}

func json<T: Encodable>(_ value: T) throws -> String {
    String(decoding: try encoder.encode(value), as: UTF8.self)
}

func object<T: Encodable>(_ value: T) throws -> [String: Any] {
    try JSONSerialization.jsonObject(with: encoder.encode(value)) as! [String: Any]
}

// A true legacy value catches silent fallback to the false default.
let debug = try decode(SettingsDebug.self, #"{"enhancedMoblinSrt":true,"maximumLogLines":73}"#)
check(debug.enhancedPoochcamSrt)
check(debug.maximumLogLines == 73)
let debugJSON = try object(debug)
check(debugJSON["enhancedMoblinSrt"] as? Bool == true)
check(debugJSON["enhancedPoochcamSrt"] == nil)
check(try decode(SettingsDebug.self, json(debug)).enhancedPoochcamSrt)
check(try !decode(SettingsDebug.self, "{}").enhancedPoochcamSrt)

let browser = try decode(SettingsWidgetBrowser.self,
                         #"{"moblinAccess":true,"width":720,"speechToText":true}"#)
check(browser.poochcamAccess && browser.speechToText && browser.width == 720)
let browserJSON = try object(browser)
check(browserJSON["moblinAccess"] as? Bool == true)
check(browserJSON["poochcamAccess"] == nil)
check(try decode(SettingsWidgetBrowser.self, json(browser)).poochcamAccess)
check(try !decode(SettingsWidgetBrowser.self, "{}").poochcamAccess)

let quick = try decode(SettingsQuickButtonType.self, #""Moblin in mouth""#)
check(quick == .poochcamInMouth)
check(try json(quick) == #""Moblin in mouth""#)
check(quick.toString() == "Poochcam in mouth")
check(try decode(SettingsQuickButtonType.self, #""Pause chat""#) == .chat)
check(try decode(SettingsQuickButtonType.self, #""Future button""#) == .unknown)

let srt = try decode(SettingsStreamSrtImplementation.self, #""Moblin""#)
check(srt == .poochcam)
check(try json(srt) == #""Moblin""#)
check(srt.toString() == "Poochcam")
check(try decode(SettingsStreamSrtImplementation.self, #""Official""#) == .official)

// Check every original wire case: adding CodingKeys must not lose another filter.
let filters: [(String, SettingsQuickButtonType)] = [
    ("pixellate", .pixellate), ("movie", .movie), ("grayScale", .grayScale),
    ("sepia", .sepia), ("triple", .triple), ("twin", .twin),
    ("fourThree", .fourThree), ("crt", .crt), ("pinch", .pinch),
    ("whirlpool", .whirlpool), ("poll", .poll), ("blurFaces", .blurFaces),
    ("privacy", .privacy), ("beauty", .beauty),
    ("moblinInMouth", .poochcamInMouth), ("cameraMan", .cameraMan),
]
check(filters.count == RemoteControlFilter.allCases.count)
for (key, button) in filters {
    let fixture = "{\"\(key)\":{}}"
    let filter = try decode(RemoteControlFilter.self, fixture)
    check(filter.toSettings() == button, key)
    check(try json(filter) == fixture, key)
    check(try json(RemoteControlFilter(type: button)!) == fixture, key)
}
check(RemoteControlFilter.poochcamInMouth.toString() == "Poochcam in mouth")
print("Legacy settings and all 16 remote filter cases round-trip; Poochcam labels retained.")
'''


@unittest.skipUnless(sys.platform == 'darwin' and shutil.which('swiftc'),
                     'requires the macOS Swift compiler')
class BrandingCompatibilityTests(unittest.TestCase):
    def test_legacy_settings_and_remote_wire_format(self):
        settings = APP / 'Various/Settings'
        declarations = [
            (ROOT / 'ios/Common/Various/CommonUtils.swift', 'extension KeyedEncodingContainer'),
            (ROOT / 'ios/Common/Various/CommonUtils.swift', 'extension KeyedDecodingContainer'),
            (settings / 'Settings.swift', 'enum SettingsDnsLookupStrategy:'),
            (settings / 'Settings.swift', 'class SettingsTesla:'),
            (settings / 'SettingsDebug.swift', 'enum SettingsLogLevel:'),
            (settings / 'SettingsDebug.swift', 'class SettingsDebug:'),
            (settings / 'SettingsScene.swift', 'enum SettingsWidgetBrowserMode:'),
            (settings / 'SettingsScene.swift', 'class SettingsWidgetBrowser:'),
            (settings / 'SettingsQuickButtons.swift', 'enum SettingsQuickButtonType:'),
            (settings / 'SettingsStream.swift', 'enum SettingsStreamSrtImplementation:'),
            (APP / 'RemoteControl/RemoteControl.swift', 'enum RemoteControlFilter:'),
        ]
        prelude = '''import Foundation
import Combine
struct SettingsFace: Codable {}
let pixelFormats = ["32BGRA", "420YpCbCr8BiPlanarFullRange", "420YpCbCr8BiPlanarVideoRange"]
'''
        source = prelude + '\n\n'.join(declaration(path, prefix) for path, prefix in declarations)
        with tempfile.TemporaryDirectory(prefix='poochcam-compatibility-') as temporary:
            work = Path(temporary)
            swift = work / 'CompatibilityTests.swift'
            binary = work / 'compatibility-tests'
            swift.write_text(source + '\n\n' + SWIFT_CHECKS)
            compilation = subprocess.run(
                ['swiftc', '-module-cache-path', str(work / 'module-cache'), str(swift), '-o', str(binary)],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(compilation.returncode, 0, compilation.stdout + compilation.stderr)
            execution = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(execution.returncode, 0, execution.stdout + execution.stderr)
            self.assertIn('all 16 remote filter cases round-trip', execution.stdout)


if __name__ == '__main__':
    unittest.main()
