#!/usr/bin/env python3
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
ORIGIN = 'https://poochcam.ca'
PAGES = {
    '': ('A little closer to home.', '''
<section class="hero"><div><p class="eyebrow">An iPhone dog camera · Self-hosted</p>
<h1>Your spare iPhone.<br>Your dog’s room.</h1>
<p class="lead">See the room and hear your dog, with a camera you run yourself.</p>
<p>Poochcam turns an iPhone into a simple portrait camera. Plug it in, choose your picture quality and tap Start Camera. Open your private viewer on another phone.</p>
<a class="button" href="/setup/">Set up your camera <span aria-hidden="true">↗</span></a>
<p class="small">Preparing for a free App Store release. Your own server is required and may cost money to run.</p></div>
<figure class="app-mark"><img src="/assets/icon.png" width="256" height="256" alt="Poochcam paw-print app icon"><figcaption>One camera. Picture and sound.</figcaption></figure></section>
<section class="features" aria-label="Camera features"><article><h2>Start, then settle in.</h2><p>One camera button and a dark screen. Keep the phone powered and the app open while you’re away.</p></article>
<article><h2>Hear the little things.</h2><p>Built-in microphone audio travels with the picture. Check both in your browser before leaving.</p></article>
<article><h2>Your choice of detail.</h2><p>Choose 480p, 720p or 1080p before starting. 720p is a good place to begin.</p></article></section>
<section class="note"><h2>Your camera needs your server.</h2><p>Poochcam is for people who can set up a server, or have someone to help. There is no Poochcam cloud account, recording service or subscription. Our guide uses Linux and Docker.</p></section>'''),
    'setup': ('Set up your camera', '''
<p class="eyebrow">Setup</p><h1>A home for your camera feed.</h1>
<p class="lead">Set up a server once. Then everyday use is one button.</p>
<p>Poochcam is not yet available on the App Store. This guide is for people preparing their server or building from <a href="https://github.com/itsvessy/poochcam/blob/main/docs/BUILD.md">the public source</a>.</p>
<ol class="steps"><li><h2>Prepare your server</h2><p>You need a Linux server with Docker Compose, a public DNS hostname and ports 80, 443 and 1936 available. It can be a small VPS. Keep it updated and protect access to it.</p>
<p>Use the <a href="https://github.com/itsvessy/poochcam/blob/main/docs/SERVER.md">complete server guide</a> to generate passwords, install a certificate and enable renewal. Plain RTMP is only suitable inside a trusted private network or VPN.</p></li>
<li><h2>Add the connection on your iPhone</h2><p>Open Poochcam and paste the complete publishing address from the server setup into Camera connection. Add the HTTPS viewing link if you want to share it with a QR code. Save, then allow Camera and Microphone access.</p></li>
<li><h2>Choose the room and start</h2><p>Stand the camera phone in portrait, connect external power and choose a picture quality. Tap Start Camera. Use Dark Screen after positioning the camera; keep Poochcam in the foreground.</p></li>
<li><h2>Check your other phone</h2><p>Open the viewing link and enter the separate viewer username and password. Tap Watch live, turn sound on and check the picture and audio before leaving.</p></li></ol>
<aside class="note"><h2>What to expect</h2><p>Internet publishing uses RTMPS; browser viewing uses HTTPS. Your server receives and can access the media. The feed has a short delay. Reopening Poochcam requires tapping Start Camera again. No outage alerts are included.</p></aside>'''),
    'support': ('Support', '''
<p class="eyebrow">Support</p><h1>Let’s get the room back.</h1>
<p class="lead">Most connection problems start with the phone, network or server.</p>
<section class="prose"><h2>No picture?</h2><p>Keep Poochcam open on the camera phone and check that it is sending video and audio. Check the network, the saved publishing address and your server certificate. If you use a VPN, it must be connected on the relevant devices.</p>
<h2>No sound?</h2><p>Allow microphone access in iPhone Settings. In the viewer, turn Sound on and increase the phone’s volume. Keep the viewing page open.</p>
<h2>Stopped or disconnected?</h2><p>Closing the camera app stops the stream. Open it and tap Start Camera again. Network interruptions retry automatically while the app stays open; confirm picture and sound after recovery.</p>
<h2>Contact</h2><p>Email <a href="mailto:support@poochcam.ca">support@poochcam.ca</a> with the app version, iOS version and what happened. Replies may come from the developer’s existing mailbox. Do not send publishing passwords, private viewing links, pet footage or personal logs unless specifically needed and agreed.</p>
<p>You can also <a href="https://github.com/itsvessy/poochcam/issues">report a software issue on GitHub</a>. GitHub issues are public; keep private details out.</p></section>'''),
    'privacy': ('Privacy policy', '''
<p class="eyebrow">Privacy · Updated September 22, 2026</p><h1>Your room stays your business.</h1>
<section class="prose"><p>This policy describes Poochcam, an independent iPhone camera app developed by Vessy Stroumsky, and poochcam.ca.</p>
<h2>Camera and microphone</h2><p>The app uses your camera and microphone to send live video and sound to the publishing server you configure. It does not provide a developer-hosted camera service or upload ordinary self-hosted feeds to the developer. The server operator and people with valid viewing credentials can access the media.</p>
<p>RTMPS and HTTPS encrypt transport to and from the server. This is not end-to-end encryption that hides media from the server operator. Plain RTMP does not encrypt media or credentials and should only be used inside a trusted private network or VPN.</p>
<h2>Information on your phone</h2><p>Connection details are stored in the iPhone Keychain using device-only protection. Picture-quality preferences stay on the device. Reset camera setup removes the stored connection details. The app does not offer recording or replay, advertising, tracking, analytics or a Poochcam account.</p>
<p>Local diagnostic logs may record connection events and device state. Publishing addresses and recognizable credential parameters are redacted. Logs are not automatically sent to the developer. Avoid sharing logs publicly.</p>
<h2>Your server and viewers</h2><p>The reference server keeps a short rolling HLS buffer in memory to deliver live video and audio. It does not record an archive. It uses authentication and transient session cookies to serve media. Routine webpage access logging is disabled; bounded operational logs may contain connection errors and IP addresses. Your server provider may separately process traffic and infrastructure logs under its own policy. The server operator controls deletion and retention.</p>
<p>The browser viewer keeps your sound preference for the current page and uses your browser’s authentication state. It does not include advertising or analytics.</p>
<h2>Beta and App Review</h2><p>A temporary developer-operated server may be offered specifically for beta testing or App Review. If you use those supplied credentials, your video, audio and connection information reach that server and may be accessible to the developer. Use a non-sensitive test scene. The service has no recording archive and is removed after testing and review finish. Ordinary self-hosting does not use this server.</p>
<h2>This website</h2><p>This static website uses Cloudflare Workers for hosting and Cloudflare for DNS and support-email routing. Cloudflare processes connection and request information, including IP addresses, to deliver and protect the site. See <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare’s privacy policy</a> for its data handling. We do not add analytics, tracking pixels or advertising cookies.</p>
<h2>Support messages</h2><p>If you email support@poochcam.ca, Cloudflare forwards the message to the developer’s existing mailbox, hosted by Google. The developer receives your address, message and any attachments to answer the request. Messages are retained while needed to resolve the request and for up to 12 months afterward, unless you request earlier deletion or a legal obligation requires retention.</p>
<h2>Your choices and contact</h2><p>You can stop streaming, revoke Camera or Microphone permission in iPhone Settings, reset the app’s connection settings and delete the app. Contact <a href="mailto:support@poochcam.ca">support@poochcam.ca</a> for privacy questions or deletion of support messages. For your server’s records, contact its operator.</p>
<h2>Changes</h2><p>Changes to this policy will be published here with an updated date.</p></section>'''),
    'credits': ('Credits', '''
<p class="eyebrow">Open source</p><h1>Built on Moblin.</h1>
<p class="lead">Poochcam is based on Moblin by Erik Moqvist.</p>
<section class="prose"><p>Moblin provides the camera, media and streaming foundation. Poochcam adapts it into a simple portrait dog camera with a browser viewer and self-hosted server guide. Poochcam is independent and is not endorsed by Moblin.</p>
<p><a href="https://github.com/eerimoq/moblin">Visit Moblin</a> · <a href="https://github.com/itsvessy/poochcam">Poochcam source</a></p>
<h2>Licenses and acknowledgements</h2><p>Moblin’s MIT copyright and permission notice are preserved. The embedded HaishinKit code carries its BSD 3-Clause notice. Bundled libraries and assets retain their own terms and attribution.</p>
<p><a href="/assets/notices.txt">Read third-party notices</a>. The same notices are accessible inside Poochcam under About &amp; open-source licenses.</p></section>'''),
}

