---
name: wily-next
description: Use when the user types $wily-next or asks which Wily phase should run next.
metadata:
  short-description: Show next ready Wily phase
---

# Wily Next

Use `$wily-next` to recommend the next executable phase and show its context bundle.

This is read-only. It must not mark a phase `in_progress` or create a session.

## Command

```bash
python3 <plugin-root>/scripts/wily.py next
```

## Report

- next executable phase, including `pending` phases whose dependencies are `done`
- dependency status
- phase definition
- planner adapter
- prompt
- verification
- handoff context
- whether an optional `plan.md` already exists

Tell the user to open a new session and run `$wily-start <phase-id>` when they are ready to execute the phase.
Do not invoke the planner adapter while handling `$wily-next`; it is context for a later implementation step.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
