# Plan: remove unused streaming dependencies from the Poochcam release

Status: planned on September 24, 2026. Dependency removal has not started.
This document authorizes no App Store submission or replacement of a working
camera installation. The checkpoint and documentation are the preparation work.

## Decision and scope

Exclude SrtSwift, Rist and DataChannel and their native binary products from the
dedicated Poochcam release build. Poochcam accepts RTMP/RTMPS publishing addresses;
its current picture, audio, portrait orientation, quality choices, local preview,
Start/Stop, Dark Screen, saved setup and reconnect behavior must remain intact.
The MediaMTX server and HLS browser viewer do not change.

Prefer compile-time separation using the existing `POOCHCAM_APP` condition and
explicit source membership where useful. Preserve upstream protocol source where
practical, without keeping its packages linked into the release. Do not replace
working capture, encoding or RTMP transport code as part of this cleanup.

Removing these libraries avoids shipping those unresolved dependencies. It does
not establish that all remaining dependencies or the final app are cleared for
distribution. Moblin MIT, HaishinKit BSD and other applicable notices stay intact.

## Restore checkpoint

- Repository: `itsvessy/poochcam`.
- Branch: `checkpoint/before-protocol-removal`, also pushed to origin.
- Exact commit: `e8c64905dda8b6b10ac6e16a3eb1e68421638d10`.
- Baseline: Poochcam-named Xcode project, target and scheme; successful unsigned
  iPhone Release build and GitHub checks on September 24, 2026.
- Leave this branch at the checkpoint. Do not commit new work to it, reset it,
  force-push it or delete it during this work. The exact SHA is the authority if
  a branch pointer is accidentally changed.

This is a source checkpoint, not a backup of signing secrets, private settings,
build caches or an installed app. Existing private build artifacts and package
caches should remain available through validation; do not publish them. A future
rebuild also depends on the Xcode toolchain and upstream artifacts being available.

The package revisions retained at the checkpoint are:

| Package | Pinned revision | Native release referenced by the manifest |
| --- | --- | --- |
| SrtSwift | `fb06b843ccd2a804672928a7bfdb3ab9b8a15579` | `libsrt-0.3.0` |
| Rist | `5bbccbc71852367be9e7ff463e2638b409e04589` | `librist-0.2.20` |
| DataChannel | `17f2aa22dfdc28c0ac4f0adee7cc02e8162060bb` | `libdatachannel-0.30.0` |

These pins preserve reproducibility information, not permission to distribute
the unresolved wrappers or binaries. The checkpoint has the same licensing gate
as the current candidate.

## Implementation sequence

1. **Start isolated work.** When implementation is requested, create
   `cleanup/remove-unused-protocols` from the then-current reviewed `main`, with a
   clean working tree. Record the base SHA and confirm the checkpoint still has
   the exact SHA above. Do not use the private pre-publication archive branch.

2. **Separate unused protocol code at compile time.** Complete this step and the
   package-removal step below together for one dependency at a time: RIST, then
   DataChannel/WHIP/WHEP, then SrtSwift/SRTLA. Keep separate reviewable commits on
   the implementation branch and verify compilation after each; squash the
   completed cleanup when merging to main.

   The main integration is
   `ios/Moblin/Various/Media.swift`: protocol objects, factories, start/stop paths,
   statistics and delegate implementations. Follow references through Model and
   ingest code, including `ModelStream`, `ModelSrtlaServer`, `ModelSrtClient`,
   `ModelRistServer`, `ModelWhipServer`, `ModelWhepClient`, camera/audio/scene
   selection and inherited settings views. Guard or exclude inactive branches
   consistently, including imports and type signatures. Shared data enums may
   remain when harmless, but an unsupported protocol must not report a successful
   connection or become selectable in Poochcam.

   Protocol-specific source clusters include `Media/HaishinKit/Srt`, `Rist` and
   `Whip`, plus `Media/SrtClient`, `Media/Srtla`, `Media/RistServer` and
   `Media/Webrtc`. The WHIP remote-preview path also needs separation; preserve
   the camera's ordinary on-device preview. Follow actual use, not names:
   `AdaptiveBitrateSrtFight` is used by RTMP and must remain unless that shared
   behavior is deliberately preserved elsewhere. Keep Processor, capture,
   H.264/AAC encoders, audio-session handling and RTMP/RTMPS intact.

   `SrtPerformanceData` has a native `CBytePerfMon` adapter despite also serving
   pure-Swift helpers; isolate that native dependency if retaining the helpers.
   Keep inherited test membership consistent for affected RIST/SRT suites without
   deleting RTMP checks. The synchronized Moblin source group automatically
   includes files: moving them into a differently named navigator group is not
   a compilation exclusion.

