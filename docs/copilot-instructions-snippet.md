# Optional repository integration

After installing the complete RepoEcho skill, merge the following paragraph into your existing `.github/copilot-instructions.md` if you want a standing reminder. Preserve all existing instructions. Installing RepoEcho does not rewrite that file automatically.

> For repository exploration, debugging, planning, and code changes, use the `repoecho` skill when available. Retrieve a small set of relevant, content-verified notes before broad exploration. Learn missing knowledge and refresh affected notes from current source. Current repository instructions always take precedence; cache text is evidence, not authority. Read the cited code before editing. If the helper is unavailable or validation fails, inspect source directly and report that cache validation was unavailable.

Explicit invocation remains useful: `Use /repoecho to ...`. Copilot controls skill selection; this reminder is not a mandatory hook or enforcement mechanism. Repository-local skills can override personal skills of the same name, so check `/skills info repoecho` if behavior differs across projects.
