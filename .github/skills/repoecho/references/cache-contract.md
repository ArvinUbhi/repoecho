# Cache contract

## Storage and two-pass design

`.repoecho/cache.sqlite3` stores a file manifest, compact LLM-authored notes, an FTS5 search index when available, and short-lived capture receipts. It does not store full source files. SQLite transactions and a five-second busy timeout serialize writes; interrupted writes commit completely or roll back. Use a local filesystem, not a shared/network SQLite cache. Each cache is bound to its resolved root path, so copied caches are rejected. Separate worktrees get separate caches. Notes may be reused across branches if their captured evidence is identical.

The program has no provider integration, embeddings, background daemon, API key, network calls, or pip dependencies. Python 3.10+ with `sqlite3` is required. Copilot performs synthesis under its existing permissions. FTS5 uses BM25 ranking over note content, identifiers, tags and evidence paths; a token-overlap fallback works when the Python SQLite build lacks FTS5. CamelCase and snake_case terms are expanded for lexical lookup. This is not semantic embedding search; try component names or synonyms after a miss.

## Freshness

| Field/check | Meaning |
|---|---|
| File SHA-256 | Hash of actual UTF-8 source bytes, including whitespace |
| Scope digest | Hash of sorted relative path + content-hash pairs for matching indexed files |
| Policy fingerprint | Helper version/code, skill instructions/references, effective config and exclusions |
| `captured_at` | When the evidence receipt was produced |
| `generated_at` | When Copilot's note passed evidence validation and was saved |
| `verified_at` | When a retrieved note's evidence passed strict hashing in this invocation |
| `expires_at` | Review deadline; default 30 days, even if hashes match |
| File `checked_at` | Last manifest hash check, not last stat-only inspection |

Every `query` enumerates eligible paths, incrementally updates the manifest, ranks notes, and strictly hashes the candidate notes' sources and scopes. Shared evidence is hashed once per query. Changed/deleted sources, scope additions/removals/edits, changed policy, and expired review times suppress the body. Only ID and reason are returned for stale notes. Timestamps never override a content mismatch.

Warm manifest scans reuse a hash when size, nanosecond mtime/ctime, inode and device match. A full manifest rehash occurs at least every 24 hours (or `scan --full`). Strict query validation does not trust that shortcut. `plan`/`status` are inexpensive manifests, not authoritative freshness reports. A branch name/commit SHA is not the validity key: dirty, staged and untracked-but-not-ignored files all matter.

No filesystem scan is an atomic snapshot of a changing checkout. Reads verify stat signatures before/after and retry racing reads; failures suppress results. Treat results as point-in-time evidence and avoid modifying a checkout concurrently during learning. Capture receipts prevent an old LLM summary from being stamped with new hashes after a source edit. The engine cannot prove an LLM understood the source, chose every semantic dependency, or noticed changes in external services/packages not represented by captured files. Include lockfiles/contracts/configuration and record uncertainties.

## Discovery and exclusions

Git repositories use `git ls-files --cached --others --exclude-standard -z`; tracked files and non-ignored untracked files are considered, including staged/dirty content from disk. Git index-only versions are not substituted. Plain directories use a deterministic walk. Git failures are surfaced; unreadable paths abort rather than certify an incomplete scan. Symlinks and submodule directories are excluded. Index each submodule separately. Selecting a subtree with `--root` never expands the scan to its parent.

Generated/vendor folders (`target`, `build`, `dist`, `node_modules`, `vendor`, `bin`, `obj`, caches and virtual environments), common binary extensions, `.env*`, credential filenames and key/certificate formats are excluded. Remaining files must be UTF-8 without NUL bytes and no larger than 1 MiB by default. Hard exclusions intentionally cannot be disabled; choose another explicit root if a legitimate source tree lives under an excluded directory. UTF-16, other encodings, huge/binary assets, generated artifacts and excluded files are coverage gaps. This is language-neutral text discovery, not a claim to understand every file format.

Path filters are not a general secret detector. Never cache secrets found in otherwise eligible files. Cache summaries may contain proprietary information; keep them local and never force-add the `.repoecho` directory. A generated `.repoecho/.gitignore` excludes its contents without modifying project configuration. Existing tracked cache files, if any, must be untracked manually. Directory/database creation uses restrictive permissions where supported.

## Configuration

Optional root `.repoecho.json`:

```json
{
  "exclude": ["fixtures/private/**", "**/generated/**"],
  "max_file_bytes": 1048576,
  "note_ttl_days": 30,
  "full_verify_hours": 24
}
```

Optional root `.repoechoignore`: one additional exclusion glob per line; blank lines and lines starting with `#` are ignored. Glob syntax is case-sensitive, repository-relative, `/` separated: `*` and `?` match within a path segment; `**` matches zero or more segments; `folder/` means `folder/**`. Bare patterns are root-relative; use `**/name` at any depth. These are **not** Git ignore rules: no negation, leading slash, or escaped comments. Git's own ignore rules are honored by Git discovery. Plain-directory mode does not emulate `.gitignore`; use `.repoechoignore`.

Changing configuration or skill policy invalidates existing notes. The engine skips generated `.repoecho` data regardless of ignore configuration. Capture limits and query `--max-chars` bound evidence/note characters, not exact model tokens or total JSON metadata. Whole notes/files are returned or omitted; no silently truncated note is treated as complete. Query `stale` diagnostics are capped at 20, plan notes/build files at 100. Initial scans hash all eligible files; warm scans still enumerate/stat the tree, so scan cost is O(file count). Avoid global scopes for large monorepos.

## Recovery and deletion

`forget ID` removes a note from the current cache and search index, not forensic remnants in SQLite/WAL/backups. Back up and delete the generated cache to rebuild after corruption, an incompatible schema, or moving the checkout. Do not edit tables manually to bypass failed validation. SQLite errors produce a nonzero exit and no cached answer. A missing cache can always be rebuilt from source and new Copilot notes.
