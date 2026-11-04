# Roll out RepoEcho to your team

RepoEcho runs locally for each developer. A 100-person rollout does not mean 100 clients sharing one database. Each repository checkout and linked worktree has its own `.repoecho` directory, containing hashes, notes and local controls. Share the skill and repository instructions; keep caches separate.

## Audit findings and fixes in 1.4.0

| Finding | Impact before the fix | Current behaviour |
|---|---|---|
| Operational settings were part of every note's policy | Changing scan frequency, retention or future note lifetime made all knowledge stale | Those settings preserve notes and existing expiry dates; exclusions/size changes affect only evidence that no longer validates |
| Exported Git variables could override `git -C` | Branch/status/discovery could describe another checkout | RepoEcho removes inherited `GIT_*` overrides from its Git subprocesses |
| Missing Git triggered filesystem fallback inside a checkout | Git-ignored paths could be indexed; branch controls were unavailable | Git checkouts fail with an actionable error; genuine plain directories still work |
| Installers had no shared lock and used one launcher temporary name | Simultaneous replacements could race or roll back another install | A per-installation lock serializes replacement; launcher staging uses unique files |
| Updater downgrade check happened before installation | Overlapping downloaded versions could install out of order | Installer repeats the check inside its lock |
| Default updates followed moving `main` | Developers could install different builds | Optional full-commit pinning and approved ZIP checksums support controlled distribution |
| ZIP extraction had no resource limits | Oversized or malformed archives could consume disk before install | Download, expansion and entry limits; unsafe/duplicate paths rejected |

The previous 1.3.3 fix also removed release/code/documentation changes from cache invalidation. Both pre-1.3.3 and 1.3.3 notes are adopted after strict evidence verification, without extending their review deadlines.

## Recommended installation

1. Choose a tested commit and have a small pilot approve it. Distribute that build or ZIP through your normal internal channel. The team can calculate a ZIP checksum with `Get-FileHash -Algorithm SHA256 .\repoecho-approved.zip`; distribute the expected hash separately through a trusted channel.
2. Install one personal skill per developer using the README ZIP instructions. Git, uv and Copilot CLI must be available; gh is optional. Work proxies may require an IT-provided CA PEM and `HTTPS_PROXY` in the calling PowerShell environment.
3. Put the section from [copilot-instructions-snippet.md](copilot-instructions-snippet.md) in each application's `AGENTS.md` or `.github/copilot-instructions.md`. Commit that instruction section through the application's normal review process. Use one authoritative section, avoiding conflicting duplicates.
4. Reopen the terminal after installation, run `repoecho --version` and `repoecho doctor` from each checkout, then `/skills reload` in Copilot. Use `/new` after changing standing repository instructions. Check `/instructions` and `/skills info repoecho` to confirm what the agent loaded.
5. Keep caches on local disk. Do not use a shared drive, roaming cache or OneDrive-synchronised `.repoecho`. Do not copy, commit or distribute the cache with your repository. Moving a checkout with its cache intentionally requires rebuilding at its new location.

Avoid installing both personal and project copies without a deliberate version policy: Copilot may load a different copy from the one your PATH command invokes. `repoecho doctor` prints the command's skill path; compare it with `/skills info repoecho`. Project installs do not change personal PATH. Updating a personal install does not update a repository's committed skill or instructions.

For existing 1.4.0+ installations:

```powershell
repoecho update --ref YOUR_APPROVED_FULL_COMMIT_SHA
# Or use an internally distributed ZIP:
repoecho update --zip "C:\Downloads\repoecho-approved.zip" --sha256 YOUR_APPROVED_SHA256
```

Add `--ca-cert "C:\certs\corporate-root.pem"` to the network update when required. Older updaters do not know the new flags: use their existing `--zip` option once, or run the trusted new checkout's installer with `--replace`. Close active Copilot sessions before replacing the skill on Windows.

## Pilot: 5, then 20, then 100 developers

Start with five people covering Windows, the work proxy, your large Java/Maven repository, another language, and linked Git worktrees. Expand to twenty after the following checks pass; expand to one hundred after a representative working week with acceptable latency and no unresolved freshness or isolation failures.

| Check | Evidence to record |
|---|---|
| Learn and reuse a workflow in a fresh Copilot session | Correct note ID, `content_verified`, source references and an accurate answer |
| Edit, stage, rename or delete captured evidence | Old note body withheld; learning refreshes only affected notes |
| Add a file covered by a note's scope | Note withheld until refreshed |
| Switch main → feature → main with different versions of a file | Correct revision on each branch, original revision reused on return |
| Ask the same question in another repository/worktree | No notes from the first checkout |
| Update the skill and tune scan/retention settings | Matching unexpired notes reused, original review dates preserved |
| Run two local Copilot sessions | No corruption; a busy database/install produces an explicit retryable error |
| Disable cache or the current branch | Cache bypass reported and no cached answer served |
| Compare off/cold/warm sessions | Same model, prompt and commit; record answer correctness, elapsed time and actual AIC |

Use `repoecho benchmark --files 5000 --notes 30 --runs 5` for synthetic helper performance. Use `tools/usage_study.py --help` for a manual Copilot comparison sheet. The per-prompt token figure estimates potential source-context reduction; it cannot measure actual model billing or reasoning tokens.

## Limits to plan around

- **Evidence completeness:** hashes prove captured evidence is unchanged. They cannot detect an omitted dependency or make an incorrect summary true. Capture shared contracts, Maven/Gradle configuration, lockfiles and relevant scope membership. Read current instructions directly and cited code before editing.
- **Large repositories:** warm queries still enumerate/stat eligible files, so work grows with file count. Use focused module notes and narrow scopes. The 5,000-file Linux benchmark measured a 363 ms median helper query; this is not a guarantee for your Windows checkout or a million-file monorepo.
- **Storage:** full source files are not stored, but the file manifest grows with file count and notes grow with learning. The latest revision per named originating branch is protected; eight is a soft extra-history limit, not a global cap. There is no automatic global disk quota or shared cache service. Monitor `.repoecho` size during the pilot; `repoecho forget NOTE_ID` removes that workflow's retained revisions, including useful branch history.
- **Sensitivity:** default filename filters are not a secret scanner. Notes can contain proprietary content and become Copilot context when retrieved. Use your organisation's approved Copilot settings and repository exclusions.
- **Concurrent edits:** source verification is a point-in-time check, not an atomic snapshot of the entire repository. Prefer separate worktrees for independent edits. SQLite uses a five-second busy timeout; the cache belongs on a local filesystem.
- **Operational validation:** this audit and CI do not substitute for live Copilot, corporate CA/proxy, antivirus and Windows folder-lock testing. Nothing has been deployed to your colleagues by this change.

If a pilot identifies a wrong or stale answer, retain the prompt, note ID, source references, branch/commit, `repoecho --version` and redacted `repoecho doctor` output. Disable caching with `repoecho cache off` while investigating. Avoid sending cache databases or source containing secrets in support reports.
