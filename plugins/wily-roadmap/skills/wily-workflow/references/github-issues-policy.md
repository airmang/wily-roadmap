# GitHub Issues Policy

GitHub Issues are optional. Wily must work the same way in projects that do not use GitHub Issues.

## Source Of Truth

GitHub Issues are the collaboration source of truth for assignment, discussion, labels, and issue lifecycle.

Wily is the roadmap and execution source of truth for local phases, sessions, verification, changed files, and implementation handoff.

## Optional Phase Metadata

Use optional metadata when a Wily phase is linked to GitHub:

```yaml
github_issues: ["#123"]
github_urls: ["https://github.com/org/repo/issues/123"]
owner: "github:@alice"
sync_policy: "manual"
```

Do not copy full issue bodies into Wily state. Store issue identifiers, URLs, ownership hints, and short local phase context.

## Commands

`$wily-issues` is an explicit optional command. Its default mode is read-only: it may inspect issues, show linked and unlinked work, and suggest roadmap additions.

Do not add unlinked issues to the roadmap without user approval.

Approved `$wily-issues --add-to-roadmap` changes only local `.wily` roadmap and phase files.

Remote-write actions such as creating issues, commenting, changing labels, changing assignees, or closing issues belong in future explicit commands such as `$wily-issue-create` or `$wily-issue-update`.

## Core Wily Behavior

Keep `$wily-status`, `$wily-next`, `$wily-start`, `$wily-complete`, and `$wily-replan` GitHub-free by default.

If GitHub issue inspection is unavailable, report that the issue source is not configured and continue to support normal Wily roadmap work.
