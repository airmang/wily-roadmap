---
name: wily-start
description: Use when the user types $wily-start and explicitly approves opening a tracked Wily phase session.
metadata:
  short-description: Start a Wily phase session
---

# Wily Start

Use `$wily-start <phase-id>` to open a tracked execution session for an approved phase.

This is state-changing. It creates a session, marks the phase `in_progress`, records the phase context bundle, and increments the attempt number.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py start <phase-id>
```

## Boundaries

- $wily-start is session bookkeeping only.
- Run only when the user explicitly chooses to start a phase session.
- Prefer starting in a fresh agent session.
- In shared Wily repositories, treat start as a phase claim. Before starting, prefer a fresh pull or clearly note if remote state was not checked.
- After start, read the generated `session/input.md`.
- Report the session path and immediate next action, then stop.
- If `.wily/roadmap.yaml` is shared through Git, tell the user that the `in_progress` roadmap change should be committed/pushed when they want collaborators to see the claim. Do not push unless explicitly asked.
- Do not continue into implementation in the same turn.
- A separate explicit user request after the start result is required before implementation.
- Do not create or update implementation plans.
- Do not edit phase target files.
- Do not run verification for the phase implementation.
- Do not invoke phase planner adapters while handling the start command.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For a successful start, include the phase id, `Session:` path, and one immediate next action, then stop.
