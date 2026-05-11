---
name: wily-start
description: Use when the user types $wily-start and explicitly approves opening a tracked Wily phase session.
metadata:
  short-description: Start a Wily phase session
---

# Wily Start

Use `$wily-start <phase-id>` to open a tracked execution session for an approved phase.

This is state-changing. It creates a session, marks the phase `in_progress`, records the phase context bundle, and increments the attempt number.

## Command

```bash
python3 <plugin-root>/scripts/wily.py start <phase-id>
```

## Boundaries

- $wily-start is session bookkeeping only.
- Run only when the user explicitly chooses to start a phase session.
- Prefer starting in a fresh Codex session.
- After start, read the generated `session/input.md`.
- Report the session path and immediate next action, then stop.
- Do not continue into implementation in the same turn.
- A separate explicit user request after the start result is required before implementation.
- Do not create or update implementation plans.
- Do not edit phase target files.
- Do not run verification for the phase implementation.
- Do not invoke phase planner adapters while handling the start command.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
