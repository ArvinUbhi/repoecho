# Published benchmark comparisons

[All benchmark runs](https://github.com/ArvinUbhi/repoecho/actions/workflows/benchmarks.yml) · [How to run and interpret benchmarks](../docs/benchmarking.md)

## Initial reference — 11 November 2026

[Report run 43018551444](https://github.com/ArvinUbhi/repoecho/actions/runs/43018551444) completed successfully on all three operating systems. Candidate commit: `a3455bf2d6c7ea1d85f89c0759ee3c3f5e09f513`. Baseline: `cfeb48008c78e42190ae31e6fe1c971b6a28ae17` (1.6.0). The engine hashes are identical: this establishes a measurement reference, not a claimed optimization.

Each OS ran eight fixtures: Git/plain × candidate/baseline × two trials, with 100 files, five notes and ten samples per repeated scenario. There are 24 Git scenarios and 17 plain-directory scenarios, yielding 82 paired scenario comparisons per OS. All correctness checks passed. The existing 12-job Python/npm CI matrix also passed.

| Runner | Candidate warm Git query median, trials 1 / 2 | Candidate warm plain query median, trials 1 / 2 | Advisory timing flags |
|---|---:|---:|---:|
| Ubuntu | 79.22 / 77.76 ms | 68.59 / 69.59 ms | 0 of 82 |
| Windows | 202.94 / 203.52 ms | 126.49 / 130.93 ms | 5 of 82 |
| macOS | 198.88 / 177.33 ms | 139.07 / 135.30 ms | 8 of 82 |

These are synthetic measurements on different hosted runners, not a controlled operating-system comparison. Flags compare candidate and baseline on the same runner and require both a 25% and 10 ms median increase. Because the engine is unchanged, the flags demonstrate environmental/sample noise; they are not evidence of a code regression. Use longer repeated runs on a controlled workstation before adopting timing gates.

Download each OS artifact from the run for the full HTML/Markdown report, raw JSON/CSV samples and commit provenance. GitHub retains these artifacts for 90 days; this summary is retained in Git. The full suite also offers 1,000, 5,000 and 20,000-file profiles; this initial published run covers the smoke profile only.

No actual Copilot token savings, answer-quality improvement, monetary savings or model-thinking speedup has been established by these synthetic tests. Use the paired-session study procedure for those questions.
