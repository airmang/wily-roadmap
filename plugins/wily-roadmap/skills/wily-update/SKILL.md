---
name: wily-update
description: Use when the user types $wily-update or wants to check, migrate, or apply Wily plugin updates.
metadata:
  short-description: Update Wily plugin install
---

# Wily Update

Use `$wily-update` to explicitly check or apply updates for the Wily plugin install.

This is installation-changing when `--migrate` or `--yes` is used. It does not change the target repository roadmap. No background checks.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py update [--check|--migrate|--yes]
```

## Modes

- `$wily-update --check` is read-only. It reports the current plugin version, install type, and whether the git-managed install is current.
- `$wily-update --migrate` is for a zip-based install. It creates a sibling git-managed install and leaves the original zip directory unchanged.
- `$wily-update --yes` applies a fast-forward-only update for a clean git-managed install.

## Boundaries

- No background checks.
- Remote actions remain approval-first.
- Dirty git-managed installs must be refused before fetching or pulling.
- Zip installs must not be patched, overwritten, or deleted automatically.
- Do not run non-fast-forward pulls, create merge commits, alter shell startup files, install hooks, or change PATH.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For a successful migration, include the managed install path and remind that the original zip install was left unchanged.
- For a successful update, include the resulting version or commit and the next verification suggestion.
