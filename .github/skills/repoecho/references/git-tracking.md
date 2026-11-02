# Git tracking and isolation

The helper uses local Git commands in the background. It does not fetch, push, switch branches, change Git configuration, or execute repository hooks/builds during indexing.

| Git information | Use |
|---|---|
| `symbolic-ref --short HEAD` | Resolve the current branch and its mode override |
| `rev-parse --verify HEAD` | Record the current commit and compare with the previous scan |
| `status --porcelain=v1 -z` | Track staged/unstaged/untracked state, including filenames with spaces |
| `diff --cached --name-only -z` | Identify staged changes |
| `diff --name-only -z` | Identify unstaged changes |
| `diff PREVIOUS_HEAD CURRENT_HEAD --name-only -z` | Track changed paths across commits and branch transitions |
| `ls-files --cached --others --exclude-standard -z` | Discover tracked and non-ignored untracked paths |

Diff commands disable external diff programs and text conversion. File-status transitions and changes between scanned commits force affected files to be rehashed. Repeated unchanged dirty/untracked files can still reuse manifest hashes when their stat signatures match. Candidate knowledge evidence is always independently hashed before retrieval. Git is an optimization and a diagnostic source, not proof that the working tree is clean or a replacement for hashing.

If a previous commit is no longer available (rewritten/pruned history, for example), record `history_complete: false` and perform a full content scan. No network retrieval is attempted. Unborn branches work without a HEAD commit. Detached HEAD has a commit but no named branch. Non-Git trees retain filesystem-based scanning and hashing.

Each note has a stable logical ID and a content-addressed `revision` derived from policy, source hashes and scope digests. Distinct revisions of the same logical note coexist. Learning on a feature branch therefore does not overwrite the main branch's evidence version. On return, reuse an earlier revision only if its evidence still matches and review TTL remains valid. Return at most one fresh revision per logical ID. At most eight revisions per ID are retained by default (`max_note_versions`); older revisions may require relearning after eviction. `forget ID` removes all retained revisions for that logical ID.

Capture provenance records the originating branch, commit and repository ID; it does not make branch names validity keys. Two branches with identical evidence can share a revision. Notes still depend on the learner selecting adequate source/scope evidence. A branch change alone does not invalidate unrelated knowledge.

Caches are **local to the exact resolved `--root`**, with one SQLite database per root. The database records that root and refuses a cache copied to another location. A repository ID derived from the root appears in output and capture provenance. Different repositories with identical filenames/note IDs never share an index. Linked worktrees have different root paths and independent caches and mode settings even when they share a Git common directory. Always pass the same root for a repository, and never point multiple repositories at one shared cache. Moving a checkout requires rebuilding its local cache.

Git summaries cap returned path lists at 100 while retaining full counts. Internal status/diff hints are not capped. Cache files are ignored and excluded from source indexing. Submodule contents remain separate roots; their working-tree dirtiness is not recursively indexed.
