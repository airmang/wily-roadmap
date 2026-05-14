---
name: wily-retry
description: Use when the user types $wily-retry or wants to create a new attempt for an unfinished Wily phase.
metadata:
  short-description: Retry a Wily phase
---

# Wily Retry

Use `$wily-retry <phase-id>` to create a new session attempt for an unfinished phase.

This is state-changing. It preserves prior attempts, creates the next attempt session, and marks the phase `in_progress`.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py retry <phase-id>
```

## Boundaries

- Do not delete or overwrite prior sessions.
- Read the new `session/input.md` before continuing.
- Keep the new attempt scoped to the same phase unless the roadmap is explicitly replanned.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For a successful retry, include the phase id, new attempt/session path, and scoped next action.
