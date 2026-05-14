---
name: wily-replan
description: Use when the user types $wily-replan or wants to revise future Wily roadmap phases after progress or goal changes.
metadata:
  short-description: Replan future Wily phases
---

# Wily Replan

Use `$wily-replan` to revise the Roadmap Plan from the current implementation baseline.

This is state-changing. It increments the roadmap version and records a revision note.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py replan "<reason>"
```

## Rules

- Preserve completed phases as history.
- Do not move completed phases back to pending silently.
- Revise, replace, split, remove, or supersede future phases.
- Add adaptation phases when completed work needs bridging.
- Record the reason under `.wily/revisions/`.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For a successful replan, include the new roadmap version or revision path and the next review action.
