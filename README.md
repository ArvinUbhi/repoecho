# RepoEcho

**Help GitHub Copilot CLI remember your codebase between sessions.**

RepoEcho saves concise notes about your repository so Copilot can reuse what it has already learned. Before using a note, it checks the source files for changes. Missing or outdated knowledge is learned again when needed.

The aim is less repeated exploration and more focused context for your task. It works with text-based repositories across languages, with extra guidance for Java, Maven and Gradle.

## Install once

You need **GitHub Copilot CLI**, [GitHub CLI (`gh`)](https://cli.github.com/), [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git. On Windows, use PowerShell with Git for Windows installed; it supplies the shell needed by the `gh` command.

```sh
gh repo clone ArvinUbhi/repoecho
uv run --no-project --python '>=3.10' repoecho/tools/install.py --gh
```

uv finds a compatible Python and downloads it if needed. Setup installs the skill and registers `gh repoecho`. No extra API key or Python packages are required. You can remove the downloaded checkout afterwards.

Already installed? Add `--replace` to the second command.

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

## Everyday controls

Run these in your terminal from anywhere inside the target Git repository:

| Command | What it does |
|---|---|
| `gh repoecho status` | Show whether RepoEcho is active and why |
| `gh repoecho on` / `gh repoecho off` | Enable or disable RepoEcho for this repository |
| `gh repoecho cache on` / `gh repoecho cache off` | Enable or disable saved knowledge use |
| `gh repoecho branch only` | Use caching only on the current branch |
| `gh repoecho branch all` | Allow caching on every branch |
| `gh repoecho branch off` / `gh repoecho branch on` | Disable or enable caching on the current branch |
| `gh repoecho doctor` | Check your setup and show tool locations |
| `gh repoecho --help` | Show command help |

The skill, cache and branch settings must all be on for caching to work. For example, `gh repoecho on` leaves a separately disabled cache off. Turning caching off keeps saved notes for later reuse. Use `status` to see the effective state without scanning your code.

You can also ask Copilot: **“Use /repoecho to turn caching off”** or **“Use /repoecho only on this branch.”**

## Branches and multiple repositories

RepoEcho checks Git branch, status and diffs, then validates source hashes before returning notes. Uncommitted edits count as changes too. When you switch back to a branch, matching saved knowledge can be reused while it remains valid.

Each repository and linked worktree has its own local cache and settings. They are never mixed. Generated notes stay in the repository's ignored `.repoecho/` directory; do not copy or commit that directory.

To select a repository explicitly:

```sh
gh repoecho --root /path/to/your-app status
```

For non-Git directories, run commands from the same root directory each time or use `--root`.

## Run a benchmark

```sh
gh repoecho benchmark --files 2000 --notes 20 --runs 5
```

This creates a temporary sample repository and measures initial indexing, warm retrieval, change detection and reuse after switching branches. It leaves your repository and cache untouched.

Increase `--files` or `--notes` to test larger workloads. Save results for comparison by adding `> benchmark.json` to the command. These measurements cover the local cache helper; they do **not** measure Copilot thinking time or prove a particular LLM speedup.

## Update or troubleshoot

From the directory containing your downloaded `repoecho` checkout:

```sh
git -C repoecho pull --ff-only
uv run --no-project --python '>=3.10' repoecho/tools/install.py --gh --replace
```

If you removed the checkout, clone it again first. Run `/skills reload` in Copilot after updating.

- **Command unavailable?** Check that `gh` and `uv` are on your PATH, then rerun setup.
- **Caching unexpectedly off?** Run `gh repoecho status` to identify the disabled setting.
- **Copilot cannot see the skill?** Run `/skills info repoecho` after reloading.
- **Need project/team installation, offline use or alias repair?** See the [setup guide](.github/skills/repoecho/references/setup.md).

## More detail

RepoEcho checks whether saved evidence has changed; it cannot guarantee that every saved interpretation is correct. Copilot should still read relevant code before editing. Binary files and common generated folders are excluded.

- [Modes and branch controls](.github/skills/repoecho/references/controls.md)
- [Git tracking and repository isolation](.github/skills/repoecho/references/git-tracking.md)
- [Cache configuration, exclusions and freshness](.github/skills/repoecho/references/cache-contract.md)
- [Tests and benchmark results](docs/validation.md)
- [Agent workflow](.github/skills/repoecho/SKILL.md)

Created for **Arvin Ubhi**.
