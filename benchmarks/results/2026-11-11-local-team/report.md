# RepoEcho benchmark report

Status: complete

Generated: 2026-11-11T23:00:14.437981+00:00

Environment: Linux / Python 3.12.14

Synthetic helper timings include Python process startup and Git. No LLM calls, actual token savings, AIC or thinking-time measurements. Cold scan means an empty RepoEcho cache, not cold OS disk caches.

## Measured scenarios

| Build | Trial | Files | Repo | Scenario | N | Median ms | p95 ms |
|---|---:|---:|---|---|---:|---:|---:|
| candidate | 1 | 1000 | git | cold_scan | 1 | 372.63 | 372.63 |
| candidate | 1 | 1000 | git | warm_hit | 3 | 189.25 | 193.35 |
| candidate | 1 | 1000 | git | compact_hit | 3 | 163.82 | 178.02 |
| candidate | 1 | 1000 | git | concurrent_readers_4 | 12 | 180.27 | 271.76 |
| candidate | 1 | 1000 | git | query_miss | 3 | 204.12 | 213.12 |
| candidate | 1 | 1000 | git | budget_omission | 3 | 162.10 | 214.87 |
| candidate | 1 | 1000 | git | warm_scan | 3 | 273.29 | 308.64 |
| candidate | 1 | 1000 | git | full_scan | 3 | 446.29 | 446.57 |
| candidate | 1 | 1000 | git | mode_off | 3 | 102.54 | 102.80 |
| candidate | 1 | 1000 | git | cache_off | 3 | 108.69 | 147.29 |
| candidate | 1 | 1000 | git | branch_off | 3 | 80.17 | 80.26 |
| candidate | 1 | 1000 | git | repository_isolation | 3 | 105.53 | 110.80 |
| candidate | 1 | 1000 | git | unrelated_edit | 3 | 142.96 | 199.69 |
| candidate | 1 | 1000 | git | dirty_evidence | 3 | 149.21 | 155.33 |
| candidate | 1 | 1000 | git | staged_evidence | 3 | 153.22 | 182.78 |
| candidate | 1 | 1000 | git | renamed_evidence | 3 | 127.64 | 141.98 |
| candidate | 1 | 1000 | git | deleted_evidence | 3 | 110.32 | 120.10 |
| candidate | 1 | 1000 | git | restored_evidence | 3 | 117.69 | 124.90 |
| candidate | 1 | 1000 | git | scope_addition | 3 | 160.71 | 187.96 |
| candidate | 1 | 1000 | git | unchanged_branch | 3 | 118.27 | 119.54 |
| candidate | 1 | 1000 | git | changed_branch | 3 | 115.67 | 137.67 |
| candidate | 1 | 1000 | git | branch_return | 3 | 107.19 | 131.02 |
| candidate | 1 | 1000 | git | feature_return | 3 | 106.57 | 108.70 |
| candidate | 1 | 1000 | git | worktree_isolation | 3 | 142.79 | 147.88 |
| baseline | 1 | 1000 | git | cold_scan | 1 | 432.67 | 432.67 |
| baseline | 1 | 1000 | git | warm_hit | 3 | 119.65 | 119.70 |
| baseline | 1 | 1000 | git | compact_hit | 3 | 134.91 | 143.45 |
| baseline | 1 | 1000 | git | concurrent_readers_4 | 12 | 150.46 | 174.61 |
| baseline | 1 | 1000 | git | query_miss | 3 | 143.89 | 148.16 |
| baseline | 1 | 1000 | git | budget_omission | 3 | 118.84 | 126.40 |
| baseline | 1 | 1000 | git | warm_scan | 3 | 177.14 | 178.20 |
| baseline | 1 | 1000 | git | full_scan | 3 | 369.81 | 410.03 |
| baseline | 1 | 1000 | git | mode_off | 3 | 72.87 | 82.66 |
| baseline | 1 | 1000 | git | cache_off | 3 | 80.58 | 82.36 |
| baseline | 1 | 1000 | git | branch_off | 3 | 83.65 | 94.96 |
| baseline | 1 | 1000 | git | repository_isolation | 3 | 83.17 | 88.55 |
| baseline | 1 | 1000 | git | unrelated_edit | 3 | 145.25 | 164.21 |
| baseline | 1 | 1000 | git | dirty_evidence | 3 | 122.96 | 138.97 |
| baseline | 1 | 1000 | git | staged_evidence | 3 | 100.67 | 113.66 |
| baseline | 1 | 1000 | git | renamed_evidence | 3 | 111.35 | 124.75 |
| baseline | 1 | 1000 | git | deleted_evidence | 3 | 113.56 | 118.31 |
| baseline | 1 | 1000 | git | restored_evidence | 3 | 114.45 | 115.39 |
| baseline | 1 | 1000 | git | scope_addition | 3 | 158.31 | 160.93 |
| baseline | 1 | 1000 | git | unchanged_branch | 3 | 101.70 | 105.26 |
| baseline | 1 | 1000 | git | changed_branch | 3 | 114.74 | 120.24 |
| baseline | 1 | 1000 | git | branch_return | 3 | 113.61 | 115.84 |
| baseline | 1 | 1000 | git | feature_return | 3 | 123.64 | 136.83 |
| baseline | 1 | 1000 | git | worktree_isolation | 3 | 124.87 | 160.77 |
| candidate | 1 | 1000 | plain | cold_scan | 1 | 334.40 | 334.40 |
| candidate | 1 | 1000 | plain | warm_hit | 3 | 120.96 | 133.44 |
| candidate | 1 | 1000 | plain | compact_hit | 3 | 114.69 | 134.87 |
| candidate | 1 | 1000 | plain | concurrent_readers_4 | 12 | 137.14 | 164.98 |
| candidate | 1 | 1000 | plain | query_miss | 3 | 110.63 | 118.40 |
| candidate | 1 | 1000 | plain | budget_omission | 3 | 117.29 | 143.99 |
| candidate | 1 | 1000 | plain | warm_scan | 3 | 166.24 | 200.22 |
| candidate | 1 | 1000 | plain | full_scan | 3 | 378.18 | 389.77 |
| candidate | 1 | 1000 | plain | mode_off | 3 | 70.03 | 84.51 |
| candidate | 1 | 1000 | plain | cache_off | 3 | 68.33 | 76.90 |
| candidate | 1 | 1000 | plain | repository_isolation | 3 | 83.45 | 85.99 |
| candidate | 1 | 1000 | plain | unrelated_edit | 3 | 126.78 | 136.24 |
| candidate | 1 | 1000 | plain | dirty_evidence | 3 | 149.11 | 150.80 |
| candidate | 1 | 1000 | plain | renamed_evidence | 3 | 127.26 | 168.28 |
| candidate | 1 | 1000 | plain | deleted_evidence | 3 | 131.36 | 149.18 |
| candidate | 1 | 1000 | plain | restored_evidence | 3 | 114.57 | 124.74 |
| candidate | 1 | 1000 | plain | scope_addition | 3 | 151.33 | 161.94 |
| baseline | 1 | 1000 | plain | cold_scan | 1 | 458.15 | 458.15 |
| baseline | 1 | 1000 | plain | warm_hit | 3 | 117.50 | 134.42 |
| baseline | 1 | 1000 | plain | compact_hit | 3 | 116.16 | 129.76 |
| baseline | 1 | 1000 | plain | concurrent_readers_4 | 12 | 171.09 | 181.05 |
| baseline | 1 | 1000 | plain | query_miss | 3 | 125.95 | 126.16 |
| baseline | 1 | 1000 | plain | budget_omission | 3 | 126.22 | 162.18 |
| baseline | 1 | 1000 | plain | warm_scan | 3 | 159.59 | 167.12 |
| baseline | 1 | 1000 | plain | full_scan | 3 | 332.39 | 352.33 |
| baseline | 1 | 1000 | plain | mode_off | 3 | 85.40 | 86.85 |
| baseline | 1 | 1000 | plain | cache_off | 3 | 73.27 | 74.06 |
| baseline | 1 | 1000 | plain | repository_isolation | 3 | 83.66 | 88.80 |
| baseline | 1 | 1000 | plain | unrelated_edit | 3 | 128.20 | 128.33 |
| baseline | 1 | 1000 | plain | dirty_evidence | 3 | 123.58 | 129.02 |
| baseline | 1 | 1000 | plain | renamed_evidence | 3 | 141.46 | 146.66 |
| baseline | 1 | 1000 | plain | deleted_evidence | 3 | 119.58 | 140.13 |
| baseline | 1 | 1000 | plain | restored_evidence | 3 | 120.98 | 132.78 |
| baseline | 1 | 1000 | plain | scope_addition | 3 | 159.22 | 173.88 |
| candidate | 1 | 5000 | git | cold_scan | 1 | 1397.01 | 1397.01 |
| candidate | 1 | 5000 | git | warm_hit | 3 | 306.41 | 316.26 |
| candidate | 1 | 5000 | git | compact_hit | 3 | 255.04 | 393.91 |
| candidate | 1 | 5000 | git | concurrent_readers_4 | 12 | 338.38 | 380.59 |
| candidate | 1 | 5000 | git | query_miss | 3 | 280.74 | 289.19 |
| candidate | 1 | 5000 | git | budget_omission | 3 | 280.41 | 288.24 |
| candidate | 1 | 5000 | git | warm_scan | 3 | 596.82 | 607.36 |
| candidate | 1 | 5000 | git | full_scan | 3 | 1591.79 | 2932.30 |
| candidate | 1 | 5000 | git | mode_off | 3 | 121.64 | 131.19 |
| candidate | 1 | 5000 | git | cache_off | 3 | 111.16 | 141.45 |
| candidate | 1 | 5000 | git | branch_off | 3 | 114.76 | 253.40 |
| candidate | 1 | 5000 | git | repository_isolation | 3 | 115.58 | 154.39 |
| candidate | 1 | 5000 | git | unrelated_edit | 3 | 343.47 | 382.24 |
| candidate | 1 | 5000 | git | dirty_evidence | 3 | 196.38 | 500.28 |
| candidate | 1 | 5000 | git | staged_evidence | 3 | 211.64 | 214.88 |
| candidate | 1 | 5000 | git | renamed_evidence | 3 | 244.11 | 256.72 |
| candidate | 1 | 5000 | git | deleted_evidence | 3 | 207.43 | 207.67 |
| candidate | 1 | 5000 | git | restored_evidence | 3 | 186.90 | 211.26 |
| candidate | 1 | 5000 | git | scope_addition | 3 | 378.51 | 397.02 |
| candidate | 1 | 5000 | git | unchanged_branch | 3 | 166.61 | 178.64 |
| candidate | 1 | 5000 | git | changed_branch | 3 | 181.41 | 474.02 |
| candidate | 1 | 5000 | git | branch_return | 3 | 176.68 | 186.65 |
| candidate | 1 | 5000 | git | feature_return | 3 | 171.98 | 177.23 |
| candidate | 1 | 5000 | git | worktree_isolation | 3 | 256.85 | 278.62 |
| baseline | 1 | 5000 | git | cold_scan | 1 | 1342.65 | 1342.65 |
| baseline | 1 | 5000 | git | warm_hit | 3 | 138.97 | 229.48 |
| baseline | 1 | 5000 | git | compact_hit | 3 | 190.45 | 211.26 |
| baseline | 1 | 5000 | git | concurrent_readers_4 | 12 | 181.40 | 227.77 |
| baseline | 1 | 5000 | git | query_miss | 3 | 167.40 | 183.53 |
| baseline | 1 | 5000 | git | budget_omission | 3 | 188.62 | 192.53 |
| baseline | 1 | 5000 | git | warm_scan | 3 | 486.78 | 499.94 |
| baseline | 1 | 5000 | git | full_scan | 3 | 1550.89 | 1772.95 |
| baseline | 1 | 5000 | git | mode_off | 3 | 98.34 | 113.09 |
| baseline | 1 | 5000 | git | cache_off | 3 | 106.36 | 125.36 |
| baseline | 1 | 5000 | git | branch_off | 3 | 82.29 | 85.70 |
| baseline | 1 | 5000 | git | repository_isolation | 3 | 83.69 | 89.75 |
| baseline | 1 | 5000 | git | unrelated_edit | 3 | 153.53 | 163.41 |
| baseline | 1 | 5000 | git | dirty_evidence | 3 | 128.82 | 182.04 |
| baseline | 1 | 5000 | git | staged_evidence | 3 | 171.56 | 203.02 |
| baseline | 1 | 5000 | git | renamed_evidence | 3 | 142.38 | 147.90 |
| baseline | 1 | 5000 | git | deleted_evidence | 3 | 163.26 | 171.07 |
| baseline | 1 | 5000 | git | restored_evidence | 3 | 149.98 | 170.52 |
| baseline | 1 | 5000 | git | scope_addition | 3 | 374.65 | 375.61 |
| baseline | 1 | 5000 | git | unchanged_branch | 3 | 147.90 | 203.66 |
| baseline | 1 | 5000 | git | changed_branch | 3 | 162.36 | 234.39 |
| baseline | 1 | 5000 | git | branch_return | 3 | 151.27 | 254.63 |
| baseline | 1 | 5000 | git | feature_return | 3 | 142.30 | 147.99 |
| baseline | 1 | 5000 | git | worktree_isolation | 3 | 202.37 | 223.45 |
| candidate | 1 | 5000 | plain | cold_scan | 1 | 1548.25 | 1548.25 |
| candidate | 1 | 5000 | plain | warm_hit | 3 | 336.06 | 361.91 |
| candidate | 1 | 5000 | plain | compact_hit | 3 | 402.04 | 412.59 |
| candidate | 1 | 5000 | plain | concurrent_readers_4 | 12 | 405.42 | 496.11 |
| candidate | 1 | 5000 | plain | query_miss | 3 | 303.18 | 316.32 |
| candidate | 1 | 5000 | plain | budget_omission | 3 | 290.87 | 372.43 |
| candidate | 1 | 5000 | plain | warm_scan | 3 | 673.05 | 864.98 |
| candidate | 1 | 5000 | plain | full_scan | 3 | 1857.40 | 1858.25 |
| candidate | 1 | 5000 | plain | mode_off | 3 | 75.26 | 118.77 |
| candidate | 1 | 5000 | plain | cache_off | 3 | 71.89 | 75.29 |
| candidate | 1 | 5000 | plain | repository_isolation | 3 | 77.47 | 100.24 |
| candidate | 1 | 5000 | plain | unrelated_edit | 3 | 310.34 | 322.02 |
| candidate | 1 | 5000 | plain | dirty_evidence | 3 | 331.92 | 336.94 |
| candidate | 1 | 5000 | plain | renamed_evidence | 3 | 314.45 | 322.93 |
| candidate | 1 | 5000 | plain | deleted_evidence | 3 | 346.95 | 374.67 |
| candidate | 1 | 5000 | plain | restored_evidence | 3 | 347.89 | 355.88 |
| candidate | 1 | 5000 | plain | scope_addition | 3 | 553.26 | 561.48 |
| baseline | 1 | 5000 | plain | cold_scan | 1 | 1668.40 | 1668.40 |
| baseline | 1 | 5000 | plain | warm_hit | 3 | 284.31 | 304.05 |
| baseline | 1 | 5000 | plain | compact_hit | 3 | 323.30 | 356.88 |
| baseline | 1 | 5000 | plain | concurrent_readers_4 | 12 | 333.66 | 417.48 |
| baseline | 1 | 5000 | plain | query_miss | 3 | 300.77 | 304.49 |
| baseline | 1 | 5000 | plain | budget_omission | 3 | 284.19 | 303.62 |
| baseline | 1 | 5000 | plain | warm_scan | 3 | 521.77 | 537.01 |
| baseline | 1 | 5000 | plain | full_scan | 3 | 1518.94 | 1573.27 |
| baseline | 1 | 5000 | plain | mode_off | 3 | 82.77 | 82.85 |
| baseline | 1 | 5000 | plain | cache_off | 3 | 69.33 | 75.79 |
| baseline | 1 | 5000 | plain | repository_isolation | 3 | 77.80 | 79.20 |
| baseline | 1 | 5000 | plain | unrelated_edit | 3 | 281.74 | 317.69 |
| baseline | 1 | 5000 | plain | dirty_evidence | 3 | 276.34 | 291.74 |
| baseline | 1 | 5000 | plain | renamed_evidence | 3 | 261.28 | 279.54 |
| baseline | 1 | 5000 | plain | deleted_evidence | 3 | 271.13 | 357.46 |
| baseline | 1 | 5000 | plain | restored_evidence | 3 | 305.89 | 318.30 |
| baseline | 1 | 5000 | plain | scope_addition | 3 | 442.08 | 459.47 |

