---
name: wily-retry
description: Use when the user types $wily-retry or wants to create a new attempt for an unfinished Wily phase.
metadata:
  short-description: Retry a Wily phase
---

# Wily Retry

Use `$wily-retry <phase-id>` to create a new session attempt for an unfinished phase.

This is state-changing. It preserves prior attempts, creates the next attempt session, and marks the phase `in_progress`.

## Command

```bash
python3 <plugin-root>/scripts/wily.py retry <phase-id>
```

## Boundaries

- Do not delete or overwrite prior sessions.
- Read the new `session/input.md` before continuing.
- Keep the new attempt scoped to the same phase unless the roadmap is explicitly replanned.