3. **Remove the package and link dependencies.** Remove all applicable package
   references, product dependencies and Frameworks-phase entries from
   `ios/Poochcam.xcodeproj/project.pbxproj`, including the duplicate Srt/Rist
   entries. Remove the three pins from the resolved graph after resolving the
   remaining project; keep every unrelated pinned revision unchanged. Ensure
   inherited targets do not cause the release project to resolve or link the
   removed packages indirectly. Runtime-disabled features alone are insufficient.
   The checkpoint remains the route back to the full inherited protocol build.
   Expect 20 retained pins from the current 23; investigate any unexpected
   dependency-graph change before continuing rather than upgrading packages.

4. **Update notices and the audit from evidence.** Update
   `tools/generate_notices.py`, which currently always prints a warning naming
   these three libraries. Base the generated dependency inventory and notices on
   what remains. Regenerate app notices and website notices with the existing
   tools; keep notices needed for retained source. Update `PRIVACY-AUDIT.md` with
   the exact removal and verification evidence, preserving its historical finding
   and unrelated open gates. Record native artifact names/checksums from the
   checkpoint manifests for the binary inspection.

5. **Validate before merge.** Use fresh build output for arm64 Simulator Debug
   and unsigned iPhone Release builds with the Poochcam scheme. Generate a linker
   map and inspect resolved packages, linker inputs, embedded frameworks, native
   libraries and the built product for Srt/Rist/DataChannel, libsrt/librist/
   libdatachannel and their transitive components. `otool -L` alone cannot prove
   static code is absent; combine it with linker-map and appropriate symbol
   inspection. Compare against the checkpoint. Shared libraries still required by
   other dependencies must be identified and audited, not assumed removed.

6. **Review and integrate.** Review the code diff and updated notice inventory.
   Run the established source-publication checks and relevant existing checks.
   Merge the functional cleanup as one recorded squash commit so rollback is
   unambiguous. Record its SHA, the base SHA and validation results in this
   document. Publish only reviewed source; do not upload an app binary yet.

## Acceptance checks and rollout

All checks below are future work; no new iOS builds, device installations or
camera tests are part of this planning step.

- Both clean builds succeed, with none of the three packages resolved or linked
  into the release and no unexplained native remnants. Notices match the result.
- Configuration checks still accept RTMP/RTMPS and reject SRT/RIST/WHIP addresses.
  Invalid input cannot create a false connected state.
- On a signed test device and a non-sensitive scene, verify permission handling,
  local preview, video and continuous microphone audio at 480p, 720p and 1080p,
  portrait orientation, Dark Screen, Start/Stop/start, saved setup after relaunch,
  and reset. Keep the app's bundle identity and Keychain behavior unchanged.
- Verify both private-network RTMP and valid-certificate RTMPS publishing. Check
  the existing authenticated HTTPS/HLS viewer on another device, including sound,
  expand/exit and ordinary reconnect. Use a test destination for failure tests.
  Incorrect publishing credentials and untrusted RTMPS certificates must fail
  clearly without a false live state or exposing credentials in logs.
- Interrupt test Wi-Fi for 30 seconds and two minutes, and restart the test
  MediaMTX server. Require automatic recovery within 60 seconds after service is
  available again. An intentional app exit still requires manual Start on reopen.
  Do not conduct these interruptions on the working home camera as part of cleanup.
- After short checks pass, arrange one normal workday of camera observation with
  picture and sound checked at both ends. This does not reinstate the previously
  deferred formal two-run endurance qualification. Document any regression and
  preserve evidence before changing one relevant variable and rechecking.

Keep the working camera installation and home services in place during development.
Replacing the camera app is a separate rollout step after the validation above;
the owner controls device installation and App Store/TestFlight submission.

## Rollback and later restoration

For a cleanup regression, stop rollout and retain the failure evidence. Revert the
recorded squash commit on a fresh branch from current main, review the diff and
repeat validation. This preserves unrelated changes made after the checkpoint.
Do not force-reset main or overwrite the whole project with old files.

To inspect or rebuild the exact pre-removal source independently, first ensure
the working tree is clean, then run from the repository root:

```sh
git fetch origin checkpoint/before-protocol-removal
git switch --create restore/protocols-from-checkpoint e8c64905dda8b6b10ac6e16a3eb1e68421638d10
git rev-parse HEAD
```

The last command must print `e8c64905dda8b6b10ac6e16a3eb1e68421638d10`.
If that local restore branch already exists, inspect it or use a fresh branch name;
do not overwrite it. Private signing configuration is supplied locally using the
documented ignored xcconfig. Opening this branch does not downgrade any installed
app or bypass licence requirements.

For a later feature that needs SRT, RIST or WebRTC, resolve redistribution rights
and complete native notices/source obligations first. Start a feature branch from
the current app, selectively restore the needed dependency and integration from
the checkpoint or removal commit, resolve changes against current code, and repeat
build, privacy and feature testing. Do not merge an old snapshot wholesale: Git
restoration makes the code available, but does not make the feature release-ready.

## Completion record

- Implementation branch: not created yet.
- Removal commit: none.
- Post-removal builds, binary inspection and device tests: not started.
- Dependency distribution gate: still open until implementation and audit evidence
  establish its resolution; other release gates remain separate.
