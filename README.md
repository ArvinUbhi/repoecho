# RepoEcho

**Help GitHub Copilot CLI remember your codebase between sessions.**

RepoEcho saves concise notes about your repository so Copilot can reuse what it has already learned. Before using a note, it checks the source files for changes. Missing or outdated knowledge is learned again when needed.

The aim is less repeated exploration and more focused context for your task. It works with text-based repositories across languages, with extra guidance for Java, Maven and Gradle.

## 1. Install once

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

## 2. Open your application repository

Open Copilot CLI in the repository you want to work on. Run:

```text
/skills reload
```

Then ask:

```text
Use /repoecho to learn this repository's architecture, build and main modules.
```

You can also use it for a specific task:

```text
Use /repoecho to find the shutdown code and help me change it.
```

Copilot retrieves relevant notes, checks that their sources still match, and learns anything missing before continuing. You do not need to write or manage notes yourself. Follow step 3 to make this your default workflow.

## 3. Make it automatic

Add this section to **`AGENTS.md` at the root of your application repository** if you already use that file. Otherwise, put it in **`.github/copilot-instructions.md` in that repository**. Create the file if needed, and preserve existing instructions. Choose one file; you do not need both.

For example: `C:\work\my-app\AGENTS.md`. Do not put it in the downloaded RepoEcho checkout or the installed skill folder.

```markdown
## RepoEcho

Use the installed repoecho skill by default for repository questions,
planning, debugging and code changes. Follow its SKILL.md workflow.
Run its repoecho_cli.py through uv with Python 3.12 and an explicit
--root pointing to this repository. No gh or system Python is required.

Use the script for cache queries, source capture, validation, saves and
mode controls. Let it check Git branches, status, diffs and source hashes.
Reuse only content_verified notes. Query again after switching branches.
Respect disabled skill, cache and branch settings; never enable them
without being asked. Learn missing or stale knowledge from current source
and save it through the script. As work progresses, save useful new
source-backed findings at meaningful milestones without waiting to be
asked. Verify saved notes, avoid rewriting unchanged notes, and refresh
relevant notes after edits. Do not read or edit the raw cache database.

Infer the intent of my normal request; do not require workflow names or
note IDs. Use query --compact with my terms plus relevant equivalents. If needed, reformulate
once before investigating source. Save useful alternative phrases in note
aliases so later related requests can find the same knowledge.
Prefer workflow-specific notes and improve them when follow-ups reveal
missing steps or dependencies. A query already validates the cache; avoid
redundant status/inspect/scan calls. Answer explanations directly from
sufficient verified notes; read source when details are missing or unclear.
Keep cache reporting to one short line.
Read current repository instructions and relevant code before editing.
If the helper fails, report it and work from source. When useful, report
which note IDs were reused or refreshed.
```

For more explicit capture, refresh and failure-handling rules, use the [full copyable instructions](docs/copilot-instructions-snippet.md) instead. For a personal default across repositories, put the section in `$HOME/.copilot/copilot-instructions.md` instead of a repository file.

**After adding or editing instructions, start a fresh Copilot session.** Changes are not loaded immediately into an active session:

```text
/new
/instructions
```

Alternatively, exit Copilot and run `copilot --continue` from your application repository. In `/instructions`, confirm your chosen file is discovered and enabled. **`/skills reload` reloads skills; it does not replace this instruction refresh step.** Saved RepoEcho notes remain available across sessions.

Now ask normally: **“Explain the shutdown workflow.”** You should not need to keep saying “use RepoEcho”. These instructions guide Copilot; they are not an enforced execution hook.

### Check that it is reusing your workflow

In a fresh session, ask:

```text
Explain the workflow we saved for [workflow name]. Report the RepoEcho
note IDs and freshness returned by the script, and learn anything missing.
```

Look for a relevant saved note marked `content_verified`. A successful capture alone does not save a note; the skill must also save it with `remember`. If no valid note exists, Copilot should read the source and refresh its knowledge.

## Ask naturally — no workflow names to remember

Ask **“What happens when I stop a running job?”** or **“How does process termination work?”** Copilot translates the request into relevant search terms and checks whether the returned notes answer it. You do not need to know that a saved note is called `workflow-shutdown`.

