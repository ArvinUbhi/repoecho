'use strict';
const fs = require('node:fs');
const pkg = require('../package.json');
const pythonVersion = fs.readFileSync('.github/skills/repoecho/scripts/repoecho.py', 'utf8').match(/^VERSION = "([^"]+)"$/m)?.[1];
if (pythonVersion !== pkg.version) throw new Error('Python and npm versions differ.');
if (process.env.GITHUB_REF_TYPE === 'tag' && process.env.GITHUB_REF_NAME !== `v${pkg.version}`) throw new Error('Release tag does not match package version.');
console.log(`Release metadata verified: ${pkg.name}@${pkg.version}`);
