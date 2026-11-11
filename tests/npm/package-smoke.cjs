'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const npm = process.env.npm_execpath;
if (!npm) throw new Error('Run through npm test so the npm CLI executable is explicit on Windows.');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "repoecho npm's "));
function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: 'utf8', cwd: root, ...options });
  if (result.status !== 0) throw new Error(`${command} ${args.join(' ')} failed: ${result.error || result.stderr || result.stdout}`);
  return result.stdout;
}
try {
  const info = JSON.parse(run(process.execPath, [npm, 'pack', '--json', '--pack-destination', temp]))[0];
  const files = info.files.map(x => x.path);
  for (const required of ['LICENSE', 'skill/LICENSE', 'skill/SKILL.md', 'skill/scripts/repoecho.py', 'skill/scripts/setup_repoecho.py', 'skill/references/java.md', 'bin/repoecho.cjs']) assert.ok(files.includes(required), required);
  assert.ok(!files.some(x => /(^|\/)(node_modules|\.repoecho|\.git|tests|__pycache__)(\/|$)|\.pyc$|\.npmrc$/.test(x)), 'Unexpected build/cache/credential files in package');
  assert.ok(info.size < 1024 * 1024, 'Package unexpectedly exceeds 1 MiB');
  const archive = path.join(temp, info.filename);
  const prefix = path.join(temp, 'global prefix');
  run(process.execPath, [npm, 'install', '--global', '--prefix', prefix, '--ignore-scripts', '--offline', '--no-audit', '--no-fund', archive]);
  const installed = path.join(prefix, ...(process.platform === 'win32' ? [] : ['lib']), 'node_modules', 'repoecho');
  const cli = path.join(installed, 'bin/repoecho.cjs');
  const version = require('../../package.json').version;
  assert.equal(run(process.execPath, [cli, '--version']).trim(), version);
  const env = { ...process.env, PATH: (process.platform === 'win32' ? prefix : path.join(prefix, 'bin')) + path.delimiter + process.env.PATH };
  const shimVersion = process.platform === 'win32'
    ? run(process.env.ComSpec || 'cmd.exe', ['/d', '/c', 'repoecho --version'], { env })
    : run(path.join(prefix, 'bin/repoecho'), ['--version'], { env });
  assert.equal(shimVersion.trim(), version);
  const python = process.env.REPOECHO_TEST_PYTHON || run('python', ['-c', 'import sys; print(sys.executable)']).trim();
  const runtimeEnv = { ...process.env, REPOECHO_PYTHON: python };
  const home = path.join(temp, 'personal home');
  run(process.execPath, [cli, 'setup', '--home', home, '--replace'], { env: runtimeEnv });
  const skill = path.join(home, '.copilot/skills/repoecho');
  assert.ok(fs.existsSync(path.join(skill, 'SKILL.md')));
  assert.ok(fs.existsSync(path.join(skill, 'LICENSE')));
  assert.ok(!fs.existsSync(path.join(home, '.local/bin')), 'npm setup must not create competing PATH shims');
  run(process.execPath, [cli, 'setup', '--home', home, '--replace'], { env: runtimeEnv });
  const repo = path.join(temp, 'application'); fs.mkdirSync(repo);
  run(process.execPath, [cli, '--root', repo, 'cache', 'off'], { env: runtimeEnv });
  const response = JSON.parse(run(process.execPath, [cli, '--root', repo, 'query', 'example', '--compact'], { env: runtimeEnv }));
  assert.equal(response.state, 'bypassed');
  assert.ok(!fs.existsSync(path.join(repo, '.repoecho/cache.sqlite3')));
  console.log(`Packed and installed ${info.filename} (${info.size} bytes) offline with scripts disabled; PATH shim, setup, licence and engine checks passed.`);
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
