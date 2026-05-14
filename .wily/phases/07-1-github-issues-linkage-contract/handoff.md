# Handoff

Start by designing the linkage contract, not by calling GitHub.

Recommended initial approach:

- Add a `github-issues-policy.md` reference under `skills/wily-workflow/references/`.
- Document optional metadata such as `github_issues: ["#123"]`, `github_url`, `owner`, and `sync_policy: "manual"`.
- Keep `$wily-status`, `$wily-next`, and `$wily-start` local-only by default.
- Treat `$wily-issues` as a future optional command skill if the contract justifies it.
