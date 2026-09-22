export function nativeHlsSupported(video) {
  return Boolean(video.canPlayType("application/vnd.apple.mpegurl"));
}

export function initialPosition(ranges, delay = 6) {
  if (!ranges.length) return null;
  const index = ranges.length - 1;
  const start = ranges.start(index), end = ranges.end(index);
  return end - start >= delay + 2 ? Math.max(start + 0.5, end - delay) : null;
}

export class PoochcamPlayer {
  constructor({ video, Hls, onState = () => {}, visible = () => true,
    now = () => performance.now(),
    setTimer = (callback, delay) => globalThis.setTimeout(callback, delay),
    clearTimer = id => globalThis.clearTimeout(id),
    source = "/dogcam/index.m3u8" }) {
    Object.assign(this, { video, Hls, onState, visible, now, setTimer, clearTimer, source });
    this.engine = nativeHlsSupported(video) ? "native" : Hls?.isSupported() ? "hls.js" : "unsupported";
    this.state = "idle";
    this.wanted = false;
    this.suspended = false;
    this.retryTimer = null;
    this.retryCount = 0;
    this.generation = 0;
    this.hls = null;
    this.events = [];
    this.listeners = [];
    video.defaultPlaybackRate = 1;
    video.playbackRate = 1;
    this.bind("ratechange", () => {
      if (video.playbackRate !== 1 && video.playbackRate !== 0) {
        this.log("rate_reset", { from: video.playbackRate });
        video.playbackRate = 1;
      }
    });
    for (const event of ["loadedmetadata", "durationchange", "progress", "canplay"]) {
      this.bind(event, () => this.primeNative());
    }
    this.bind("timeupdate", () => this.progress());
    this.bind("waiting", () => {
      if (this.wanted && !this.rebuilding && !this.suspended && this.retryTimer === null) {
        this.setState("buffering", "Waiting for a little more video and sound.");
      }
    });
    this.bind("error", () => {
      if (this.wanted && !this.rebuilding) {
        this.log("media_error", { code: video.error?.code });
        this.retry();
      }
    });
    this.bind("ended", () => { if (this.wanted) this.retry(); });
    this.setState(this.engine === "unsupported" ? "unsupported" : "idle",
      this.engine === "unsupported" ? "Open this page in Safari on your iPhone." : "Tap Watch to start video and sound.");
  }

  bind(type, handler) {
    this.video.addEventListener(type, handler);
    this.listeners.push([type, handler]);
  }

  log(type, detail = {}) {
    this.events.push({ at: Math.round(this.now()), type, ...detail });
    if (this.events.length > 200) this.events.shift();
  }

  setState(state, message) {
    if (state !== this.state) this.log("state", { state });
    this.state = state;
    this.onState({ state, message, wanted: this.wanted, engine: this.engine });
  }

  clearRetry() {
    if (this.retryTimer !== null) this.clearTimer(this.retryTimer);
    this.retryTimer = null;
  }

  watch() {
    if (this.engine === "unsupported") return;
    this.wanted = true;
    this.suspended = false;
    this.retryCount = 0;
    this.connect();
  }

  pause() {
    this.wanted = false;
    this.generation++;
    this.clearRetry();
    this.video.pause();
    this.hls?.stopLoad();
    this.setState("paused", "Viewing is paused. The camera keeps running.");
  }

