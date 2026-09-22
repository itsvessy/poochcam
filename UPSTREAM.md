# Upstream provenance

Poochcam is an independent adaptation of [Moblin](https://github.com/eerimoq/moblin),
by Erik Moqvist, licensed under MIT. It is not endorsed by Moblin.

- Base release: `ios-34.2137.0-174`
- Base commit: `1b9efe3c2f735c9a8033247a5259921401937495`
- The MIT copyright and permission notice are retained in `LICENSE` and `ios/LICENSE`.
- The embedded HaishinKit fork retains its BSD 3-Clause license.
- Dependency revisions remain locked in Xcode's `Package.resolved`.

Poochcam changes the app entrypoint, portrait camera interface, profile, onboarding,
credential storage, runtime feature initialization and audio-session defaults. The
RTMP capture/encoding/reconnect engine is retained. It also supplies an independent
browser viewer, Docker server package and documentation website.

This repository begins with a clean source export. Personal capture evidence,
server settings, signing material, build artifacts and earlier private history are
not part of this repository. The linked upstream commit preserves source provenance.

The unused `-100.gif` alert artwork is omitted because its upstream attribution did
not establish redistribution permission. The native Poochcam dog icon is supplied
as editable vector layers; private design references and generated previews are excluded.
The outstanding dependency audit in `docs/PRIVACY-AUDIT.md` applies before binary
distribution. Publishing this source does not mark that audit complete.
