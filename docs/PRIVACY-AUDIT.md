# Privacy and license audit — release gate

## Implemented data handling

| Flow | Handling |
| --- | --- |
| Camera/microphone | Foreground capture; H.264/AAC sent only to the configured publishing server. No background recording/replay. |
| Publishing/viewing configuration | One Keychain item, WhenUnlockedThisDeviceOnly; no cloud Keychain synchronization. |
| Settings/history | Poochcam skips upstream settings/history loading and settings persistence. The runtime profile contains a non-secret sentinel URL; the transport receives the real URL in memory. |
| Quality | App-owned UserDefaults; configuration installation marker is also app-owned. |
| Diagnostics | URL and credential-parameter redaction; RTMP server error text is replaced before logging. Local bounded logs, no automatic uploads. File sharing is disabled. |
| Integrations | Fixed profile disables platform features; connection reload and NTP initialization return early. No purchases, Watch discovery, broadcast extension or app settings-import scheme. |
| Website | Static pages; no scripts, trackers, analytics or forms. Cloudflare Workers static-asset hosting and processing of connection/request information are disclosed. Keep optional Web Analytics and injected scripts disabled; verify the deployed site. |
| Self-hosted viewer | Same-origin HTTP Basic over HTTPS; browser session/authentication and transient HLS cookies. No cross-origin media or URL credentials. |
| Review server | Explicitly disclosed developer-operated test service. Use non-sensitive scenes; do not claim the developer cannot access that service's media. |
| Support | Forwarding through Cloudflare to the existing Google-hosted mailbox. Draft policy specifies deletion within 12 months after resolution, or earlier on request. Confirm and follow this practice before publication. |

The app manifest declares FileTimestamp C617.1, SystemBootTime 35F9.1 and
UserDefaults CA92.1, with no tracking. The otherwise-unused disk-space query is
compiled out for POOCHCAM_APP, rather than declaring an unrelated purpose.
Review all required-reason APIs in the final archive, including embedded SDK manifests.

## Remaining verification before an App Store submission

- Observe network traffic from a fresh install, idle preview, streaming, reconnect
  and Stop. Confirm there are no inherited unexpected endpoints or telemetry.
- Inspect app-container files, logs and the archive for a uniquely generated test
  publishing secret after save/relaunch/start/stop/quality changes/reset. Do not use
  a real home credential. Check that Keychain persistence/reset behave on a device.
- Inspect Xcode's aggregated privacy report and the current App Store Connect
  questionnaire. The manifest is not a completed App Store privacy-label decision.
  Include any SDK behavior and retained data on a developer-operated review service.
- Confirm actual retention, support routing and website-hosting behavior against
  the privacy policy before publishing it.

## Licenses

The bundled ThirdPartyNotices file includes the Moblin MIT notice, HaishinKit BSD
notice, license/notice files found at the exact revisions of 23 Swift packages,
and retained upstream sound attribution. `dependency-inventory.json` records the
result. Regenerate using `tools/generate_notices.py PATH_TO_SOURCEPACKAGES_CHECKOUTS`.

**Not yet cleared for binary redistribution:** the pinned SrtSwift, Rist and
DataChannel wrapper repositories have no license file. SrtSwift's Swift source is
empty; Rist is a small version wrapper; DataChannel has substantive Swift code.
The three package manifests also download native XCFrameworks whose transitive
licenses, build source provenance, any modifications and source-availability
obligations need a separate audit. Do not assume Moblin's MIT license covers them.
Retaining these dependencies preserves the working media engine for this candidate.

Resolve by documenting applicable permission and complete notices/source obligations,
or remove/replace the affected unused protocol dependencies and re-verify the app.
No request has been sent to upstream maintainers. Also verify any upstream artwork
whose attribution does not itself state a redistribution license before binary release.

### Follow-up inspection — September 21, 2026

The exact local package pins still have no wrapper license files; the three public
repository root listings also contain none. Their pinned manifests identify these
downloaded artifacts in [xcframeworks](https://github.com/eerimoq/xcframeworks):

| Package | Native artifact release | Used by inherited source |
| --- | --- | --- |
| SrtSwift | `libsrt-0.3.0` | SRT output, SRT clients and SRTLA ingestion |
| Rist | `librist-0.2.20` | RIST output and ingestion |
| DataChannel | `libdatachannel-0.30.0` | WHIP output and WebRTC/WHEP ingestion |

The Poochcam publishing validator accepts only RTMP/RTMPS, but the legacy model and
media source still reference these other protocol implementations. Disabling their
runtime features does not establish that the dependencies are absent from the binary.
The recommended engineering path is to exclude the unused implementations and their
package products from the dedicated release target, then inspect the built product,
regenerate notices and recheck RTMP/RTMPS capture and reconnect. This has not yet been
implemented; permission/source-provenance review is still required if they are retained.

The unused `Alerts.bundle/-100.gif` has been removed from the public source and
release product, along with its gallery entry, because the upstream attribution
did not establish redistribution permission. The private pre-publication history
is not included in the public branch. This removal does not clear the remaining
dependency and native-binary review.

Sources: [Apple privacy details](https://developer.apple.com/app-store/app-privacy-details/),
[required-reason APIs](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitype),
[Moblin](https://github.com/eerimoq/moblin), [SrtSwift](https://github.com/eerimoq/SrtSwift),
[Rist](https://github.com/eerimoq/Rist), [DataChannel](https://github.com/eerimoq/DataChannel).
