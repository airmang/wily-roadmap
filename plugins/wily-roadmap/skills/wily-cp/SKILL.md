---
name: wily-cp
description: Use when recording or importing Wily checkpoint progress for a task.
---

# Wily CP

Record checkpoint progress in `.wily/tasks/<id>/progress.jsonl` so `wily watch` can render checkpoint bars and current cp state.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py cp <task-id> <start|done|note|import-status> <cp-or-status-path> [--note TEXT] [--actor ID]
```

## Behavior

- State-changing: appends checkpoint events to the task `progress.jsonl`.
- Use `wily cp <id> start <cp>` when a custom-workflow checkpoint starts.
- Use `wily cp <id> done <cp>` when that checkpoint passes verification.
- Custom Workflow interface contract: custom-workflow does not update Wily by itself; `wily cp` closes the cp automation gap for checkpoint sync.
- Use `wily cp <id> import-status .wily/handoffs/<id>/status.md` to backfill checkpoint events from a custom-workflow status board.
- The equivalent template path is `.wily/handoffs/<task-id>/status.md`.
- Use import-status as the recovery path when the status board exists but start/done checkpoint calls were missed.
- Custom Workflow interface contract: this command is the manual bridge for the cp automation gap.
- `wily cp <id> import-status` reads `.wily/handoffs/<id>/status.md` by default.
- Import is idempotent for existing checkpoint/event pairs.
- Parent-owned coordination mode is active when `.wily/coordination.yaml`
  exists. Import into the parent task progress ledger; JSON project views expose
  `active_mode`.
- In parent-owned coordination mode, `.wily/coordination.yaml` keeps checkpoint
  events on the parent task ledger, and status-style JSON views expose
  `active_mode`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the task id, cp action, and next action or blocker.
- Do not echo internal helper commands in normal user-facing responses.
