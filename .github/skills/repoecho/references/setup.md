# Setup, daily use and measurement

Prerequisites for the easy shell interface: Git and `uv` on PATH. `gh` is optional. Windows needs `sh` from Git for Windows only for the optional gh alias. uv selects Python 3.10+ automatically; its first invocation may download Python. The cache itself is local and has no API/network requirement. Offline machines need a compatible Python already installed; set `UV_OFFLINE=1` to disallow downloads. Do not install or modify the target repository's Python environment.

From a downloaded RepoEcho checkout:

```sh
uv run --no-project --python 3.12 tools/install.py
```

From a loaded skill, use the same uv command with its absolute `scripts/setup_repoecho.py` path. The complete skill, including installer, CLI and benchmark, is self-contained. Setup installs a `repoecho` command into `~/.local/bin`, adds that directory to the user PATH if needed, and points it at the installed personal skill. On Windows open a new PowerShell window to pick up the user PATH; on bash/zsh open a new terminal. The downloaded checkout can then be removed. Run `repoecho status`, `repoecho cache off` or `repoecho branch only` from the target repository. Use `--no-path` to skip command/PATH installation. On Windows without PATH changes, you can run `uv run --no-project --python 3.12 "$HOME\.copilot\skills\repoecho\scripts\repoecho_cli.py" status` from the target repository instead. `--home` creates a portable command under the specified home without changing your real PATH. Project-local installs never modify global PATH. An unrelated command with the same name is not overwritten.

The optional `--gh` also registers a supported gh **shell alias**, not an extension; it requires gh and sh. Use `--replace` to update an existing skill. A different existing alias is protected; `--replace-alias` is an explicit override. Setup rolls back the skill copy if alias registration fails. After installation/update, run `/skills reload` in Copilot CLI.

Daily controls (from any directory inside a Git worktree):

```sh
gh repoecho status
gh repoecho off
gh repoecho on
gh repoecho cache off
gh repoecho cache on
gh repoecho branch only
gh repoecho branch all
gh repoecho doctor
gh repoecho benchmark --files 2000 --notes 20 --runs 5
```

`status` is cheap: it shows controls, current branch and effective state without opening the knowledge database. `inspect` explicitly scans and reports cache state. `on` changes only the skill gate; other disabled gates stay disabled. Branch policies are checked afresh after every Git checkout. Worktrees use their own roots. Explicit `--root /path` overrides discovery, including when indexing a subtree. For non-Git directories, always work from the chosen root or supply it explicitly. Put global options before the command: `gh repoecho --root /path --json status`.

All engine commands remain available: `scan`, `plan`, `capture`, `remember`, `query` and `forget`. Knowledge output stays JSON. The gh interface does not synthesize notes; use Copilot `/repoecho` to learn or refresh them. A full scan only refreshes hashes, not LLM-written notes.

Benchmark output is JSON; redirect it to a file to compare runs. It creates its own temporary Java fixture and never changes the caller's files, branches or modes. It measures cold scan, warm retrieval, stale rejection, off modes and return-to-main revision reuse. Scale `--files`, `--notes` and `--runs`; add `--plain` for non-Git fixtures. Timings include helper interpreter startup and Git work, excluding the outer gh/uv launch and all model thinking/network latency. Measure model response time separately on matched tasks if evaluating LLM savings; do not infer it from local timings.

To update: pull the trusted RepoEcho checkout, rerun its installer with `--gh --replace`, then reload Copilot skills. `gh repoecho setup --gh` repairs a missing alias from the installed skill; it does not download updates. `gh repoecho setup --project /path/to/repo` copies the installed skill for a team; the personal gh alias still uses the personal version. Compatible releases from 1.3.3 onward reuse the same cache. Updating from older releases automatically adopts matching saved notes on query without resetting review deadlines. Avoid downgrading to older helpers: they still use release-bound policy checks. Remove just the shell command with `gh alias delete repoecho`; existing caches and skill files remain.

If uv is unavailable, Python 3.10+ can execute `scripts/repoecho_cli.py` directly. If gh is unavailable, ordinary installation provides both the Copilot skill and the `repoecho` command. Never claim gh setup succeeded if its prerequisite checks or alias registration failed.

To update a personal installation without Git or gh, use `repoecho update`; to use a browser-downloaded ZIP, run `repoecho update --zip PATH`. The bundled `tools/update.sh` invokes the same updater through uv from a downloaded checkout. The updater compares semantic MAJOR.MINOR.PATCH versions, rejects downgrades and calls the installer with `--replace`. Close Copilot first on Windows to avoid folder locks.

For corporate proxies, `repoecho update` inherits `HTTPS_PROXY` from the calling PowerShell environment, including credentials set by its profile. It never prints the proxy URL. If TLS verification fails because of corporate interception, use `repoecho update --ca-cert PATH` with an IT-provided PEM root certificate, or use a browser-downloaded `--zip PATH`. Do not disable certificate verification.
