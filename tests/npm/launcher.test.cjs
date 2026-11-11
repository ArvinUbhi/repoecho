'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { main, invocation } = require('../../lib/launcher.cjs');
const root = path.resolve(__dirname, '../..');
require('../../scripts/build-package.cjs');

test('version and help need no runtime or home writes', () => {
  const output = [];
  const options = { root, env: {}, write: x => output.push(x), spawn: () => { throw new Error('Unexpected runtime'); } };
  assert.equal(main(['--version'], options), 0);
  assert.equal(output[0], require('../../package.json').version);
  assert.equal(main(['--help'], options), 0);
  assert.match(output[1], /setup --replace/);
});
test('uv receives exact arguments with no command shell', () => {
  const args = ['--root', "C:\\work repo's\\app", 'query', 'stop & $(echo nope); "job"', '--compact'];
  let received;
  assert.equal(main(args, { root, env: { HTTPS_PROXY: 'http://example.invalid:8080' }, spawn: (...x) => { received = x; return { status: 0 }; } }), 0);
  assert.equal(received[0], 'uv');
  assert.deepEqual(received[1].slice(-args.length), args);
  assert.equal(received[2].shell, false);
  assert.equal(received[2].env.HTTPS_PROXY, 'http://example.invalid:8080');
});
test('setup preserves npm PATH ownership and respects project installs', () => {
  assert.equal(invocation(['setup', '--replace'], root, {}).args.at(-1), '--no-path');
  assert.ok(!invocation(['setup', '--project', 'some project'], root, {}).args.includes('--no-path'));
  assert.equal(invocation(['--json', '--root', '/app', 'setup'], root, {}).args.at(-1), '--no-path');
});
test('explicit Python is invoked as an executable, never as a shell expression', () => {
  const executable = path.join(os.tmpdir(), 'python with spaces', 'python.exe');
  const call = invocation(['status'], root, { REPOECHO_PYTHON: executable });
  assert.equal(call.command, executable);
  assert.equal(call.args.at(-1), 'status');
  assert.throws(() => invocation([], root, { REPOECHO_PYTHON: 'python --unsafe' }), /absolute path/);
});
test('runtime errors and exit status propagate without echoing environment secrets', () => {
  const messages = [];
  const opts = { root, env: {}, error: x => messages.push(x) };
  assert.equal(main(['status'], { ...opts, spawn: () => ({ status: 7 }) }), 7);
  assert.equal(main(['status'], { ...opts, spawn: () => ({ error: { code: 'ENOENT', message: 'secret' } }) }), 2);
  assert.match(messages[0], /Install uv/);
  assert.ok(!messages[0].includes('secret'));
});
test('npm installations do not invoke the ZIP updater', () => {
  const output = [];
  assert.equal(main(['update'], { root, error: x => output.push(x), spawn: () => { throw new Error('must not run'); } }), 2);
  assert.match(output[0], /npm install -g/);
});
