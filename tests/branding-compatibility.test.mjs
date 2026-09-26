import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

test('renamed browser API keeps existing widgets on the same connection', () => {
  const messages = [];
  let timers = 0;
  const context = vm.createContext({
    TextDecoder,
    setInterval: () => ++timers,
    window: { webkit: { messageHandlers: {
      poochcam: { postMessage: value => messages.push(JSON.parse(value)) },
    } } },
  });
  const source = readFileSync(new URL('../ios/Poochcam/VideoEffects/Browser/poochcam.js', import.meta.url), 'utf8');
  vm.runInContext(source, context);
  assert.equal(vm.runInContext('moblin === poochcam && Moblin === Poochcam', context), true);
  vm.runInContext('moblin.publish("legacy"); poochcam.subscribe("chat");', context);
  assert.deepEqual(messages, [
    { publish: { message: 'legacy' } },
    { subscribe: { topic: 'chat' } },
  ]);
  assert.equal(timers, 1, 'the compatibility alias must not create a second connection');
});
