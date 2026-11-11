'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const pkg = require('../package.json');
const source = path.join(root, '.github', 'skills', 'repoecho');
const target = path.join(root, 'skill');
const version = fs.readFileSync(path.join(source, 'scripts/repoecho.py'), 'utf8').match(/^VERSION = "([^"]+)"$/m)?.[1];
if (version !== pkg.version) throw new Error(`Version mismatch: npm ${pkg.version}, engine ${version}`);
if (pkg.license !== 'MIT' || !fs.readFileSync(path.join(root, 'LICENSE'), 'utf8').includes('Copyright (c) 2026 Arvin Ubhi')) throw new Error('Missing MIT licence or attribution.');
fs.rmSync(target, { recursive: true, force: true });
fs.mkdirSync(target, { recursive: true });
fs.copyFileSync(path.join(source, 'SKILL.md'), path.join(target, 'SKILL.md'));
for (const folder of ['scripts', 'references', 'agents']) {
  fs.mkdirSync(path.join(target, folder));
  for (const entry of fs.readdirSync(path.join(source, folder), { withFileTypes: true })) {
    if (!entry.isFile() || !/\.(py|md|yaml)$/.test(entry.name)) continue;
    fs.copyFileSync(path.join(source, folder, entry.name), path.join(target, folder, entry.name));
  }
}
fs.copyFileSync(path.join(root, 'LICENSE'), path.join(target, 'LICENSE'));
