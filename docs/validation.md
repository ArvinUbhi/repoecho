# Validation

Recorded on 2 November 2026. All 43 tests passed locally on Linux with Python 3.12.14; this is not a claim of a live GitHub Copilot CLI run. Copilot CLI was not installed in the build environment. Format, installation locations and slash commands were checked against GitHub's official documentation linked in the README.

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
- Windows path-stat versus descriptor-stat timestamp differences, while still rejecting metadata changes during a read. See [CPython issue 157671](https://github.com/python/cpython/issues/157671).

The CI workflow declares Python 3.10 and 3.13 on Linux, macOS and Windows. A declared matrix is not evidence of successful remote runs; consult GitHub Actions for actual results. Symlink tests skip when the platform does not permit creating symlinks.

## Independent Java walkthrough

A separate agent used only the skill and a fresh synthetic Maven multi-module repository to explain shutdown, the Java compatibility target and available tests. It read applicable repository instructions, captured evidence, saved focused `build-and-test` and `process-lifecycle` notes, and retrieved both with strict verification of five evidence files. Its explanation correctly distinguished configured Java 8 source/target settings from an unverified runtime JDK and reported that no automated tests were supplied. Application source was unchanged.

This demonstrates the agent-facing workflow on a controlled fixture. It does not establish accuracy for arbitrary repositories or replace testing in the user's Copilot CLI installation.

## Reproducible benchmark

```sh
python3 tools/benchmark.py --files 2000 --runs 5
```

Observed sample on the build host, using a plain directory with 2,000 synthetic UTF-8 Java files (about 3.6 KB each), one compact note and three source dependencies:

| Measurement | Observed |
|---|---:|
| Cold manifest scan | 779.24 ms |
| Median warm manifest scan, 5 runs | 190.68 ms |
| Median warm query, 5 runs | 185.62 ms |
| Manifest files rehashed on warm query | 0 |
| Evidence files independently verified | 3 |
| Note payload returned | 853 characters |

Wall times depend on CPU/filesystem/cache warmth and can vary between consecutive samples. The query includes enumeration, stat checks, lookup and strict evidence verification. It excludes Python process startup, provider latency, LLM synthesis and Copilot context overhead. A single note is not a large-index ranking benchmark. No token-savings percentage or Copilot speedup is claimed. Run this tool on representative repository/storage sizes before setting performance expectations.
