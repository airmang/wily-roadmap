---
name: wily-next
description: Use when the user types $wily-next or asks which Wily phase should run next.
metadata:
  short-description: Show next ready Wily phase
---

# Wily Next

Use `$wily-next` to recommend the next executable phase.

This is read-only. It must not mark a phase `in_progress` or create a session.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py next
```

## Report

- next executable phase id and title
- dependency status
- phase path
- whether an optional `plan.md` already exists
- one sentence naming the immediate user action

Do not paste the full phase context unless the user asks for details; provide the phase path so it can be inspected when needed.
Tell the user to open a new session and run `$wily-start <phase-id>` when they are ready to execute the phase.
Do not invoke the planner adapter while handling `$wily-next`; it is context for a later implementation step.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Include only the next phase id/title, dependency status, phase path, plan availability, and `$wily-start <phase-id>` as the user-facing next action.
