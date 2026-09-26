# Poochcam naming and compatibility

Poochcam is an independent adaptation of Moblin. The project, app targets, schemes,
products, source folders, app entrypoints and Swift modules use Poochcam names.
The main source folder is `ios/Poochcam`; its app-specific code remains in
`ios/Poochcam/Poochcam`.

Renaming does not change the production bundle identity, Keychain storage or saved
camera setup. Existing bundle identifiers and compatibility values remain stable
so a name change does not create a different app or invalidate stored data.

## Names deliberately retained

- **Attribution and history:** Moblin's licenses, copyright notices, credits and
  factual historical release notes retain their original names. Upstream URLs,
  external services and third-party package names still identify their actual
  projects. See [UPSTREAM.md](../UPSTREAM.md).
- **Shared identity:** inherited app-group identifiers, the screen-recording
  extension's `.Moblin-Capture` bundle suffix and the widget kind
  `MoblinWidgetApp` remain stable identifiers, not the app's display name.
- **Stored settings:** legacy JSON keys and enum raw values keep their serialized
  spelling. Renaming these values without a migration would lose compatibility
  with existing settings.
- **Interoperability:** the `.moblinSettings` file extension, `moblin://` import
  URLs, `_moblin._tcp` service name and legacy browser/chat aliases are retained
  where inherited code uses them to exchange data with existing clients.
- **Moblink:** this is a distinct interoperability protocol and retains its name.
- **Bundled assets:** `Moblin Meme`, `Moblin pixels`, `Moblin party` and
  `Moblin trillionaire` retain their stored asset identities so existing references
  still resolve.

Retaining an identifier does not enable its associated feature in the dedicated
Poochcam camera app. The inherited auxiliary targets remain outside the iPhone
release. Future compatibility migrations require a separate change with explicit
data and protocol handling; a branding replacement must not silently alter them.

## Verification and rollback

On September 25, 2026, the renamed source passed unsigned iPhone Release and arm64
iOS Simulator Debug builds. Both products retain `com.vessy.poochcam`, the original
third-party notices and the final browser compatibility resources. The camera
controller, configuration/Keychain storage and camera UI code are unchanged.
Fourteen Python checks and nineteen Node checks passed, including legacy settings
and all sixteen remote-filter messages round-tripping, plus old/new browser API
names sharing one connection. No app was installed or submitted.

To undo this rename, revert its single source commit on a new branch from current
main and rebuild. Do not reset main or change the fixed protocol-removal checkpoint.
The earlier snapshot still contains the original names and dependencies; restoring
it does not change an already installed app. Dependency removal remains separate
work under [PROTOCOL-REMOVAL-PLAN.md](PROTOCOL-REMOVAL-PLAN.md).
