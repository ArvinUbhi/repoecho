# Install RepoEcho through npm

The first public npm publication requires maintainer authentication. The commands below apply after publication; before then, download the `npm-package` artifact from a successful GitHub Actions Tests run and install its `.tgz` file.

## Standard setup

Install Node.js 22+, npm, uv and Git through your organisation's approved channels. Copilot CLI must already be installed. No gh, API key or system Python is needed when uv can supply Python.

```powershell
npm install -g repoecho@1.6.0 --ignore-scripts
repoecho setup --replace
```

In Copilot run `/skills reload`, then follow the README to add the RepoEcho instructions to your application's `AGENTS.md`. Run `repoecho doctor` inside that application. Do not run repository commands from the installed skill directory.

## Corporate registry and TLS

Use the company registry that mirrors approved public npm packages:

```powershell
npm install -g repoecho@1.6.0 --ignore-scripts --registry=https://npm.example.internal/
```

Your registry administrator must approve or mirror the package. npm's user configuration controls registry authentication and proxy routing. Use your organisation's approved credential setup; never commit tokens or proxy passwords. If HTTPS_PROXY is already set in your PowerShell profile, run npm from that PowerShell session. Some corporate configurations additionally require npm's `https-proxy` setting; follow your IT-provided npm configuration.

For a corporate CA certificate:

```powershell
npm config set cafile "C:\certs\corporate-ca.pem"
```

Keep TLS verification enabled. npm and uv have separate download configuration: npm installing successfully does not mean uv can download Python. Have IT provision Python 3.12 through uv or use an approved existing Python 3.10+ executable:

```powershell
$env:REPOECHO_PYTHON = 'C:\ApprovedPython\python.exe'
repoecho setup --replace
```

Persist that environment variable in your PowerShell profile if needed. It is a path, not a command with arguments. Copilot's installed skill normally uses uv; provision uv's Python 3.12 for the agent workflow even if you use the override for manual CLI commands.

## Offline installation

Obtain the approved `.tgz` from your internal distribution channel. npm requires no package dependencies or lifecycle scripts:

```powershell
npm install -g .\repoecho-1.6.0.tgz --offline --ignore-scripts
repoecho setup --replace
```

Provision Node, uv and Python beforehand. The skill is bundled; setup performs no GitHub download. Never distribute an application's `.repoecho` cache in this package.

## Updating and switching from ZIP

```powershell
npm install -g repoecho@1.6.0 --ignore-scripts
repoecho setup --replace
```

Change the version to the approved release. Reload Copilot's skills. Updates preserve local repository caches; changed source evidence or incompatible formats still require refresh.

For migration from ZIP, check `Get-Command repoecho -All` in PowerShell (or `type -a repoecho` on POSIX). The old ZIP launcher may precede npm's shim. Remove only the old RepoEcho launcher or adjust PATH; keep other tools in its directory. Use the npm-installed command explicitly if needed. `npm prefix -g` shows npm's global prefix: the command is `repoecho.cmd` there on Windows and `bin/repoecho` there on POSIX. npm setup suppresses creation of another standalone launcher.

To uninstall the npm command: `npm uninstall -g repoecho`. The installed Copilot skill and application caches remain; remove those separately only if you want to stop using the skill or delete learned knowledge.
