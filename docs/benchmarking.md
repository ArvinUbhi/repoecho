# Benchmark RepoEcho for your team

Use two different measurements: **helper speed/correctness** and **real Copilot session cost**. Faster retrieval does not by itself prove fewer model tokens or better answers.

## Read the published reports

Open [GitHub Actions → Benchmarks](https://github.com/ArvinUbhi/repoecho/actions/workflows/benchmarks.yml), select a run, and read its job summaries. Download the OS-specific artifacts for:

- `report.md` and `report.html`: readable timings, storage and baseline comparisons.
- `report.json`: raw samples, environment, engine SHA-256 identities, context estimates and checks.
- `samples.csv`: one row per measured command for your own charts.
- `provenance.json`: exact candidate/baseline Git commits and workflow run.
- `failure.json`: a failed correctness check; this is not a successful benchmark.

Reports run on Windows, macOS and Linux for every main push and pull request. A weekly run exercises the large profile. Use **Run workflow** to select smoke, team or large and an approved baseline commit. Artifacts are retained for 90 days; archive approved results internally for longer retention. Reports are public because this repository is public. CI generates synthetic fixtures only and uploads no application source or caches.

The default baseline is the tested 1.6.0 release commit, `cfeb48008c78e42190ae31e6fe1c971b6a28ae17`. Both versions run with the same current benchmark harness on the same runner. Initial comparisons against an unchanged engine establish noise; they are not a claim of improvement.

## Run locally with one command

Download the latest RepoEcho source ZIP and extract it, or use a checkout. From its root:

```powershell
uv run --no-project --python 3.12 tools/benchmark_suite.py --profile team --runs 10 --trials 2
```

Requires Git and Python (provided by uv). No npm, gh, model account or third-party Python packages are needed. Results appear in `benchmark-results/`. The suite creates and removes temporary synthetic repositories; it never benchmarks or changes your application checkout.

| Profile | Files per fixture | Notes per fixture | Use |
|---|---|---|---|
| smoke | 100 | 5 | CI correctness and quick installation checks |
| team | 1,000 and 5,000 | 20 and 100 | Representative team rollout comparison |
| large | 1,000, 5,000 and 20,000 | 20, 100 and 200 | Scaling and weekly checks |

Every profile tests both Git and plain directories, with mixed Java/Python/TypeScript/XML file extensions and deterministic padded UTF-8 text. This measures indexing/retrieval, not language parsing. Each trial creates fresh fixtures. Ten samples and two trials are a useful starting point; use more samples on a controlled workstation for a release decision.

To compare two downloaded versions, point the current harness at the older engine:

```powershell
uv run --no-project --python 3.12 tools/benchmark_suite.py --profile team --runs 20 --trials 2 --baseline-helper "C:\bench\previous\repoecho\.github\skills\repoecho\scripts\repoecho.py"
```

Baseline engines must implement the 1.6.0 CLI/storage contract. Incompatible versions fail explicitly rather than silently skipping checks. Only use trusted engine files: benchmarking executes them. Trials alternate candidate/baseline order to reduce ordering bias. Do not compare a laptop run directly with a different CI machine and call the difference a release regression.

For an existing installation's shorter smoke benchmark, `repoecho benchmark --files 2000 --notes 20 --runs 5` remains available. The extensive suite is repository tooling and does not require a new npm release.

## What is checked and timed

- Empty-cache scan, warm scan and forced full hashing; synthetic learning setup is reported separately.
- Warm full/compact retrieval, misses, output budgets and four simultaneous CLI readers.
- Skill/cache/branch disabled paths.
- Dirty, staged, renamed and deleted evidence; restoration of original evidence.
- Unrelated edits that should leave the note valid.
- A new untracked file matching a captured scope, which must invalidate membership-sensitive knowledge.
- Unchanged branches, changed branch evidence, and return to both main and feature revisions.
- Separate repository and linked-worktree isolation.
- Database allocation before/after, revision counts and no duplicate writes on branch return.

Every measured sample must satisfy its correctness check. Stale content, isolation failures, budget failures and revision duplication fail the job. Regression reports flag a median slowdown only when it exceeds **both 25% and 10 ms**. Shared-runner timing flags are advisory by default; use `--fail-on-regression` on a controlled machine to make them blocking. Thresholds can be set with `--regression-percent` and `--regression-ms`.

The reports retain all samples and show median, nearest-rank p95, min/max and response bytes. Cold scan is one observation per fresh fixture/trial. p95 from a small sample is not a service-level guarantee. No OS page-cache flushing occurs. CLI timings include Python startup and Git but exclude uv/npm startup, Copilot, model latency and human work. Four readers represent overlap inside one checkout, not a central server with 100 users. Team caches are local to each user's checkout.

Context estimates in JSON use the engine's hypothetical captured-source-versus-note calculation. They are **not actual tokens saved**, do not account for all agent calls, and must not be used as billing claims. Reports contain no claim that identical file hashes prove an LLM summary is correct.

## Measure actual Copilot savings

Copy `benchmarks/study-template.csv` to `benchmark-results/study.csv`. For each task/trial/model record an `off` session and a `warm` session, with optional `cold` learning session:

1. Fix the repository commit, model, instructions, task and answer-quality rubric. Keep task identifiers anonymous; do not store prompts or code in the CSV.
2. Start a fresh Copilot session for each condition. Explicitly bypass RepoEcho for `off`, and start from a prepared verified cache for `warm`. Use a separate disposable clone for `cold`; do not delete your working cache.
3. Randomize condition order across tasks; keep model parameters and available tools consistent. Include related-query retrieval, edits, branch changes and cache misses, not only easy repeated questions.
4. Record **total measured input/output tokens for the whole task**, including cache operations, learning and refresh calls. Record total duration in milliseconds and `correct` as `yes` or `no`, ideally from blind review against the same rubric.
5. If the client does not expose actual token counts, do not invent them or translate AIC to tokens. Keep AIC as a separate study until its unit and measurement are documented.
6. Repeat across representative Java repositories and developers. Check whether incorrect or incomplete answers increase. Review cold learning cost as well as warm savings.

```powershell
uv run --no-project --python 3.12 tools/benchmark_study.py benchmark-results/study.csv
```

The tool validates paired rows, preserves negative savings, excludes failed-quality pairs from aggregate savings (while listing them), and reports cold-learning break-even repeat uses when cold data is present. It aggregates user-supplied measurements; it does not instrument Copilot. Do not aggregate different model prices into a monetary saving. Keep private study data local; it is not uploaded by the benchmark workflow.

For the 100-person rollout, start with 5 developers and representative repos, then 20, then 100. Set acceptance thresholds from those observed baselines. Synthetic CI success is a necessary regression check, not proof of corporate proxy compatibility, enterprise filesystem performance or real LLM savings.
