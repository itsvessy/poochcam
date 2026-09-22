import test from "node:test";
import assert from "node:assert/strict";
import { ExpandedView } from "../viewer/expanded.mjs";

function setup() {
  const classes = () => new Set();
  const classList = () => {
    const values = classes();
    return { add: name => values.add(name), remove: name => values.delete(name), contains: name => values.has(name) };
  };
  const document = new EventTarget();
  document.body = { classList: classList() };
  document.fullscreenElement = null;
  const container = { classList: classList() };
  document.exitFullscreen = async () => {
    document.fullscreenElement = null;
    document.dispatchEvent(new Event("fullscreenchange"));
  };
  const states = [];
  const expanded = new ExpandedView({ container, document, onChange: active => states.push(active) });
  return { document, container, expanded, states };
}

test("iPhone without element fullscreen expands and exits without a video API", async () => {
  const { expanded, container, document } = setup();
  await expanded.enter();
  assert.equal(expanded.active, true);
  assert.equal(container.classList.contains("is-expanded"), true);
  assert.equal(document.body.classList.contains("viewer-expanded"), true);
  await expanded.exit();
  assert.equal(expanded.active, false);
  assert.equal(container.classList.contains("is-expanded"), false);
  assert.equal(document.body.classList.contains("viewer-expanded"), false);
});

test("browser refusal retains a usable in-page expanded view", async () => {
  const { expanded, container } = setup();
  container.requestFullscreen = async () => { throw new Error("NotSupportedError"); };
  await expanded.enter();
  assert.equal(expanded.active, true);
  await expanded.exit();
  assert.equal(expanded.active, false);
});

test("standard fullscreen and browser exit keep the page controls synchronized", async () => {
  const { expanded, container, document } = setup();
  container.requestFullscreen = async () => {
    document.fullscreenElement = container;
    document.dispatchEvent(new Event("fullscreenchange"));
  };
  await expanded.enter();
  assert.equal(expanded.nativeFullscreen, true);
  await document.exitFullscreen();
  assert.equal(expanded.active, false);
  assert.equal(container.classList.contains("is-expanded"), false);
  await expanded.enter();
  await expanded.exit();
  assert.equal(document.fullscreenElement, null);
  assert.equal(expanded.active, false);
});

test("Escape closes fallback expansion and releases page scrolling", async () => {
  const { expanded, document } = setup();
  await expanded.enter();
  const escape = new Event("keydown", { cancelable: true });
  Object.defineProperty(escape, "key", { value: "Escape" });
  document.dispatchEvent(escape);
  await Promise.resolve();
  assert.equal(expanded.active, false);
  assert.equal(escape.defaultPrevented, true);
  assert.equal(document.body.classList.contains("viewer-expanded"), false);
});

test("exit during pending fullscreen entry cannot leave the viewer trapped", async () => {
  const { expanded, container, document } = setup();
  let resolve;
  container.requestFullscreen = () => new Promise(done => { resolve = done; });
  const entering = expanded.enter();
  await expanded.exit();
  document.fullscreenElement = container;
  document.dispatchEvent(new Event("fullscreenchange"));
  resolve();
  await entering;
  assert.equal(expanded.active, false);
  assert.equal(document.fullscreenElement, null);
});

test("a declined browser exit retains the exit control for another attempt", async () => {
  const { expanded, container, document } = setup();
  container.requestFullscreen = async () => { document.fullscreenElement = container; };
  document.exitFullscreen = async () => { throw new Error("temporary rejection"); };
  await expanded.enter();
  await expanded.exit();
  assert.equal(expanded.active, true);
  assert.equal(container.classList.contains("is-expanded"), true);
});

test("an older pending entry does not close a newly requested expanded view", async () => {
  const { expanded, container, document } = setup();
  const pending = [];
  container.requestFullscreen = () => new Promise(resolve => pending.push(resolve));
  const first = expanded.enter();
  await expanded.exit();
  const second = expanded.enter();
  document.fullscreenElement = container;
  document.dispatchEvent(new Event("fullscreenchange"));
  pending[0](); await first;
  assert.equal(expanded.active, true);
  assert.equal(document.fullscreenElement, container);
  pending[1](); await second;
  await expanded.exit();
  assert.equal(expanded.active, false);
});
