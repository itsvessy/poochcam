class Poochcam {
  constructor() {
    this.timer = setInterval(() => {
      this.send({ ping: {} });
    }, 2000);
    this.onmessage = null;
    this.textDecoder = new TextDecoder();
  }

  publish(message) {
    this.send({ publish: { message: message } });
  }

  subscribe(topic) {
    this.send({ subscribe: { topic: topic } });
  }

  handleMessage(message) {
    if (this.onmessage) {
      const json = this.textDecoder.decode(Uint8Array.fromBase64(message));
      this.onmessage(JSON.parse(json).message.data);
    }
  }

  send(message) {
    window.webkit.messageHandlers.poochcam.postMessage(JSON.stringify(message));
  }
}

const poochcam = new Poochcam();

// Compatibility for existing browser widgets using the upstream API.
const Moblin = Poochcam;
const moblin = poochcam;
