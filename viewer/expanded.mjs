// Expand the existing page container. Never hand the video to iOS's native player:
// that handoff can pause it on return and desynchronize the inline controls.
export class ExpandedView {
  constructor({ container, document, onChange = () => {} }) {
    Object.assign(this, { container, document, onChange });
    this.active = false;
    this.nativeFullscreen = false;
    this.changed = () => {
      if (document.fullscreenElement === container) {
        if (this.active) this.nativeFullscreen = true;
        else this.leaveFullscreen(); // A pending entry completed after the user exited.
      } else if (this.nativeFullscreen) this.collapse();
    };
    this.keydown = event => {
      if (event.key === "Escape" && this.active && !document.fullscreenElement) {
        event.preventDefault();
        this.exit();
      }
    };
    document.addEventListener("fullscreenchange", this.changed);
    document.addEventListener("keydown", this.keydown);
  }

  async enter() {
    if (this.active) return;
    this.active = true;
    this.container.classList.add("is-expanded");
    this.document.body.classList.add("viewer-expanded");
    this.onChange(true);
    // iPhone Safari may not support fullscreen for ordinary page elements.
    // The CSS expansion remains usable, with the same video and controls.
    if (!this.container.requestFullscreen || this.document.fullscreenElement) return;
    try {
      await this.container.requestFullscreen();
      if (!this.active) await this.leaveFullscreen();
      else this.nativeFullscreen = this.document.fullscreenElement === this.container;
    } catch { /* Keep the in-page expansion when the browser declines fullscreen. */ }
  }

  async leaveFullscreen() {
    if (this.document.fullscreenElement !== this.container) return true;
    try {
      await this.document.exitFullscreen();
      return this.document.fullscreenElement !== this.container;
    } catch { return false; }
  }

  async exit() {
    if (await this.leaveFullscreen()) this.collapse();
  }

  collapse() {
    this.active = false;
    this.nativeFullscreen = false;
    this.container.classList.remove("is-expanded");
    this.document.body.classList.remove("viewer-expanded");
    this.onChange(false);
  }

  toggle() { return this.active ? this.exit() : this.enter(); }

  destroy() {
    this.document.removeEventListener("fullscreenchange", this.changed);
    this.document.removeEventListener("keydown", this.keydown);
    return this.exit();
  }
}
