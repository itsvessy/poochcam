# Linux server setup

Use a dedicated Ubuntu 24.04 LTS server with Docker Engine, the Docker Compose
plugin, Python 3 and OpenSSL. Run these commands as the server administrator from
`/opt/poochcam`. Do not copy a personal camera's server configuration into this
deployment. Images are locked by digest in `server/images.json`; MediaMTX is 1.20.1.

## Prepare

1. Copy or clone the Poochcam repository to `/opt/poochcam`.
2. Create an A record such as `camera.example.com` pointing to the server's public
   IPv4 address. In Cloudflare use **DNS only**, not the orange-cloud proxy. Do not
   add an AAAA record unless you separately configure and verify IPv6 listeners.
3. Allow inbound TCP 80 (certificate validation), 443 (viewing) and 1936 (RTMPS).
   Restrict SSH to your administrator address. Do not expose MediaMTX's 1935 or
   8888 ports. Use a provider firewall: Docker-published ports may bypass UFW rules.
4. Choose a monitored email address for certificate notices. Read the current
   [Let's Encrypt agreement](https://letsencrypt.org/repository/) before first start.

```sh
cd /opt/poochcam
sudo python3 server/poochcamctl.py setup --hostname camera.example.com --email admin@example.com
sudo python3 server/poochcamctl.py start --accept-acme-terms
sudo python3 server/poochcamctl.py doctor
sudo python3 server/poochcamctl.py credentials
```

`setup` does not contact a certificate authority or start services. It generates
independent camera, viewer and private backend-reader passwords. It refuses to
overwrite an existing setup. First `start` obtains a certificate and activates
TLS; an ACME failure leaves media unavailable rather than exposing plaintext media.
Correct DNS/firewall problems and run `start` again. Existing certificates are reused.

The credentials command displays passwords. Use it privately; do not paste its
output into issues, build logs or chat. The same information is in
`server/state/connection.txt` (mode 0600, within a mode-0700 directory).

## Connect the phone

Paste the generated `rtmps://HOST:1936/dogcam?user=camera&pass=...` address into Camera
connection. It is a secret. Add `https://HOST/watch/` as the optional viewing link.
Save, allow Camera and Microphone permissions, and tap Start Camera. The browser
asks for the separate viewer credentials. Check picture and sound on another network.

Viewer authentication covers `/watch/` and all `/dogcam/` resources, including the
MediaMTX fallback viewer and `hls.min.js`. The proxy supplies the backend reader's
credentials only on the internal HLS connection. Camera credentials cannot read;
viewer credentials cannot publish. No anonymous MediaMTX permissions are configured.
Do not put viewer passwords in the URL or QR code. Browsers may retain HTTP Basic
credentials for a session; use a private browsing session on shared devices and
close it afterward. Rotate credentials to revoke access reliably.

## Supervision and certificates

Docker restart policies start both services after reboot. `stop` persists across
ordinary daemon recovery; **Docker's unless-stopped policy also preserves an explicit
stop across daemon restarts**. `start` resumes explicitly. Enable Docker at boot.

Install these files as `/etc/systemd/system/poochcam-renew.service` and
`/etc/systemd/system/poochcam-renew.timer` (paths assume `/opt/poochcam`):

```ini
# poochcam-renew.service
[Unit]
Description=Renew and check Poochcam certificates
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/poochcam
ExecStart=/usr/bin/python3 /opt/poochcam/server/poochcamctl.py renew
ExecStart=/usr/bin/python3 /opt/poochcam/server/poochcamctl.py doctor
TimeoutStartSec=240
```

```ini
# poochcam-renew.timer
[Unit]
Description=Check Poochcam certificates twice daily

[Timer]
OnCalendar=*-*-* 03,15:00:00
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target
```

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now poochcam-renew.timer
sudo python3 server/poochcamctl.py renew-test
sudo systemctl list-timers poochcam-renew.timer
```

Renewal runs Certbot without giving a container the Docker socket. Nginx configuration
is tested before graceful reload, so active uploads need not be disconnected. A
failed renewal or a certificate with under 14 days remaining produces a nonzero
service result. Check `systemctl --failed` and `journalctl -u poochcam-renew.service`.
No phone notifications are implemented. Stop the renewal timer when intentionally
stopping or removing the service; enable it again when resuming.

## Operate, rotate and roll back

```sh
sudo python3 server/poochcamctl.py status
sudo python3 server/poochcamctl.py stop
sudo python3 server/poochcamctl.py start
sudo python3 server/poochcamctl.py restart
sudo python3 server/poochcamctl.py backup --output /root/poochcam-backup.tar.gz
sudo python3 server/poochcamctl.py rotate
```

Rotation interrupts the stream and invalidates all old camera/viewer passwords.
Retrieve the new credentials and update both devices. Rotation also changes the
private backend reader. Keep an encrypted backup before changing credentials or
upgrading. Backup archives contain passwords and TLS private keys; never commit them.

Restore at the same absolute installation path: stop the services, move the current
`server/state` to a private recovery directory, inspect your own backup archive's
file list, then extract its `state/` directory inside `server/`. Run `doctor` and
`start`, then verify audio/video. Container recreation after a restore or image
change uses `start`; reloading the proxy refreshes upstream DNS resolution.

The reference setup disables recording, replay, API, metrics, pprof, RTSP, WebRTC
and SRT. HLS uses a short memory buffer. Docker logs rotate at 5 MiB × 3 per service;
routine HTTP access logging is off. Certbot rotated logs older than seven days are
removed during renewal. Configure a bounded system journal on the host too.

Neither container status nor HTTP 200 proves healthy media. Verify decoded picture
and sound in the viewer. A frozen image can repeat with advancing timestamps.

To remove: disable the renewal timer, retain an encrypted backup if needed, then
run `sudo python3 server/poochcamctl.py remove --confirm-remove`. This removes the
containers and local credentials/certificates. Remove the DNS record and any VPS
separately; stopping a VPS usually does not stop its billing.

## Advanced private Mac setup

A Mac with MediaMTX and a private VPN can also host Poochcam, but it is not the
Linux reference deployment. Keep HLS on loopback and route HTTPS viewing through
Tailscale Serve. Bind RTMP only to the Mac's private VPN address and restrict
publishing to the camera's VPN address. Configure the app with that RTMP address
and explicitly acknowledge the private-network requirement. Tailscale must be
connected on the relevant devices. Do not expose plaintext RTMP or anonymous HLS
to the internet. Keep the Mac powered, awake, logged in and supervised independently
of a terminal window. Existing personal Mac installations should retain their own
configuration and rollback material; this package does not modify them.
