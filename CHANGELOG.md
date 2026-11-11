# Changelog

RepoEcho uses `MAJOR.MINOR.PATCH` versions. Major changes can break compatibility, minor changes add behaviour, and patches fix issues. `repoecho --version` shows the installed version. Each entry below names the change and links its commit on `main`.

## 1.6.0 — 11 November 2026

- Add dependency-free npm distribution with native Windows/POSIX command shims, bundled Copilot skill and explicit setup. Installation supports disabled lifecycle scripts and offline tarballs.
- Add MIT licensing to the repository and installed skill; document corporate registry, CA, runtime and update configuration.
- Keep npm updates separate from ZIP updates and avoid competing PATH launchers. Support an explicit approved Python executable.
- Test argument safety, runtime errors, package contents, offline installation, PATH shims and repeated setup. Add cross-platform npm CI and a gated provenance publishing workflow. ([Release commit](https://github.com/ArvinUbhi/repoecho/commit/cfeb48008c78e42190ae31e6fe1c971b6a28ae17).)
- npm accepted the initial public publication on 11 November 2026 after browser 2FA approval; registry availability follows npm processing.

## 1.5.1 — 5 November 2026

- Fix the Windows lock-initialisation race exposed by concurrent installer CI: acquire the byte-range lock without a pre-lock sentinel write. Add an empty-file concurrent-writer regression test. (This release commit.)

## 1.5.0 — 5 November 2026

- [Bound cache growth and focus retrieval on verified candidate evidence](https://github.com/ArvinUbhi/repoecho/commit/94d9ecf80b2185aea7772a92c35c2b1fcc810a26): bound per-checkout database pages, note revisions and outstanding receipts; retain valid branch history, clean expired entries, and add `storage` / `prune --compact` commands.
- Restrict query file inspection to candidate source/scope evidence while preserving Git discovery, strict hashes and branch-return reuse.
- Add ancestor build/lock-file capture hints and doctor warnings for duplicate installations and detected UNC/OneDrive locations.
- Add quota rollback, cleanup, focused retrieval, scope membership and diagnostics regression tests; update rollout guidance and benchmarks.

## 1.4.0 — 4 November 2026

- [Harden team rollout, cache settings, Git isolation and ZIP updates](https://github.com/ArvinUbhi/repoecho/commit/19204017c223cec7a722a10928fdf8de74aa6d05): preserve knowledge across operational settings changes; separate scan eligibility from evidence compatibility; normalize existing compatible notes without renewing dates.
- Prevent exported Git environment variables from redirecting repository discovery; require Git for detected checkouts instead of bypassing ignore rules.
- Serialize overlapping installs, stage launchers uniquely, and recheck downgrades inside the installation lock.
- Add approved-commit ZIP updates, optional SHA-256 verification, HTTPS-only URL validation and bounded archive extraction.
- Add team rollout/audit guidance, regression tests and a 5,000-file synthetic benchmark.

## 1.3.3 — 4 November 2026

- [Preserve learned cache across compatible RepoEcho updates](https://github.com/ArvinUbhi/repoecho/commit/5056c3bdd9d4a0334bb119d22de3fafe89276ad7): separate release and evidence compatibility versions, upgrade verified legacy notes without resetting timestamps, retain branch versions and deduplicate matching revisions. Add regression coverage for updates, migration, branch switching and stale/incompatible evidence.

## 1.3.2 — 4 November 2026

- [Report potential per-query source context token savings](https://github.com/ArvinUbhi/repoecho/commit/e8b4e082425af20639a1485b96739b47d734f9ba): add a per-query potential context-token estimate for verified compact notes and one-line agent reporting. The figure compares captured source text with compact notes; actual AIC still requires matched Copilot runs.
- [Fix Windows newline expectation in context estimate tests](https://github.com/ArvinUbhi/repoecho/commit/38f2e6174982e6d5c69b81075b1e494c8c9e802b): compare source characters using the bytes stored on disk.

## 1.3.1 — 4 November 2026

- [Support corporate HTTPS proxy and CA for ZIP updates](https://github.com/ArvinUbhi/repoecho/commit/2d62b9cfe48aec45abbcc3b2182e5a265f074f32): inherit `HTTPS_PROXY` from PowerShell, keep TLS verification, accept `--ca-cert`, and explain the browser ZIP fallback.

## 1.3.0 — 4 November 2026

- [Add uv Bash ZIP updater and version 1.3.0](https://github.com/ArvinUbhi/repoecho/commit/8862a7ba355fbe4e74d3950d3480ae378a017839): download/extract/install from a public ZIP, with an offline ZIP option and downgrade check.

## Earlier commits — 3 November 2026

- [Fix Windows installer test for short and long path aliases](https://github.com/ArvinUbhi/repoecho/commit/904ad5172697358a7696ed6f9c44ca3bdc2d5b24): compare the actual installed file across Windows path spellings.
- [Install repo echo command on user PATH without GitHub CLI](https://github.com/ArvinUbhi/repoecho/commit/517f23fde96368206fbd896fab134cc966dfe3e9): personal `repoecho` launcher and Windows/POSIX PATH setup.
- [Retain matching workflow revisions across Git branches](https://github.com/ArvinUbhi/repoecho/commit/689514ecadfa6c2c48e7bbe188f509039d9b977d): protect the latest learned revision per branch.
- [Rank workflow matches and add retrieval and Copilot usage evaluations](https://github.com/ArvinUbhi/repoecho/commit/a4d3706df94644697311bd6b7916eb6808022a65): component-aware ranking and AIC study sheet.
- [Add natural-language aliases and compact verified agent retrieval](https://github.com/ArvinUbhi/repoecho/commit/685db0ff21f758f8455a88580bf85f245f5c6f43): aliases, compact output and measured output reduction.
- [Reduce redundant cache work and adapt focused workflow notes](https://github.com/ArvinUbhi/repoecho/commit/65551141ec2bb38db9c280026d23b1c7fbebbb66): avoid repeated scans and refine workflow notes.
- [Make updating easy for ZIP and Git installations](https://github.com/ArvinUbhi/repoecho/commit/a36b37bcfb8e4812e6e7dbe8bd9e6b7106d53005): documented update steps.
- [Make ongoing learning and verified cache population explicit](https://github.com/ArvinUbhi/repoecho/commit/b4d70b43ec64e49d3ccd0ef0b6df5b5ab634b770): capture and save useful findings while working.
- [Simplify setup and explain instruction refresh and branch reuse](https://github.com/ArvinUbhi/repoecho/commit/4c5032a0f82ebcb0a4c648e759fad31a17fdd5b1): README setup and branch examples.
- [Document default Copilot workflow through RepoEcho scripts](https://github.com/ArvinUbhi/repoecho/commit/f3d194fcb1b7b0b639efdfd986a336c3203991bd): standing Copilot instructions.
- [Make gh optional and document Windows ZIP setup with uv](https://github.com/ArvinUbhi/repoecho/commit/5901cf82d3224c866cdb85fa6e8b59ae5dc73255): no-gh installation.
- [Rewrite README around user setup and everyday usage](https://github.com/ArvinUbhi/repoecho/commit/f1a42df935616c0667e4ff7cea02d9d096f8e0bb): user-focused guide.
- [Simplify RepoEcho with uv setup, gh controls and portable benchmarks](https://github.com/ArvinUbhi/repoecho/commit/70db80e7748d1a1f614897d933fb484e64eb32fb): initial command controls and benchmark.
- [Add mode controls, Git-aware change tracking and isolated branch-aware caches](https://github.com/ArvinUbhi/repoecho/commit/586a124): settings and repository isolation.
- [Handle Windows timestamp differences without weakening source-read validation](https://github.com/ArvinUbhi/repoecho/commit/672c538): Windows file metadata handling.
- [Build RepoEcho two-pass repository knowledge cache for Copilot CLI](https://github.com/ArvinUbhi/repoecho/commit/a1eb947): first working cache and skill.
- [Initial commit](https://github.com/ArvinUbhi/repoecho/commit/fd008ac): repository start.