  connect() {
    if (!this.wanted || !this.visible() || this.suspended) return;
    this.clearRetry();
    const generation = ++this.generation;
    this.rebuilding = true;
    this.hls?.destroy();
    this.hls = null;
    this.video.pause();
    this.video.removeAttribute("src");
    this.video.load();
    this.video.playbackRate = 1;
    this.video.defaultPlaybackRate = 1;
    this.primed = false;
    this.moving = false;
    this.lastTime = null;
    this.lastProgress = this.now();
    this.rebuilding = false;
    this.setState("connecting", "Connecting to home…");
    if (this.engine === "native") {
      // Called synchronously by Watch: preserve Safari's user gesture for sound.
      this.video.src = this.source;
      this.video.load();
      this.play(generation);
    } else {
      const hls = new this.Hls({
        lowLatencyMode: false,
        maxLiveSyncPlaybackRate: 1,
        liveSyncDurationCount: 3,
        maxBufferLength: 12,
        maxMaxBufferLength: 24,
        backBufferLength: 6,
      });
      this.hls = hls;
      hls.on(this.Hls.Events.ERROR, (_event, data) => {
        if (generation === this.generation && data.fatal) {
          this.log("hls_error", { detail: data.details });
          this.retry();
        }
      });
      hls.on(this.Hls.Events.MEDIA_ATTACHED, () => {
        if (generation === this.generation) {
          hls.loadSource(this.source);
          this.play(generation);
        }
      });
      hls.attachMedia(this.video);
    }
  }

  play(generation) {
    let promise;
    try { promise = this.video.play(); }
    catch (error) { this.playError(error, generation); return; }
    Promise.resolve(promise).catch(error => this.playError(error, generation));
  }

  playError(error, generation) {
    if (generation !== this.generation || !this.wanted || this.suspended) return;
    if (error.name === "NotAllowedError") {
      this.wanted = false;
      this.clearRetry();
      this.video.pause();
      this.setState("gesture", "Tap Watch to allow video and sound.");
    } else if (error.name !== "AbortError") {
      this.log("play_error", { name: error.name });
      this.retry();
    }
  }

  primeNative() {
    if (this.engine !== "native" || !this.wanted || this.primed || this.moving || this.rebuilding) return;
    try {
      const position = initialPosition(this.video.seekable);
      if (position !== null) {
        this.primed = true;
        this.lastTime = null;
        this.video.currentTime = position;
        this.log("initial_position", { position });
      }
    } catch { /* Safari may not expose a seekable range yet. Its buffering remains active. */ }
  }

  progress() {
    const time = this.video.currentTime;
    if (this.wanted && !this.video.paused && !this.video.seeking && !this.suspended) {
      if (this.lastTime !== null && time > this.lastTime + 0.05 && time - this.lastTime < 3) {
        this.lastProgress = this.now();
        this.moving = true;
        this.retryCount = 0;
        this.clearRetry();
        this.setState("live", "You're watching home. Use your phone’s buttons to adjust the volume.");
      }
      this.lastTime = time;
    }
  }

  tick() {
    if (!this.wanted || !this.visible() || this.suspended || this.retryTimer !== null) return;
    const age = this.now() - this.lastProgress;
    if (age > 20000) this.retry();
    else if (age > 8000 && this.state === "live") {
      this.setState("buffering", "Waiting for a little more video and sound.");
    }
  }

  retry() {
    if (!this.wanted || this.suspended || this.retryTimer !== null) return;
    const delay = Math.min(30000, 5000 * ++this.retryCount);
    this.setState("offline", "Check the camera phone and Tailscale. We’ll keep trying.");
    this.log("retry_scheduled", { delay });
    this.retryTimer = this.setTimer(() => {
      this.retryTimer = null;
      this.connect();
    }, delay);
  }

  suspend() {
    this.suspended = true;
    this.generation++;
    this.clearRetry();
    this.video.pause();
    this.hls?.stopLoad();
  }

  resume() {
    if (!this.suspended) return;
    this.suspended = false;
    if (this.wanted) this.connect();
  }

  snapshot() {
    let ahead = 0;
    const ranges = this.video.buffered;
    for (let i = 0; i < ranges.length; i++) {
      if (ranges.start(i) <= this.video.currentTime && ranges.end(i) >= this.video.currentTime) {
        ahead = ranges.end(i) - this.video.currentTime;
      }
    }
    return { engine: this.engine, state: this.state, wanted: this.wanted,
      currentTime: this.video.currentTime, playbackRate: this.video.playbackRate,
      bufferedAhead: ahead, muted: this.video.muted, events: [...this.events] };
  }

  destroy() {
    this.pause();
    this.hls?.destroy();
    for (const [type, handler] of this.listeners) this.video.removeEventListener(type, handler);
  }
}
