# Build the iPhone app

Open `ios/Moblin.xcodeproj` in Xcode 26 or later with its iOS SDK and Metal toolchain.
The scheme remains **Moblin**; the product is **Poochcam**. The deployment target is
iOS 16.4, iPhone only. Keep the package revisions in `Package.resolved` unchanged.

For signing, copy `ios/Config/User.xcconfig.example` to the ignored
`ios/Config/User.xcconfig`. Set your personal `DEVELOPMENT_TEAM`. The intended App
Store bundle identifier is `com.vessy.poochcam`; use a unique identifier when building
your own fork. Leave provisioning automatic. No historical provisioning profile
path is required. Do not commit `User.xcconfig`, certificates or profiles.

```sh
./tools/build_ios.sh simulator
./tools/build_ios.sh release
```

Both commands compile unsigned. Simulator builds use arm64 because upstream native
frameworks do not contain the required Intel simulator slices. Neither command
installs the app on a device, creates an App Store submission or publishes anything.

For a signed build or archive, select your personal team in Xcode, choose a supported
device or Any iOS Device, and use Product → Archive when the release checklist is
complete. Inspect the privacy report and Validate App before your own upload.

The public app starts unconfigured. Existing private-profile defaults are deliberately
not imported. Pasting a publishing URL is required; ordinary relaunches and app updates
retain the new Keychain configuration and picture-quality choice. Reset removes the
configuration. A missing installation marker clears leftover Keychain data before
fresh onboarding; restoring to a different device requires setup again.

## Verification

The public website uses only Python's standard library:

```sh
python3 tools/build_site.py
python3 -m unittest discover -s tests -p 'test_site.py'
```

Run these commands from the repository root. The generated `site/` directory is
the only asset directory selected by the root `wrangler.jsonc` for Cloudflare
Workers. It contains no server configuration or private camera credentials.
No Worker script is required for this static website. See [RELEASE.md](RELEASE.md)
for the Git integration's build, deploy and preview commands.

Validate the hosting configuration without uploading anything:

```sh
npx --yes wrangler@4.70.0 deploy --dry-run
npx --yes wrangler@4.70.0 versions upload --dry-run
```

These checks do not verify account access, the live hostname or HTTPS issuance.

The remaining local checks are:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.mjs
mkdir -p artifacts
swiftc -module-cache-path artifacts/swift-module-cache ios/Moblin/Poochcam/PoochcamConfiguration.swift tests/ConfigurationTests.swift -o artifacts/configuration-tests
artifacts/configuration-tests
python3 tools/check_public.py
```

The focused configuration checks run on macOS without the full app. The inherited
Moblin test target expects Mac Catalyst, which the dedicated iPhone target disables;
it is not the release test suite. Follow the physical-device checklist separately.

## App icon

The editable app icon is `ios/Moblin/PoochcamIcon.icon`. Open it in Icon Composer;
the seven SVG layers and `icon.json` are the production source. Preserve front-to-back
layer ordering. The app-icon build setting is `PoochcamIcon`.

Run `python3 ios/Tools/export-icon.py` to generate native appearance exports and a
preview sheet with the selected Xcode toolchain. These outputs go to the ignored
`ios/Design/` directory. Private reference artwork and simulator screenshots are
not required to build the app and are not included in the public repository.
