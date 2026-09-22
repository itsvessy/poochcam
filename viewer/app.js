import { PoochcamPlayer, nativeHlsSupported } from "./player.mjs?v=1";
import { ExpandedView } from "./expanded.mjs?v=1";

const video = document.querySelector("#video");
const watch = document.querySelector("#watch");
const sound = document.querySelector("#sound");
const fullscreen = document.querySelector("#fullscreen");
const room = document.querySelector("#room");
const placeholder = document.querySelector("#placeholder");
const title = document.querySelector("#placeholder-title");
const detail = document.querySelector("#placeholder-detail");
const paused = document.querySelector("#paused");
const message = document.querySelector("#message");
const status = document.querySelector("#status");
const statusText = document.querySelector("#status-text");
const buffering = document.querySelector("#buffering");
const help = document.querySelector("#help");
const reconnect = document.querySelector("#reconnect");
const watchLabel = document.querySelector("#watch-label");
const watchIcon = document.querySelector("#watch-icon");
const expanded = new ExpandedView({ container: document.querySelector(".viewer"), document,
  onChange: () => fullscreenState() });
const labels = { idle: "Ready to watch", live: "Live", connecting: "Connecting", buffering: "Reconnecting",
  offline: "Reconnecting", paused: "Paused", gesture: "Tap to watch", unsupported: "Use Safari" };
const emptyStates = {
  idle: ["A moment at home.", "See the room. Hear your dog. Tap Watch live below."],
  connecting: ["Opening your view…", "Video and sound will start together."],
  offline: ["Can’t reach the camera.", "Trying the connection again. Open Help if this continues."],
  buffering: ["Waiting for the picture…", "Your view will resume when the connection returns."],
  paused: ["Viewing paused", "The camera keeps running. Tap Resume to check in again."],
  gesture: ["Ready when you are.", "Tap Watch live to allow video and sound."],
  unsupported: ["Open in Safari", "Use Safari on your iPhone to watch this camera."],
};
const hints = { idle: "Video and sound start together.", live: "Use your phone’s buttons to adjust the volume.",
  connecting: "Connecting to your home camera…", buffering: "Your view will resume automatically.",
  offline: "We’ll keep trying. Pause stops the retries.", paused: "Only your view is paused.",
  gesture: "One tap starts video and sound.", unsupported: "This browser can’t play the camera stream." };

function setText(element, text) {
  if (element.textContent !== text) element.textContent = text;
}

function fullscreenState() {
  const active = expanded.active;
  fullscreen.setAttribute("aria-label", active ? "Exit expanded view" : "Expand view");
  fullscreen.title = active ? "Exit expanded view" : "Expand view";
  document.querySelector("#fullscreen-icon").setAttribute("href", active ? "#i-collapse" : "#i-expand");
}

function render({ state, wanted }) {
  const hasPicture = video.readyState >= 2;
  const presentation = state === "buffering" && !hasPicture ? "connecting" : state;
  status.dataset.state = room.dataset.state = presentation;
  setText(statusText, labels[presentation]);
  const quietView = video.muted && ["idle", "live", "connecting", "gesture"].includes(presentation);
  setText(message, quietView ? "Sound is off. Tap Sound on to listen." : hints[presentation]);
  setText(watchLabel, wanted ? "Pause" : state === "paused" ? "Resume" : "Watch live");
  watchIcon.setAttribute("href", wanted ? "#i-pause" : "#i-play");
  watch.disabled = sound.disabled = reconnect.disabled = state === "unsupported";
  placeholder.hidden = state === "live" || (state === "buffering" || state === "paused") && hasPicture;
  paused.hidden = state !== "paused" || !hasPicture;
  buffering.hidden = state !== "buffering" || !hasPicture;
  if (emptyStates[presentation]) {
    setText(title, emptyStates[presentation][0]);
    const mutedDetail = { idle: "See your dog. Tap Watch live below.",
      connecting: "The picture will start with sound off.", gesture: "Tap Watch live to allow video playback." };
    setText(detail, video.muted && mutedDetail[presentation] || emptyStates[presentation][1]);
  }
  // Exit must remain available even if the stream loses its picture while expanded.
  fullscreen.disabled = !hasPicture && !expanded.active;
  fullscreen.hidden = !hasPicture && !expanded.active;
  fullscreenState();
}

document.querySelector("#help-open").addEventListener("click", () => help.showModal());
document.querySelector("#help-close").addEventListener("click", () => help.close());
help.addEventListener("click", event => { if (event.target === help) {
  const box = help.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) help.close();
} });

async function fallbackLibrary() {
  if (nativeHlsSupported(video)) return undefined;
  await new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "/dogcam/hls.min.js";
    const timer = setTimeout(() => { script.remove(); reject(new Error("Player unavailable")); }, 10000);
    script.onload = () => { clearTimeout(timer); resolve(); };
    script.onerror = () => { clearTimeout(timer); reject(new Error("Player unavailable")); };
    document.head.append(script);
  });
  return window.Hls;
}

try {
  const Hls = await fallbackLibrary();
  const player = new PoochcamPlayer({ video, Hls, onState: render,
    visible: () => document.visibilityState !== "hidden" });
  // Diagnostic state stays on this device; no analytics or audio collection.
  window.poochcamViewer = player;
  watch.addEventListener("click", () => player.wanted ? player.pause() : player.watch());
  reconnect.addEventListener("click", () => { help.close(); player.watch(); });
  sound.addEventListener("click", () => { video.muted = !video.muted; });
  video.addEventListener("volumechange", () => {
    setText(document.querySelector("#sound-label"), video.muted ? "Sound off" : "Sound on");
    document.querySelector("#sound-icon").setAttribute("href", video.muted ? "#i-muted" : "#i-sound");
    sound.setAttribute("aria-pressed", String(!video.muted));
    render({ state: player.state, wanted: player.wanted });
  });
  fullscreen.addEventListener("click", () => expanded.toggle());
  document.addEventListener("visibilitychange", () => document.hidden ? player.suspend() : player.resume());
  window.addEventListener("pagehide", () => player.suspend());
  window.addEventListener("pageshow", () => { if (!document.hidden) player.resume(); });
  setInterval(() => player.tick(), 1000);
} catch {
  setText(statusText, "Player unavailable");
  setText(title, "Let’s reconnect.");
  setText(detail, "Check Tailscale, then reload this page.");
  setText(watchLabel, "Reload");
  watch.disabled = false;
  setText(message, "The player couldn’t load. Your camera is unaffected.");
  watch.addEventListener("click", () => location.reload());
}
