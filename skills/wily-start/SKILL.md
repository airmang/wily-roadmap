---
name: wily-start
description: Use when the user types $wily-start and explicitly approves starting a tracked Wily phase execution attempt.
metadata:
  short-description: Start a Wily phase session
---

# Wily Start

Use `$wily-start <phase-id>` to start a tracked execution attempt for an approved phase.

This is state-changing. It creates a session, marks the phase `in_progress`, records the phase context bundle, and increments the attempt number.

## Command

```bash
python3 <plugin-root>/scripts/wily.py start <phase-id>
```

## Boundaries

- Run only when the user explicitly chooses to execute the phase.
- Prefer starting in a fresh Codex session.
- After start, read the generated `session/input.md`.
- Use the recommended planner from `planner.md` when a detailed implementation plan is needed.
- Implement only this phase.
