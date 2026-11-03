# Validation

Recorded on 2 November 2026. All 71 tests passed locally on Linux with Python 3.12.14; this is not a claim of a live GitHub Copilot CLI run. Copilot CLI was not installed in the build environment. Real gh 2.103.3 + uv 0.13.4 integration was exercised in isolated temporary home/config directories, including installation, alias updates, paths with apostrophes/spaces, argument forwarding and the installed benchmark. Format, installation locations and slash commands were checked against GitHub's official documentation linked in the README.

## Behavioral checks

Run `python3 -m unittest discover -s tests -v` from the repository root. The suite covers:

- Cold indexing, warm stat reuse, forced/periodic full hashing and session persistence.
- Same-size edits with restored mtime, and strict query validation even with an outdated manifest hash and matching stat signature.
- Source edits/deletion/renaming, new scope members, empty-to-populated scopes, uncaptured scope changes and new Maven modules.
- Shared build-file invalidation while unrelated edits preserve focused notes.
- Capture-to-save races, one-use receipts, receipt expiry, review TTL, policy/configuration invalidation and replacement by stable note ID.
- Whole-note/evidence budgets, unknown-note-field rejection, stale-body withholding and candidate-only status output.
- Git ignored/untracked/staged/dirty files, branch changes and reversion, bounded subtree discovery and automatic cache exclusion from normal Git status.
- Java, Gradle, Maven, Python, JavaScript, Rust, Go and Unicode path discovery.
- Binary/secret-path/generated/large-file exclusions, custom glob behavior, symlink and traversal rejection, root identity and corrupt-cache failure.
- FTS and fallback search, concurrent CLI processes, note deletion and absence of source blobs from storage.
- Complete personal/project installation and overwrite protection.
- uv isolation from incompatible project dependencies/Python pins; gh alias conflict protection and idempotent updates; rollback after alias failure; human/JSON controls; nested worktree-root discovery; benchmark isolation from exported Git paths.
- Windows path-stat versus descriptor-stat timestamp differences, while still rejecting metadata changes during a read. See [CPython issue 157671](https://github.com/python/cpython/issues/157671).
- Independent skill/cache/branch controls, precedence, off-mode database bypass, atomic concurrent settings updates and resume-after-change validation.
- Git status and staged/unstaged diffs, branch transition diffs, missing-history fallback, retained note revisions, history bounds, and cache isolation across repositories and linked worktrees.
- A benchmark smoke test covering warm retrieval, invalidation and disabled modes.

The CI workflow declares Python 3.10 and 3.13 on Linux, macOS and Windows. A declared matrix is not evidence of successful remote runs; consult GitHub Actions for actual results. Symlink tests skip when the platform does not permit creating symlinks.

## Independent Java walkthrough

A separate agent used only the skill and a fresh synthetic Maven multi-module repository to explain shutdown, the Java compatibility target and available tests. It read applicable repository instructions, captured evidence, saved focused `build-and-test` and `process-lifecycle` notes, and retrieved both with strict verification of five evidence files. Its explanation correctly distinguished configured Java 8 source/target settings from an unverified runtime JDK and reported that no automated tests were supplied. Application source was unchanged.

This demonstrates the agent-facing workflow on a controlled fixture. It does not establish accuracy for arbitrary repositories or replace testing in the user's Copilot CLI installation.

## Reproducible benchmark

```sh
python3 tools/benchmark.py --files 2000 --notes 20 --runs 5
```

Observed sample on the build host, using a Git repository with 2,000 synthetic UTF-8 Java files (about 3.6 KB each), 20 compact notes and three source dependencies per note:

| Measurement | Observed |
|---|---:|
| Cold scan CLI | 546.28 ms |
| Synthetic learning setup, 20 notes | 4,775.06 ms |
| Median warm query CLI, 5 runs | 203.14 ms |
| Sample p95 warm query CLI | 216.81 ms |
| Median skill-off query CLI | 57.14 ms |
| Median cache-off query CLI | 57.15 ms |
| Median branch-off query CLI | 53.04 ms |
| Changed-source query CLI | 187.55 ms |
| Manifest files rehashed on warm query | 0 |
| Evidence files independently verified | 3 |
| Note payload returned | 1,122 characters |
| Return-to-main query | 236.68 ms |
| Original revision reused after branch return | yes |

Wall times depend on CPU/filesystem/cache warmth and can vary between consecutive samples. CLI timings exclude the outer gh/uv launch and include helper interpreter startup, Git operations, enumeration, stat checks, lookup and strict evidence verification. Synthetic learning setup exercises capture/remember with fabricated benchmark notes and excludes LLM synthesis. Provider latency and Copilot context overhead are not measured. Twenty notes are not a large-index ranking benchmark; use `--notes` to scale it and `--plain` for non-Git mode. Sample p95 is not an SLA. No token-savings percentage or Copilot speedup is claimed. Run the tool on representative repository/storage sizes before setting performance expectations.

## Command usability walkthrough

An independent agent used the bundled CLI in a disposable Java Git repository, enabled main-only caching, verified state from a nested source directory, switched to a disabled feature branch, confirmed query bypass, ran the synthetic benchmark and returned to main. Root discovery and branch controls behaved correctly, with a clean final Git status. Its feedback identified an ambiguous global-options instruction; the skill now explicitly says benchmark already emits JSON and does not accept repository-root options.

## Natural-language retrieval and compact agent output

The alias and compact-output update passed 74 unit tests (one optional integration test skipped). Added coverage checks aliases in both FTS and lexical fallback, session persistence, alias validation, revision reuse, stale-evidence rejection, compact knowledge/caveat preservation and output budgets.

A local synthetic Git benchmark (`python tools/benchmark.py --files 200 --notes 20 --runs 3`) returned the same note IDs with 2,941 full JSON characters versus 551 compact characters: 81.26% less serialized output. Warm query median was 83.97 ms. These are one-run fixture measurements, not guaranteed production results or model token/AIC savings. Full output uses its normal pretty formatting; compact uses compact JSON. Repeat in Copilot with the same model, question and repository in fresh sessions to measure actual model usage and answer quality.
