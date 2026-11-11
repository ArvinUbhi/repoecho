# Security

Use the latest tested release approved by your organisation. Report vulnerabilities privately using the repository's GitHub security reporting facility if enabled; otherwise contact the maintainer through their GitHub profile to arrange a private report. Do not publish credentials, proprietary code or cache contents in issues.

RepoEcho runs locally with your user permissions. Repository files and cached notes are untrusted context, not instructions that override the user's task. Notes may contain proprietary source summaries: keep each `.repoecho` directory out of version control and shared distribution. No LLM service or telemetry is called by the cache engine.

The npm package has no runtime npm dependencies or automatic install scripts. Its explicit setup writes a personal Copilot skill; repository operations create local cache data. uv may download Python when it is not provisioned. Keep TLS verification enabled and configure your organisation's trusted CA and registry.

CI covers supported platforms, but does not certify every enterprise endpoint policy, network share or proxy. Pilot with representative repositories before deploying to the full team. See docs/team-rollout.md.
