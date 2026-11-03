# RepoEcho

**Help GitHub Copilot CLI remember your codebase between sessions.**

RepoEcho saves concise notes about your repository so Copilot can reuse what it has already learned. Before using a note, it checks the source files for changes. Missing or outdated knowledge is learned again when needed.

The aim is less repeated exploration and more focused context for your task. It works with text-based repositories across languages, with extra guidance for Java, Maven and Gradle.

## Install once

You need **GitHub Copilot CLI** and [uv](https://docs.astral.sh/uv/getting-started/installation/). Git enables branch tracking. **GitHub CLI (`gh`) is optional.**

Download this repository using **Code → Download ZIP**, then extract it. In PowerShell, from the directory containing `repoecho-main`, run:

```powershell
uv run --no-project --python 3.12 .\repoecho-main\tools\install.py
```

Alternatively, if you use Git:

```sh
git clone https://github.com/ArvinUbhi/repoecho.git
uv run --no-project --python 3.12 repoecho/tools/install.py
```

uv finds Python 3.12 and downloads it if needed. Setup installs the complete Copilot skill. No extra API key or Python packages are required. You can remove the downloaded checkout afterwards.

Already installed? Add `--replace` to the install command. Do not add `--gh` unless GitHub CLI is installed and you want its optional terminal commands.

## Use it in your repository

Open Copilot CLI in the repository you want to work on. Run:

```text
/skills reload
```

Then ask:

```text
Use /repoecho to learn this repository's architecture, build and main modules.
```

In later sessions, include RepoEcho in your normal request:

```text
Use /repoecho to find the shutdown code and help me change it.
```

Copilot retrieves relevant notes, checks that their sources still match, and learns anything missing before continuing. You do not need to write or manage notes yourself. Invoke `/repoecho` when you want this workflow; it does not automatically intercept every prompt.

## Everyday controls — no gh needed

Ask Copilot directly:

```text
Use /repoecho to show its current status.
Use /repoecho to turn caching off.
Use /repoecho to turn caching on, using Python 3.12 through uv.
Use /repoecho only on this branch.
Use /repoecho on all branches.
```

The skill, cache and branch settings must all be on for caching to work. Enabling the skill leaves a separately disabled cache off. Turning caching off keeps saved notes for later reuse.

For direct terminal control on Windows, run this from your target repository:

```powershell
$repoecho = "$HOME\.copilot\skills\repoecho\scripts\repoecho_cli.py"
uv run --no-project --python 3.12 "$repoecho" status
uv run --no-project --python 3.12 "$repoecho" cache off
uv run --no-project --python 3.12 "$repoecho" branch only
```

Replace the last command with `on`, `off`, `cache on`, `branch all`, `doctor` or `--help` as needed. If Copilot selects an incompatible Python installation, tell it to use **`uv run --python 3.12`** for RepoEcho commands.

### Optional GitHub CLI controls

If you have [GitHub CLI](https://cli.github.com/) installed, add `--gh` when running setup (and `--replace` when updating). Windows also needs `sh`, supplied by Git for Windows. This registers shortcuts such as `gh repoecho status`, `gh repoecho cache off` and `gh repoecho branch only`.

The generated gh launcher currently requests any Python 3.10 or newer. If uv selects a broken managed interpreter, use the explicit Python 3.12 commands above instead.

## Branches and multiple repositories

RepoEcho checks Git branch, status and diffs, then validates source hashes before returning notes. Uncommitted edits count as changes too. When you switch back to a branch, matching saved knowledge can be reused while it remains valid.

Each repository and linked worktree has its own local cache and settings. They are never mixed. Generated notes stay in the repository's ignored `.repoecho/` directory; do not copy or commit that directory.

To select a repository explicitly:

```powershell
uv run --no-project --python 3.12 "$repoecho" --root "C:\path\to\your-app" status
```

Use the `$repoecho` variable defined above. On macOS/Linux, the installed script is at `~/.copilot/skills/repoecho/scripts/repoecho_cli.py`.

For non-Git directories, run commands from the same root directory each time or use `--root`.

## Run a benchmark

```powershell
uv run --no-project --python 3.12 "$repoecho" benchmark --files 2000 --notes 20 --runs 5
```

Use the `$repoecho` variable defined above. With the optional gh setup, you can also run `gh repoecho benchmark`.

This creates a temporary sample repository and measures initial indexing, warm retrieval, change detection and reuse after switching branches. It leaves your repository and cache untouched.

Increase `--files` or `--notes` to test larger workloads. Save results for comparison by adding `> benchmark.json` to the command. These measurements cover the local cache helper; they do **not** measure Copilot thinking time or prove a particular LLM speedup.

## Update or troubleshoot

**ZIP download:** download and extract the latest ZIP, then run from its parent directory:

```powershell
uv run --no-project --python 3.12 .\repoecho-main\tools\install.py --replace
```

**Git clone:** from the directory containing your `repoecho` checkout:

```sh
git -C repoecho pull --ff-only
uv run --no-project --python 3.12 repoecho/tools/install.py --replace
```

Run `/skills reload` in Copilot after updating. ZIP downloads do not support `git pull`.

- **Python fails to start?** Run `uv python install 3.12`, then `uv run --python 3.12 python --version` before retrying setup.
- **Access denied when replacing the skill?** Close Copilot sessions and retry. A folder lock or permissions may prevent replacement. For a project-local installation, use `--project "C:\path\to\your-app"` instead.
- **Caching unexpectedly off?** Ask Copilot for RepoEcho status or run the direct `status` command above.
- **Copilot cannot see the skill?** Run `/skills info repoecho` after reloading.
- **Need offline use, team setup or optional gh alias repair?** See the [setup guide](.github/skills/repoecho/references/setup.md).

## More detail

RepoEcho checks whether saved evidence has changed; it cannot guarantee that every saved interpretation is correct. Copilot should still read relevant code before editing. Binary files and common generated folders are excluded.

- [Modes and branch controls](.github/skills/repoecho/references/controls.md)
- [Git tracking and repository isolation](.github/skills/repoecho/references/git-tracking.md)
- [Cache configuration, exclusions and freshness](.github/skills/repoecho/references/cache-contract.md)
- [Tests and benchmark results](docs/validation.md)
- [Agent workflow](.github/skills/repoecho/SKILL.md)

Created for **Arvin Ubhi**.
