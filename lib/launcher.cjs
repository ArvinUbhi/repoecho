'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');

function commandIndex(args) {
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--root') { i++; continue; }
    if (args[i] === '--json' || args[i].startsWith('--root=')) continue;
    return args[i].startsWith('-') ? -1 : i;
  }
  return -1;
}

function invocation(args, root, env) {
  const cli = path.join(root, 'skill', 'scripts', 'repoecho_cli.py');
  if (!fs.existsSync(cli)) throw new Error('Bundled skill is missing. Reinstall the npm package, or run npm run build in a source checkout.');
  const forwarded = [...args];
  const index = commandIndex(forwarded);
  if (forwarded[index] === 'setup' && !forwarded.some(x => x === '--project' || x.startsWith('--project=')) && !forwarded.includes('--no-path')) {
    forwarded.push('--no-path'); // npm owns PATH shims; never create a competing launcher.
  }
  const childEnv = { ...env, PYTHONDONTWRITEBYTECODE: '1', REPOECHO_DISTRIBUTION: 'npm' };
  if (env.REPOECHO_PYTHON) {
    if (!path.isAbsolute(env.REPOECHO_PYTHON) || /\.(cmd|bat)$/i.test(env.REPOECHO_PYTHON)) {
      throw new Error('REPOECHO_PYTHON must be an absolute path to a Python executable, without arguments.');
    }
    return { command: env.REPOECHO_PYTHON, args: [cli, ...forwarded], env: childEnv };
  }
  return { command: 'uv', args: ['run', '--no-project', '--no-config', '--python', '3.12', '--script', cli, ...forwarded], env: childEnv };
}

function main(args, options = {}) {
  const root = options.root || path.resolve(__dirname, '..');
  const env = options.env || process.env;
  const write = options.write || (text => process.stdout.write(text + '\n'));
  const error = options.error || (text => process.stderr.write(text + '\n'));
  const spawn = options.spawn || spawnSync;
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (args.length === 1 && args[0] === '--version') { write(pkg.version); return 0; }
  if (args.length === 1 && ['--help', '-h'].includes(args[0])) {
    write(`RepoEcho ${pkg.version} (npm)\n\nSetup: repoecho setup --replace\nUse: repoecho status | query "question" --compact | storage | doctor\nControls: repoecho cache on|off; repoecho branch only|all\nUpdate: npm install -g repoecho@latest, then repoecho setup --replace\nRuntime: uv with Python 3.12, or an absolute REPOECHO_PYTHON executable.\nPut --root PATH and --json before a repository command.\nUse repoecho COMMAND --help for command-specific options.`);
    return 0;
  }
  if (args[commandIndex(args)] === 'update') {
    error('This command is managed by npm. Run npm install -g repoecho@latest (or your approved version), then repoecho setup --replace. Existing caches are preserved.');
    return 2;
  }
  try {
    const call = invocation(args, root, env);
    const result = spawn(call.command, call.args, { stdio: 'inherit', shell: false, windowsHide: true, env: call.env });
    if (result.error) {
      if (result.error.code === 'ENOENT') error('RepoEcho runtime was not found. Install uv on PATH, or set REPOECHO_PYTHON to an approved Python 3.10+ executable. No system Python is needed with uv.');
      else error(`RepoEcho could not start its runtime (${result.error.code || 'unknown error'}). Check executable permissions and run repoecho --help.`);
      return 2;
    }
    return result.status ?? (128 + (os.constants.signals[result.signal] || 1));
  } catch (err) { error(err.message); return 2; }
}
module.exports = { main, invocation, commandIndex };