DESCRIPTIONS = {
    '': 'Turn a spare iPhone into a portrait dog camera with live sound and a private, self-hosted browser viewer. Preparing for a free App Store release.',
    'setup': 'Prepare your own Poochcam server, connect your iPhone camera and check live picture and sound in your private browser viewer.',
    'support': 'Get help with Poochcam picture, sound and connection problems, or contact support for the self-hosted iPhone dog camera.',
    'privacy': 'How Poochcam handles camera and microphone access, connection settings, self-hosted video, website requests and support messages.',
    'credits': 'Poochcam is based on Moblin by Erik Moqvist. Find the source code, third-party licenses and acknowledgements.',
}


def render_page(slug, title, body, description, *, indexable=True):
    page_title = escape(title + ' · Poochcam')
    description = escape(description, quote=True)
    canonical = ORIGIN + '/' + (slug + '/' if slug else '')
    metadata = (f'''<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Poochcam">
<meta property="og:title" content="{page_title}"><meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{ORIGIN}/assets/icon.png">
<meta property="og:image:alt" content="Poochcam paw-print app icon">
<meta name="twitter:card" content="summary">''' if indexable else '<meta name="robots" content="noindex">')
    nav = ''.join(f'<a href="/{name + "/" if name else ""}"' +
                  (' aria-current="page"' if name == slug else '') + f'>{label}</a>'
                  for name, label in [('', 'Home'), ('setup', 'Setup'), ('support', 'Support'), ('privacy', 'Privacy'), ('credits', 'Credits')])
    # Root-relative links also work when Cloudflare serves 404.html at a deep URL.
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{description}">
<meta name="referrer" content="no-referrer"><title>{page_title}</title>
{metadata}
<link rel="icon" href="/assets/icon.png"><link rel="apple-touch-icon" href="/assets/icon.png"><link rel="stylesheet" href="/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/"><img src="/assets/icon.png" width="36" height="36" alt="">Poochcam</a><nav aria-label="Main navigation">{nav}</nav></header>
<main id="main">{body}</main><footer><p>Poochcam · Based on <a href="https://github.com/eerimoq/moblin">Moblin</a>.</p><p>Preparing for a free App Store release.<br>Your own server is required.</p></footer></body></html>'''


def build():
    for slug, (title, body) in PAGES.items():
        directory = SITE / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'index.html').write_text(render_page(slug, title, body, DESCRIPTIONS[slug]), encoding='utf-8')
    (SITE / '404.html').write_text(render_page(
        '404', 'Page not found', '''
<section class="prose"><p class="eyebrow">404 · Page not found</p>
<h1>This page wandered off.</h1>
<p class="lead">We couldn’t find that address. Let’s get you back home.</p>
<a class="button" href="/">Back to Poochcam <span aria-hidden="true">↗</span></a>
<p>Looking for help? Visit <a href="/setup/">Setup</a> or <a href="/support/">Support</a>.</p></section>''',
        'This page could not be found. Return to Poochcam or find setup and support.', indexable=False), encoding='utf-8')
    urls = '\n'.join(f'  <url><loc>{ORIGIN}/{slug + "/" if slug else ""}</loc></url>' for slug in PAGES)
    (SITE / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        urls + '\n</urlset>\n', encoding='utf-8')
    (SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n', encoding='utf-8')
    (SITE / 'assets/notices.txt').write_text((ROOT / 'ios/Poochcam/Poochcam/ThirdPartyNotices.txt').read_text())
    print('Built five static website routes, a custom 404, robots.txt and sitemap.xml.')


if __name__ == '__main__':
    build()
