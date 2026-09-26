# Poochcam

A simple portrait dog camera for iPhone. Built-in sound, three picture qualities,
one Start Camera button, and a dark screen while streaming.

**Release candidate — not yet submitted to the App Store.** Poochcam requires your
own server. There is no hosted camera service, account, advertising or subscription.

This is a source preview. Dependency licensing and native-binary provenance still
need review before distributing an app build; see [the audit](docs/PRIVACY-AUDIT.md).
The app is intended to be free; running your own server may cost money.

- [Server setup and maintenance](docs/SERVER.md)
- [Build the iPhone app](docs/BUILD.md)
- [Privacy and data-flow audit](docs/PRIVACY-AUDIT.md)
- [Protocol dependency removal plan and restore checkpoint](docs/PROTOCOL-REMOVAL-PLAN.md)
- [Release checklist and rollback](docs/RELEASE.md)
- [Upstream provenance](UPSTREAM.md)

The app sends H.264 video and AAC sound using RTMPS. The browser viewer uses HLS
and retains continuous 1× playback. Keep the camera phone powered, connected and
Poochcam in the foreground. Reopening the app never starts streaming automatically.

The reference server uses Linux, Docker, MediaMTX, Nginx and Certbot. The website
under `site/` is static HTML prepared for Cloudflare Workers static-asset hosting at
poochcam.ca. The public source owner is **itsvessy/poochcam**.

Poochcam is based on **Moblin by Erik Moqvist** and is an independent project.
See [LICENSE](LICENSE) and [third-party notices](ios/Poochcam/Poochcam/ThirdPartyNotices.txt).
