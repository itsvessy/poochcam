import test from "node:test";
import assert from "node:assert/strict";
import { PoochcamPlayer, initialPosition } from "../viewer/player.mjs";

function ranges(start, end) {
  return start === undefined ? { length: 0 } : { length: 1, start: () => start, end: () => end };
}
class Video extends EventTarget {
  currentTime = 0; paused = true; seeking = false; muted = false; readyState = 0;
  playbackRate = 1; defaultPlaybackRate = 1; seekable = ranges(); buffered = ranges();
  native = true; loads = 0; plays = 0;
  canPlayType() { return this.native ? "probably" : ""; }
  load() { this.loads++; this.currentTime = 0; }
  pause() { this.paused = true; }
  play() { this.plays++; this.paused = false; return this.failure ? Promise.reject(this.failure) : Promise.resolve(); }
  removeAttribute(name) { if (name === "src") this.src = ""; }
  emit(type) { this.dispatchEvent(new Event(type)); }
}
function setup(video = new Video(), Hls) {
  const clock = { time: 0 }, timers = new Map(), states = [];
  let next = 0;
  const player = new PoochcamPlayer({ video, Hls, now: () => clock.time,
    setTimer: (fn, delay) => { const id = next++; timers.set(id, { fn, delay }); return id; },
    clearTimer: id => timers.delete(id), onState: state => states.push(state) });
  return { player, video, timers, clock, states };
}
function move(video, time) { video.currentTime = time; video.emit("timeupdate"); }

test("Safari uses native HLS even when a JavaScript player exists", () => {
  class Hls { constructor() { throw new Error("must not instantiate on Safari"); } }
  Hls.isSupported = () => true;
  const { player, video } = setup(new Video(), Hls);
  player.watch();
  assert.equal(player.engine, "native");
  assert.equal(video.src, "/dogcam/index.m3u8");
  assert.equal(video.muted, false);
  assert.equal(video.playbackRate, 1);
  assert.equal(video.plays, 1);
});

test("native startup seeks behind the available edge once, never on every play", () => {
  const { player, video } = setup();
  player.watch(); video.seekable = ranges(100, 114); video.emit("loadedmetadata");
  assert.equal(video.currentTime, 108);
  move(video, 108); move(video, 108.25);
  assert.equal(player.state, "live");
  video.seekable = ranges(106, 120); video.emit("progress"); video.emit("play");
  assert.equal(video.currentTime, 108.25);
  assert.equal(initialPosition(ranges(0, 4)), null);
});

test("metadata or a seek does not falsely mark media as live", () => {
  const { player, video } = setup(); player.watch();
  video.readyState = 4; video.emit("canplay"); assert.notEqual(player.state, "live");
  move(video, 90); assert.notEqual(player.state, "live");
  video.seeking = true; move(video, 95); assert.notEqual(player.state, "live");
  video.seeking = false; move(video, 95); assert.notEqual(player.state, "live");
  move(video, 95.2); assert.equal(player.state, "live");
});

test("playback speed corrections cannot accelerate audio", () => {
  const { player, video } = setup(); player.watch();
  video.playbackRate = 1.5; video.emit("ratechange"); assert.equal(video.playbackRate, 1);
  assert.equal(player.events.at(-1).type, "rate_reset");
});

test("outage retries coalesce and Pause prevents later restart", () => {
  const { player, video, timers, clock } = setup(); player.watch();
  clock.time = 21000; player.tick(); video.emit("error"); player.tick();
  assert.equal(player.state, "offline"); assert.equal(timers.size, 1);
  assert.equal([...timers.values()][0].delay, 5000);
  player.pause(); assert.equal(timers.size, 0);
  video.emit("error"); clock.time += 60000; player.tick();
  assert.equal(player.state, "paused"); assert.equal(video.plays, 1);
});

test("browser timers receive the global receiver during retry and cancellation", () => {
  const originalSet = globalThis.setTimeout, originalClear = globalThis.clearTimeout;
  let scheduled = 0, cancelled = 0;
  globalThis.setTimeout = function (_callback, delay) {
    assert.equal(this, globalThis); assert.equal(delay, 5000); scheduled++; return 123;
  };
  globalThis.clearTimeout = function (id) {
    assert.equal(this, globalThis); assert.equal(id, 123); cancelled++;
  };
  try {
    const player = new PoochcamPlayer({ video: new Video() });
    player.watch(); player.retry(); player.pause();
    assert.equal(scheduled, 1); assert.equal(cancelled, 1);
  } finally {
    globalThis.setTimeout = originalSet; globalThis.clearTimeout = originalClear;
  }
});

test("fresh progress cancels a pending retry without restarting sound", () => {
  const { player, video, timers } = setup(); player.watch(); player.retry();
  move(video, 1); move(video, 1.2);
  assert.equal(player.state, "live"); assert.equal(timers.size, 0); assert.equal(video.plays, 1);
});

test("hidden pages suspend; resume reconnects only while viewing is wanted", () => {
  const { player, video, timers } = setup(); player.watch(); player.retry();
  player.suspend(); assert.equal(timers.size, 0); assert.equal(video.paused, true);
  player.resume(); assert.equal(video.plays, 2);
  player.pause(); player.suspend(); player.resume(); assert.equal(video.plays, 2);
});

test("autoplay denial asks for a tap rather than retrying indefinitely", async () => {
  const video = new Video(); video.failure = { name: "NotAllowedError" };
  const { player, timers } = setup(video); player.watch(); await Promise.resolve();
  assert.equal(player.state, "gesture"); assert.equal(player.wanted, false); assert.equal(timers.size, 0);
});

test("a rejected old play promise cannot restart a paused viewer", async () => {
  const video = new Video(); video.failure = { name: "NotSupportedError" };
  const { player, timers } = setup(video); player.watch(); player.pause(); await Promise.resolve();
  assert.equal(player.state, "paused"); assert.equal(timers.size, 0);
});

test("desktop fallback disables low-latency catch-up and retains mute on reconnect", () => {
  class Hls {
    static isSupported() { return true; }
    static Events = { ERROR: "error", MEDIA_ATTACHED: "attached" };
    handlers = {};
    constructor(config) { this.config = config; }
    on(event, callback) { this.handlers[event] = callback; }
    attachMedia() { this.handlers.attached(); }
    loadSource(url) { this.url = url; }
    destroy() {} stopLoad() {}
  }
  const video = new Video(); video.native = false;
  const { player } = setup(video, Hls); player.watch();
  assert.equal(player.hls.config.maxLiveSyncPlaybackRate, 1);
  assert.equal(player.hls.config.lowLatencyMode, false);
  video.muted = true; player.connect(); assert.equal(video.muted, true);
});
