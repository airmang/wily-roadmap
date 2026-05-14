# Remote And Destructive Action Policy

## Defaults

Wily is local-first.

Do not run these actions unless the user explicitly asks:

- push
- pull with merge or rebase effects
- open a PR
- mark a PR ready
- merge a PR
- delete branches
- delete user files
- rewrite history
- reset or checkout over local changes
- install or configure remote integrations

## Before Remote Work

Before remote work, state:

1. target branch or remote,
2. current branch,
3. current `git status --short`,
4. exact command class: push, PR creation, PR update, merge, or fetch-only inspection,
5. phase or session that the remote action belongs to.

Then wait for explicit approval.

## Before Destructive Work

Before destructive work, state:

1. files or refs affected,
2. whether user changes are present,
3. why the action is needed,
4. safer alternative if one exists.

Then wait for explicit approval.

## Merge Conflict Rule

When resolving conflicts, edit only files needed for the active conflict. Do not add new features, rewrite roadmap state, switch branches, abort merges, push, or open PRs unless the user explicitly asked for that action.

## Roadmap Recording

If approved remote or destructive work happens as part of a phase, record it in that phase's session result.
