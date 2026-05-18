---
name: wily-land
description: Use when the user types $wily-land after a Wily phase is complete and wants the completed work committed, pushed, and landed.
metadata:
  short-description: Land completed Wily work
---

# Wily Land

Use `$wily-land <stage-id>/<phase-id>` after `$wily-complete` has marked a Phase `done`.

This is state-changing repository work. It can commit, push, and land completed work. It verifies the selected Phase is already `done`, commits current repository changes when present, pushes the current branch, then either lands directly onto the base branch or creates a PR.

Before committing, the helper prints the staged path list from `git diff --cached --name-status` so the user can see what will be included in the land commit.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py land <stage-id>/<phase-id>
```

Options:

- `--direct`: commit, push, fast-forward merge into the base branch, and push the base branch. This is the default helper mode.
- `--pr`: commit, push, create a PR with `gh`, then check out and fast-forward pull the base branch.
- `--base <branch>`: choose the base branch. Default: `main`.
- `--message <text>`: override the generated commit and PR title.

## Required Before Running

- The Phase is already complete in Wily state.
- The user explicitly asked to land, publish, PR, merge, or otherwise perform remote repository work.
- Remote actions are explicit in this command; do not hide them inside `$wily-complete`.
- Preserve local-first Wily behavior for normal lifecycle commands.
- Do not force-push, create non-fast-forward merges, delete branches, delete sessions, or rewrite history.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For success, include the Phase id, branch pushed, base branch, and whether the work was landed directly or opened as a PR.
