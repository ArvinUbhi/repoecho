# Mode controls

Use `python3 "$HELPER" --root "$REPO" COMMAND` (or `python`/`py -3` on Windows). Settings apply to the selected repository root/worktree, persist across sessions and do not affect other repositories.

| User intent | Command | Effect |
|---|---|---|
| Turn RepoEcho off/on here | `mode off` / `mode on` | Disable/enable the repository workflow |
| Disable/enable knowledge caching | `cache off` / `cache on` | Bypass/allow cache reads and writes; retain skill guidance |
| Disable/enable on this branch | `branch off` / `branch on` | Store an override for the current named Git branch |
| Use only the current branch | `branch only` | Default other branches off; replace overrides with current branch on |
| Use on all branches | `branch all` | Default on; clear all branch overrides |
| Remove this branch's override | `branch inherit` | Use the default branch setting |
| Show controls quickly | `mode`, `cache`, or `branch` | Report controls without indexing or opening the database |
| Show controls and cache state | `status` | Index/status when enabled; bypass report when disabled |

All three gates must allow caching: **skill on AND cache on AND current branch allowed**. Enabling one does not silently override another. Always report `effective_enabled` and any `bypass_reasons` so the user knows the actual result.

Example: `mode on` while `cache off` keeps caching disabled. `branch only` while `mode off` records branch policy but does not enable the workflow. If the user explicitly asks for all gates enabled, run `mode on`, `cache on`, and the requested branch rule, then report the effective state.

Off modes do not open, read or write the knowledge database and do not scan source content. They retain existing notes for later validated reuse. All knowledge commands, including `forget`, return a bypass report while off; status and mode commands remain available. Settings themselves are kept in `.repoecho/control.json`, updated atomically under an OS-released lock. A crashed writer cannot leave a stale lock. Invalid settings fail closed. These controls are checked at CLI invocation; they cannot cancel a command already running or erase information already in a model's context.

Git branch controls are resolved afresh on every invocation. Names containing `/` work. Detached HEAD and non-Git directories follow the default branch setting; they cannot receive a named-branch override. Thus `branch only` also disables detached HEAD until `branch all` or another applicable default policy is chosen. Ordinary `mode`/`cache` controls work in non-Git directories.

To disable discovery of the skill **across all repositories in Copilot itself**, the user can use `copilot skill disable repoecho`; enable with `copilot skill enable repoecho`. That is a Copilot setting, separate from these per-repository gates. A disabled Copilot skill will not process natural-language toggle requests until re-enabled.
