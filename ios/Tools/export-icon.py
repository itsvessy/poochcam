#!/usr/bin/env python3
"""Export the native Poochcam icon and its visual review sheet on macOS."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


APPEARANCES = ("Default", "Dark", "TintedLight", "TintedDark", "ClearLight", "ClearDark")
SMALL_SIZES = (60, 40, 29)
IOS_ROOT = Path(__file__).resolve().parent.parent
DESIGN_ROOT = IOS_ROOT / "Design" / "PoochcamIcon"


def command_output(command):
    return subprocess.check_output(command, text=True).strip()


def run(command):
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed: {' '.join(map(str, command))}\n{result.stdout}{result.stderr}"
        )
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icon", type=Path, default=IOS_ROOT / "Moblin" / "PoochcamIcon.icon")
    parser.add_argument("--output", type=Path, default=DESIGN_ROOT / "Exports")
    parser.add_argument("--preview", type=Path, default=DESIGN_ROOT / "PoochcamIcon-preview.png")
    parser.add_argument("--background", default="233D33", help="Opaque export corner color (RRGGBB)")
    parser.add_argument("--tint-color", type=float, default=0.42)
    parser.add_argument("--tint-strength", type=float, default=0.6)
    args = parser.parse_args()
    color = args.background.removeprefix("#")
    if len(color) != 6 or any(c not in "0123456789abcdefABCDEF" for c in color):
        parser.error("--background must be a six digit RGB hex color")
    if not 0 <= args.tint_color <= 1 or not 0 <= args.tint_strength <= 1:
        parser.error("tint values must be between zero and one")
    icon = args.icon.resolve()
    if not (icon / "icon.json").is_file():
        parser.error(f"No icon.json in {icon}")

    # Follow the selected Xcode instead of assuming an installation or version.
    developer = Path(command_output(["xcode-select", "--print-path"]))
    renderer = developer.parent / "Applications" / "Icon Composer.app" / "Contents" / "Executables" / "ictool"
    if not renderer.is_file():
        parser.error("The selected Xcode does not contain Icon Composer; select a full Xcode 26+ installation")
    output = args.output.resolve()
    preview = args.preview.resolve()
    output.mkdir(parents=True, exist_ok=True)
    preview.parent.mkdir(parents=True, exist_ok=True)

    # Render the small icons independently so this checks native size-dependent rendering.
    for appearance in APPEARANCES:
        for size in (1024, *SMALL_SIZES):
            filename = f"{appearance}.png" if size == 1024 else f"{appearance}-{size}pt@1x.png"
            command = [str(renderer), str(icon), "--export-image", "--output-file", str(output / filename),
                       "--platform", "iOS", "--rendition", appearance,
                       "--width", str(size), "--height", str(size), "--scale", "1"]
            if appearance.startswith("Tinted"):
                command += ["--tint-color", str(args.tint_color), "--tint-strength", str(args.tint_strength)]
            run(command)
        print(f"Exported {appearance}: 1024 px and 60/40/29 pt", flush=True)

    helper = Path(__file__).with_name("icon-preview.swift")
    # Compilation products stay outside the repository.
    with tempfile.TemporaryDirectory(prefix="poochcam-icon-export-") as temporary:
        temporary = Path(temporary)
        executable = temporary / "icon-preview"
        run(["xcrun", "swiftc", "-module-cache-path", str(temporary / "module-cache"),
             str(helper), "-o", str(executable)])
        run([str(executable), "opaque", str(output / "Default.png"),
             str(output / "PoochcamIcon-1024.png"), color])
        run([str(executable), "sheet", str(output), str(preview)])

    digest = hashlib.sha256()
    for source in sorted(path for path in icon.rglob("*") if path.is_file()):
        digest.update(source.relative_to(icon).as_posix().encode())
        digest.update(b"\0")
        digest.update(source.read_bytes())
    metadata = {
        "sourcePackage": "Moblin/PoochcamIcon.icon" if icon == IOS_ROOT / "Moblin" / "PoochcamIcon.icon" else str(icon),
        "sourceSHA256": digest.hexdigest(),
        "xcode": command_output(["xcodebuild", "-version"]),
        "renderer": command_output([str(renderer), "--version"]),
        "nativeAppearances": list(APPEARANCES),
        "smallSizesInPoints": list(SMALL_SIZES),
        "smallSizeScale": 1,
        "tintColor": args.tint_color,
        "tintStrength": args.tint_strength,
        "opaqueExport": "PoochcamIcon-1024.png",
        "opaqueExportBackground": "#" + color.upper(),
        "opaqueExportMethod": "Native default preview composited over an opaque sRGB square using CoreGraphics. Filled corners retain the rendered system edge lighting. This PNG is a rendered export, not the editable unmasked source or the Xcode app-icon input.",
    }
    (output / "export-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Opaque 1024px export: {output / 'PoochcamIcon-1024.png'}")
    print(f"Preview sheet: {preview}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