As it learns, Copilot saves short alternative phrases alongside each note. Related wording can then find the same source-verified knowledge. If the first search is insufficient, it can reformulate once before investigating source and improving the note for next time. It will not assume two operations are equivalent just because their names sound related.

Agents use `query --compact` to receive verified notes, caveats and source paths without the full hash manifests and scan diagnostics. Validation still runs before anything is returned. The full query output remains available for troubleshooting.

Intent interpretation happens in Copilot; the Python helper searches locally without another model/API call or an embedding service. This improves discovery but does not guarantee every paraphrase will match. Existing notes remain valid and gain aliases as they are revisited—no cache reset is required.

## It learns as you work

You do not need to ask it to "remember" every discovery. With RepoEcho in use and caching enabled, Copilot saves useful findings as it investigates workflows, understands components and completes changes. It captures the relevant source, writes a concise note through the helper, and checks that the saved note can be retrieved.

For example, investigating a Java shutdown workflow can add a workflow note; later discovering its configuration dependency can update that same note. Unchanged notes are reused rather than saved again. Learning happens at useful milestones, so it does not require indexing the entire application first or writing after every file read.

Notes focus on individual workflows: their trigger, steps, relevant classes, configuration and failure paths. As follow-up questions reveal missing details, Copilot improves the same note using fresh source evidence. This makes later questions easier to answer without repeating the investigation.

For explanations, sufficient verified notes can provide the answer directly. Copilot still opens source for gaps or ambiguity and always reads current relevant code before edits. The initial query already checks settings and freshness, so routine status/inspect/scan calls and duplicate queries are unnecessary. Cache reporting stays within one short line unless you request diagnostics.

The cache grows through the work you actually do. It is not a background process and does not learn while Copilot is idle. Disabled skill, cache or branch settings stop cache reads and writes. A capture or scan alone is not a saved knowledge note.

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

RepoEcho stores focused, source-linked notes rather than copying your entire repository into each branch's cache. On a large repository, Copilot first queries relevant notes and reads additional source only when the saved knowledge is missing or insufficient. Generated folders and binary files are excluded; selecting focused files and scopes keeps the retrieved context small.

The script uses Git branch, status and diffs to identify changes, then validates candidate notes against source hashes and scope evidence. Uncommitted changes count too. Git helps narrow the work; a clean Git status alone is not proof that a note is valid.

**Branch names do not determine whether a note can be reused. Its source evidence does.** Within the same checkout:

| What happens | What RepoEcho does |
|---|---|
| Learn a workflow on `main` | Save a note with a content-addressed evidence revision. |
| Switch to `feature` with that workflow's files and scope unchanged | Reuse the same revision after validation. No separate copy is needed just because the branch name changed. |
| Change unrelated files on `feature` | Keep reusing the workflow note if all of its evidence still matches. |
| Change files or scope that the note depends on | Treat that revision as stale; Copilot reads the changed evidence and saves a refreshed revision when needed. |
| Return to `main` | Reuse the earlier matching revision if it is still retained and within its review lifetime. |

Different revisions of a note coexist, so learning a changed workflow on one branch does not simply overwrite the version learned on another. By default, up to **eight revisions per note** are retained and notes have a **30-day review lifetime**. Expired or evicted knowledge may need relearning. Reuse also depends on capturing adequate evidence: a note cannot detect dependencies its author omitted.

This avoids repeating the same learning and storage for every branch. Validation still costs file reads/hashing, and broad evidence scopes cost more than focused ones; it does not promise constant-time retrieval for every repository size.

**Separate repositories and linked worktrees have independent caches and settings.** Cross-branch reuse applies when switching branches within the same checkout, not across separate worktree directories. Generated notes stay in that root's ignored `.repoecho/` directory. Do not copy or commit it. Branch-specific controls can disable caching even when a matching revision exists.

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

Increase `--files` or `--notes` to test larger workloads. Save results for comparison by adding `> benchmark.json` to the command. The `retrieval_output` section compares full and compact JSON character counts for the same retrieved note IDs. This measures actual output size, not model token counts. These measurements cover the local cache helper; they do **not** measure Copilot thinking time or prove a particular LLM speedup.

## Measure real Copilot usage

