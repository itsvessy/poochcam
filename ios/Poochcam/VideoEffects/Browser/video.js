class PoochcamCanvasDrawer {
  constructor(video) {
    this.video = video;
    this.canvas = document.createElement("canvas");
    this.canvasContext = this.canvas.getContext("2d");
    this.videoFrameCallbackId = null;
    this.isPlaying = false;
    document.body.appendChild(this.canvas);
    this.timer = setInterval(() => {
      this.handleTimer();
    }, 100);
  }

  tearDown = () => {
    document.body.removeChild(this.canvas);
    this.clearVideoFrameCallback();
    this.video = null;
    this.canvas = null;
    this.canvasContext = null;
    clearInterval(this.timer);
    this.timer = null;
    this.setPlaying(false);
    poochcamideoPlayingUpdated();
  };

  handleTimer = () => {
    if (this.video === null) {
      return;
    }
    if (this.video.paused) {
      this.canvas.width = 0;
      this.canvas.height = 0;
      this.clearVideoFrameCallback();
      this.setPlaying(false);
    } else if (!this.isPlaying && this.videoFrameCallbackId === null) {
      this.videoFrameCallbackId = this.video.requestVideoFrameCallback(this.handleVideoFrame);
    }
  };

  clearVideoFrameCallback = () => {
    if (this.videoFrameCallbackId !== null) {
      this.video.cancelVideoFrameCallback(this.videoFrameCallbackId);
      this.videoFrameCallbackId = null;
    }
  }

  positionCanvas = () => {
    const rect = this.video.getBoundingClientRect();
    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
    this.canvas.style.position = "absolute";
    this.canvas.style.left = rect.left + window.scrollX + "px";
    this.canvas.style.top = rect.top + window.scrollY + "px";
    this.canvas.style.width = rect.width + "px";
    this.canvas.style.height = rect.height + "px";
    this.canvas.style.zIndex = -9999;
  };

  handleVideoFrame = () => {
    if (this.canvasContext === null) {
      return;
    }
    this.positionCanvas();
    this.canvasContext.drawImage(
      this.video,
      0,
      0,
      this.canvas.width,
      this.canvas.height,
    );
    this.setPlaying(true);
    this.videoFrameCallbackId = this.video.requestVideoFrameCallback(this.handleVideoFrame);
  };

  setPlaying = (playing) => {
    if (this.isPlaying === playing) {
      return;
    }
    this.isPlaying = playing;
    poochcamVideoPlayingUpdated();
  };
}

function poochcamIsAnyVideoPlaying() {
  for (const poochcamCanvasDrawer of poochcamCanvasDrawers.values()) {
    if (poochcamCanvasDrawer.isPlaying) {
      return true;
    }
  }
  return false;
}

let poochcamPublishedVideoPlaying = false;

function poochcamVideoPlayingUpdated() {
  const videoPlaying = poochcamIsAnyVideoPlaying();
  if (videoPlaying === poochcamPublishedVideoPlaying) {
    return;
  }
  poochcamPublishedVideoPlaying = videoPlaying;
  publishVideoPlaying(videoPlaying);
}

function publishVideoPlaying(value) {
  poochcam.publish({
    videoPlaying: { value: value },
  });
}

function log(message) {
  poochcam.publish({
    log: { message: message },
  });
}

function poochcamUpdateVideosPlaysInline() {
  document.querySelectorAll("video").forEach((video) => {
    video.setAttribute("playsinline", "");
  });
}

let poochcamCanvasDrawers = new Map();

function poochcamUpdateCanvasDrawers() {
  const videos = [...document.querySelectorAll("video")];
  videos.forEach((video) => {
    if (poochcamCanvasDrawers.get(video) === undefined) {
      poochcamCanvasDrawers.set(video, new PoochcamCanvasDrawer(video));
    }
  });
  for (const [video, canvasDrawer] of poochcamCanvasDrawers.entries()) {
    if (!videos.includes(video)) {
      canvasDrawer.tearDown();
      poochcamCanvasDrawers.delete(video);
    }
  }
}

function poochcamUpdateVideosConfigured() {
  poochcamUpdateVideosPlaysInline();
  poochcamUpdateCanvasDrawers();
}

const poochcamObserver = new MutationObserver(() => {
  poochcamUpdateVideosConfigured();
});
poochcamObserver.observe(document, { childList: true, subtree: true });

document.addEventListener("DOMContentLoaded", () => {
  publishVideoPlaying(false);
  poochcamUpdateVideosConfigured();
});
