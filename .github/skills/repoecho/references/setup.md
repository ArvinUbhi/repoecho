# Setup, daily use and measurement

Prerequisites for the easy shell interface: Git, GitHub CLI (`gh`) and `uv` on PATH. Windows also needs `sh` from Git for Windows. uv selects Python 3.10+ automatically; its first invocation may download Python. The cache itself is local and has no API/network requirement. Offline machines need a compatible Python already installed; set `UV_OFFLINE=1` to disallow downloads. Do not install or modify the target repository's Python environment.

From a downloaded RepoEcho checkout:

```sh
uv run --no-project --python '>=3.10' tools/install.py --gh
```

From a loaded skill, use the same uv command with its absolute `scripts/setup_repoecho.py` path. The complete skill, including installer, CLI and benchmark, is self-contained. Setup registers a supported gh **shell alias**, not an extension; the alias points at the installed personal skill, so the download checkout can be removed. Use `--replace` to update an existing skill. A different existing alias is protected; `--replace-alias` is an explicit override. Setup rolls back the skill copy if alias registration fails. After installation/update, run `/skills reload` in Copilot CLI.

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

To update: pull the trusted RepoEcho checkout, rerun its installer with `--gh --replace`, then reload Copilot skills. `gh repoecho setup --gh` repairs a missing alias from the installed skill; it does not download updates. `gh repoecho setup --project /path/to/repo` copies the installed skill for a team; the personal gh alias still uses the personal version. Avoid running different skill versions against the same cache: policy changes intentionally invalidate notes. Remove just the shell command with `gh alias delete repoecho`; existing caches and skill files remain.

If uv is unavailable, Python 3.10+ can execute `scripts/repoecho_cli.py` directly. If gh is unavailable, installation without `--gh` still provides the Copilot skill. Never claim gh setup succeeded if its prerequisite checks or alias registration failed.
