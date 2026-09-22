# Validation status

This is a development candidate, not a qualified or submitted App Store release.
The following records describe checks of the prepared candidate; distribution
still requires the open items below.

## Recorded checks

- Xcode 26.4.1: Apple silicon simulator Debug and unsigned iPhone Release builds.
  Inherited native frameworks do not support an Intel simulator build.
- 23 focused Swift configuration/log-privacy checks: complete and incomplete
  addresses, encoded credential round trips, optional viewer links and redaction.
- 11 Python server/site/publication checks: separate credentials, private file
  modes, invalid inputs, no setup overwrite, port isolation, local website links,
  and detection of private files in the exact Git index and reachable history.
- 18 browser-viewer checks, including native HLS at fixed playback speed,
  reconnect/pause handling and expanded-view exit.
- Isolated native MediaMTX 1.20.1 accepted generated configuration, rejected
  unauthorized publication/read access, and delivered synthetic H.264/AAC media
  that FFprobe identified and FFmpeg decoded.
- Simulator interaction checks: readable address entry, Show/Hide, Save remaining
  available for an incomplete RTMP prefix, validation messages and explicit RTMP
  confirmation. Cancelling preserves the entered address.
- Manual phone checks reported passing: saved connection after reopening, picture
  and sound, Stop and Start. These do not replace an instrumented storage audit.
- The seven unused inherited App Shortcuts phrase tables were removed; a subsequent
  iPhone build passed without the unused-phrase diagnostics.
- The native dog icon was checked in the simulator on iOS 18.6 and 26.4.1, including
  older-system compatibility output. iOS 27 appearance remains unverified.
- September 22, 2026 publication candidate: all 52 Swift, Python and browser
  checks passed, along with the unsigned iPhone Release build. Its app bundle
  includes the native dog icon and excludes the unused artwork with unclear
  licensing. Public-source content and asset review covered the initial snapshot;
  older local history is excluded from the public branch.
- The [initial Linux CI run](https://github.com/itsvessy/poochcam/actions/runs/35724315202)
  passed on September 22, 2026: Docker RTMPS ingestion, authenticated HTTPS HLS,
  rejection of anonymous viewing, fallback viewer assets, video/audio decoding,
  and Nginx configuration/reload. This isolated test uses a temporary local
  certificate; it does not verify public certificate issuance or renewal.

## Still required

- Live certificate issuance and renewal on the public reference server.
- Signed-device reset/update behavior, denied/restored permissions, all resolutions,
  interruption recovery, accessibility and native Safari authentication against
  the reference server. Unsigned simulator Keychain failures do not qualify storage.
- Two independent self-hosting beta users and final real-device screenshots.
- Runtime endpoint/storage audit, aggregated privacy report and the unresolved
  dependency/native-binary licensing in [PRIVACY-AUDIT.md](PRIVACY-AUDIT.md).
- Public website HTTPS, support reply verification, actual review-server access
  and the final App Store Connect configuration.

No unattended reliability or remote phone-alert qualification is implied by these
checks. The app has no outage-notification or recording/replay service.