The built-in benchmark measures local helper time and output size. To measure **your actual AIC**, use the study sheet included with your downloaded RepoEcho checkout. In PowerShell, from the folder containing `tools`, run:

```powershell
uv run --no-project --python 3.12 .\tools\usage_study.py init .\usage-study.csv
```

Replace the five example questions in the CSV with questions about your Java application. For each question, run a **fresh Copilot session** (`/new`) with the same model and unchanged repository/commit. Record three modes: `off` (turn caching off and confirm it), `cold` (caching on, no relevant note yet), and `warm` (caching on, relevant note already learned). A repository that already has a relevant note cannot provide a genuine cold run for that question; use another new workflow rather than deleting your useful cache. Turn caching back on when done.

Enter AIC as Copilot displays it, elapsed seconds, number of RepoEcho helper calls, and `correct` as `yes` or `no`. Copy the model name and commit SHA consistently for matched runs. The CSV stays local and is not sent anywhere. Summarize completed matches with:

```powershell
uv run --no-project --python 3.12 .\tools\usage_study.py report .\usage-study.csv
```

This reports matched AIC differences, latency, helper calls and answer correctness. It cannot automatically read Copilot's AIC; you enter it from each session. Single runs vary, so repeat questions before drawing conclusions.

A separate retrieval check uses synthetic notes to test whether ordinary questions find the right workflow and whether changed source prevents stale reuse:

```powershell
uv run --no-project --python 3.12 .\tools\retrieval_eval.py
```

## Update to the latest version

**No `gh` or system Python needed. Your repository's saved notes and cache settings stay in place.** Updating the installed skill does not automatically update your `AGENTS.md` or Copilot instruction file.

### Windows: ZIP installation

1. Close Copilot before replacing the installed skill, to avoid folder-lock errors.
2. [Download the latest ZIP](https://github.com/ArvinUbhi/repoecho/archive/refs/heads/main.zip) and extract it into a **fresh folder**. Open the extracted `repoecho-main` folder containing `tools` and `README.md`.
3. Open PowerShell in that folder (type `powershell` in File Explorer's address bar), then paste:

```powershell
uv run --no-project --python 3.12 .\tools\install.py --replace
```

Wait for **Installed RepoEcho at ...**. Running an old downloaded copy only reinstalls that old version—download the latest ZIP first.

### Git installation

Open a terminal **inside your RepoEcho checkout**, then run:

```sh
git pull --ff-only
uv run --no-project --python 3.12 tools/install.py --replace
```

These commands update the RepoEcho checkout, not your Java/application repository. ZIP downloads cannot use `git pull`.

For a project-local installation, add `--project "C:\path\to\your-app"` to the install command. Use the same installation location as before. Add `--gh` only if you already use the optional GitHub CLI integration and have its prerequisites installed.

### Load the update in Copilot

Open Copilot in **your application repository**, then run:

```text
/skills reload
/skills info repoecho
```

If you use the automatic instructions from this README, replace **only the RepoEcho section** in your chosen `AGENTS.md` or `.github/copilot-instructions.md` with the [current instructions above](#3-make-it-automatic). Preserve your other instructions. Then run:

```text
/new
/instructions
```

Check that your instruction file is discovered and enabled. `/skills reload` reloads the installed skill; `/new` loads changes to standing instructions. Neither step clears your saved notes.

Finally, ask:

```text
Use /repoecho to show its effective status, then retrieve a saved note
for this repository and report its note ID and freshness.
```

If caching is off, that should be reported rather than silently enabled. If no valid note exists, ask Copilot to learn a relevant workflow.

## Troubleshooting

- **Python fails to start?** Run `uv python install 3.12`, then `uv run --python 3.12 python --version` before retrying setup.
- **Access denied when replacing the skill?** Close Copilot sessions and retry. A folder lock or permissions may prevent replacement. For a project-local installation, use `--project "C:\path\to\your-app"` instead.
- **Caching unexpectedly off?** Ask Copilot for RepoEcho status or run the direct `status` command above.
- **Only AGENTS.md appears in `/instructions`?** You can put the section there. If using `.github/copilot-instructions.md`, check the exact filename (not `.md.txt`) and that it is in your application repository, then run `/new` and `/instructions`.
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