## Storage and context

| Build | Trial | Files | Repo | DB allocated bytes | Revisions | Compact response bytes |
|---|---:|---:|---|---:|---:|---:|
| candidate | 1 | 1000 | git | 339968 | 22 | 825 |
| baseline | 1 | 1000 | git | 335872 | 22 | 825 |
| candidate | 1 | 1000 | plain | 323584 | 21 | 825 |
| baseline | 1 | 1000 | plain | 323584 | 21 | 825 |
| candidate | 1 | 5000 | git | 1458176 | 102 | 825 |
| baseline | 1 | 5000 | git | 1458176 | 102 | 825 |
| candidate | 1 | 5000 | plain | 1388544 | 101 | 825 |
| baseline | 1 | 5000 | plain | 1388544 | 101 | 825 |

## Baseline comparison

Positive changes are slower. Flags require both percentage and absolute thresholds; confirm on a controlled machine before treating timing as a release blocker.

| Files | Repo | Trial | Scenario | Baseline ms | Candidate ms | Change % | Flag |
|---:|---|---:|---|---:|---:|---:|---|
| 1000 | git | 1 | cold_scan | 432.67 | 372.63 | -13.9 |  |
| 1000 | git | 1 | warm_hit | 119.65 | 189.25 | +58.2 | REVIEW |
| 1000 | git | 1 | compact_hit | 134.91 | 163.82 | +21.4 |  |
| 1000 | git | 1 | concurrent_readers_4 | 150.46 | 180.27 | +19.8 |  |
| 1000 | git | 1 | query_miss | 143.89 | 204.12 | +41.9 | REVIEW |
| 1000 | git | 1 | budget_omission | 118.84 | 162.10 | +36.4 | REVIEW |
| 1000 | git | 1 | warm_scan | 177.14 | 273.29 | +54.3 | REVIEW |
| 1000 | git | 1 | full_scan | 369.81 | 446.29 | +20.7 |  |
| 1000 | git | 1 | mode_off | 72.87 | 102.54 | +40.7 | REVIEW |
| 1000 | git | 1 | cache_off | 80.58 | 108.69 | +34.9 | REVIEW |
| 1000 | git | 1 | branch_off | 83.65 | 80.17 | -4.2 |  |
| 1000 | git | 1 | repository_isolation | 83.17 | 105.53 | +26.9 | REVIEW |
| 1000 | git | 1 | unrelated_edit | 145.25 | 142.96 | -1.6 |  |
| 1000 | git | 1 | dirty_evidence | 122.96 | 149.21 | +21.3 |  |
| 1000 | git | 1 | staged_evidence | 100.67 | 153.22 | +52.2 | REVIEW |
| 1000 | git | 1 | renamed_evidence | 111.35 | 127.64 | +14.6 |  |
| 1000 | git | 1 | deleted_evidence | 113.56 | 110.32 | -2.9 |  |
| 1000 | git | 1 | restored_evidence | 114.45 | 117.69 | +2.8 |  |
| 1000 | git | 1 | scope_addition | 158.31 | 160.71 | +1.5 |  |
| 1000 | git | 1 | unchanged_branch | 101.70 | 118.27 | +16.3 |  |
| 1000 | git | 1 | changed_branch | 114.74 | 115.67 | +0.8 |  |
| 1000 | git | 1 | branch_return | 113.61 | 107.19 | -5.6 |  |
| 1000 | git | 1 | feature_return | 123.64 | 106.57 | -13.8 |  |
| 1000 | git | 1 | worktree_isolation | 124.87 | 142.79 | +14.3 |  |
| 1000 | plain | 1 | cold_scan | 458.15 | 334.40 | -27.0 |  |
| 1000 | plain | 1 | warm_hit | 117.50 | 120.96 | +2.9 |  |
| 1000 | plain | 1 | compact_hit | 116.16 | 114.69 | -1.3 |  |
| 1000 | plain | 1 | concurrent_readers_4 | 171.09 | 137.14 | -19.8 |  |
| 1000 | plain | 1 | query_miss | 125.95 | 110.63 | -12.2 |  |
| 1000 | plain | 1 | budget_omission | 126.22 | 117.29 | -7.1 |  |
| 1000 | plain | 1 | warm_scan | 159.59 | 166.24 | +4.2 |  |
| 1000 | plain | 1 | full_scan | 332.39 | 378.18 | +13.8 |  |
| 1000 | plain | 1 | mode_off | 85.40 | 70.03 | -18.0 |  |
| 1000 | plain | 1 | cache_off | 73.27 | 68.33 | -6.7 |  |
| 1000 | plain | 1 | repository_isolation | 83.66 | 83.45 | -0.2 |  |
| 1000 | plain | 1 | unrelated_edit | 128.20 | 126.78 | -1.1 |  |
| 1000 | plain | 1 | dirty_evidence | 123.58 | 149.11 | +20.7 |  |
| 1000 | plain | 1 | renamed_evidence | 141.46 | 127.26 | -10.0 |  |
| 1000 | plain | 1 | deleted_evidence | 119.58 | 131.36 | +9.8 |  |
| 1000 | plain | 1 | restored_evidence | 120.98 | 114.57 | -5.3 |  |
| 1000 | plain | 1 | scope_addition | 159.22 | 151.33 | -5.0 |  |
| 5000 | git | 1 | cold_scan | 1342.65 | 1397.01 | +4.0 |  |
| 5000 | git | 1 | warm_hit | 138.97 | 306.41 | +120.5 | REVIEW |
| 5000 | git | 1 | compact_hit | 190.45 | 255.04 | +33.9 | REVIEW |
| 5000 | git | 1 | concurrent_readers_4 | 181.40 | 338.38 | +86.5 | REVIEW |
| 5000 | git | 1 | query_miss | 167.40 | 280.74 | +67.7 | REVIEW |
| 5000 | git | 1 | budget_omission | 188.62 | 280.41 | +48.7 | REVIEW |
| 5000 | git | 1 | warm_scan | 486.78 | 596.82 | +22.6 |  |
| 5000 | git | 1 | full_scan | 1550.89 | 1591.79 | +2.6 |  |
| 5000 | git | 1 | mode_off | 98.34 | 121.64 | +23.7 |  |
| 5000 | git | 1 | cache_off | 106.36 | 111.16 | +4.5 |  |
| 5000 | git | 1 | branch_off | 82.29 | 114.76 | +39.5 | REVIEW |
| 5000 | git | 1 | repository_isolation | 83.69 | 115.58 | +38.1 | REVIEW |
| 5000 | git | 1 | unrelated_edit | 153.53 | 343.47 | +123.7 | REVIEW |
| 5000 | git | 1 | dirty_evidence | 128.82 | 196.38 | +52.4 | REVIEW |
| 5000 | git | 1 | staged_evidence | 171.56 | 211.64 | +23.4 |  |
| 5000 | git | 1 | renamed_evidence | 142.38 | 244.11 | +71.4 | REVIEW |
| 5000 | git | 1 | deleted_evidence | 163.26 | 207.43 | +27.1 | REVIEW |
| 5000 | git | 1 | restored_evidence | 149.98 | 186.90 | +24.6 |  |
| 5000 | git | 1 | scope_addition | 374.65 | 378.51 | +1.0 |  |
| 5000 | git | 1 | unchanged_branch | 147.90 | 166.61 | +12.7 |  |
| 5000 | git | 1 | changed_branch | 162.36 | 181.41 | +11.7 |  |
| 5000 | git | 1 | branch_return | 151.27 | 176.68 | +16.8 |  |
| 5000 | git | 1 | feature_return | 142.30 | 171.98 | +20.9 |  |
| 5000 | git | 1 | worktree_isolation | 202.37 | 256.85 | +26.9 | REVIEW |
| 5000 | plain | 1 | cold_scan | 1668.40 | 1548.25 | -7.2 |  |
| 5000 | plain | 1 | warm_hit | 284.31 | 336.06 | +18.2 |  |
| 5000 | plain | 1 | compact_hit | 323.30 | 402.04 | +24.4 |  |
| 5000 | plain | 1 | concurrent_readers_4 | 333.66 | 405.42 | +21.5 |  |
| 5000 | plain | 1 | query_miss | 300.77 | 303.18 | +0.8 |  |
| 5000 | plain | 1 | budget_omission | 284.19 | 290.87 | +2.4 |  |
| 5000 | plain | 1 | warm_scan | 521.77 | 673.05 | +29.0 | REVIEW |
| 5000 | plain | 1 | full_scan | 1518.94 | 1857.40 | +22.3 |  |
| 5000 | plain | 1 | mode_off | 82.77 | 75.26 | -9.1 |  |
| 5000 | plain | 1 | cache_off | 69.33 | 71.89 | +3.7 |  |
| 5000 | plain | 1 | repository_isolation | 77.80 | 77.47 | -0.4 |  |
| 5000 | plain | 1 | unrelated_edit | 281.74 | 310.34 | +10.2 |  |
| 5000 | plain | 1 | dirty_evidence | 276.34 | 331.92 | +20.1 |  |
| 5000 | plain | 1 | renamed_evidence | 261.28 | 314.45 | +20.3 |  |
| 5000 | plain | 1 | deleted_evidence | 271.13 | 346.95 | +28.0 | REVIEW |
| 5000 | plain | 1 | restored_evidence | 305.89 | 347.89 | +13.7 |  |
| 5000 | plain | 1 | scope_addition | 442.08 | 553.26 | +25.1 | REVIEW |

Raw samples, engine SHA-256 identities, thresholds and detailed storage/context estimates are in report.json and samples.csv. p95 uses nearest rank; small samples do not establish an SLA. Correctness failures abort the suite and produce failure.json.
