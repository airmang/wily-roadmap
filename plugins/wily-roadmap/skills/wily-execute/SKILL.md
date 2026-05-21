---
name: wily-execute
description: Use when the user asks an agent to execute a Wily task end-to-end via custom-workflow.
---

# Wily Execute

When the user says "T03 cw로 진행해줘" or asks to process the next Wily task, orchestrate the command sequence.

1. Run `wily status` or `wily next` to confirm the task.
2. Run `wily claim <id>` to record actor, timestamp, legacy claim SHA or
   coordination `claim_snapshot`, and progress file.
3. Run `wily go <id>` and pass the emitted block to `custom-workflow-skillset:plan-goal-runner`.
4. During custom-workflow, record every checkpoint in Wily with `wily cp <id> start <cp-name>` and `wily cp <id> done <cp-name>` so `.wily/tasks/<id>/progress.jsonl` drives `wily watch`.
5. Custom Workflow interface contract: custom-workflow does not update Wily by itself; the explicit `wily cp` calls close the cp automation gap between custom-workflow and the Wily task ledger.
6. If custom-workflow already produced a status board, run `wily cp <id> import-status .wily/handoffs/<id>/status.md` to backfill checkpoint progress into `.wily/tasks/<id>/progress.jsonl`.
   The equivalent template path is `.wily/handoffs/<task-id>/status.md`.
7. Use the import-status path as the recovery path when checkpoint calls were missed or when a custom-workflow handoff was produced first.
8. Use `Wily-Task: <id>` / `Wily-CP: <name>` commit trailers where commits are created.
9. Compare the result against task acceptance and report scope drift.
10. Run `wily done <id>` only after verification.
11. Run `wily land <id>` only after explicit user approval.

## Parent-Owned Coordination Mode

- `.wily/coordination.yaml` enables parent-owned coordination mode, where the
  parent `.wily/tasks.yaml` owns tasks and registered child repos are work
  targets.
- In this mode, `wily claim` records `claim_snapshot` instead of a fake parent
  `claim_sha`. The snapshot includes each repo's branch, sha, dirty files, and
  fingerprints for dirty or untracked files.
- Status-style JSON exposes `active_mode`; commands run inside a registered
  child repo with its own `.wily/` use that child-local project.
- Use `wily land --dry-run <id>` before coordination land. Mixed files block by
  default unless `--include-mixed` or `--include <repo:path>` explicitly includes
  them. Coordination land is local-only and `--push` is rejected.

## Custom Workflow interface contract

- custom-workflow does not update Wily by itself; this is the cp automation gap.
- Use `wily cp <id> import-status` to backfill from the default `.wily/handoffs/<id>/status.md` path.
- `.wily/handoffs/<task-id>/status.md` remains the explicit compatible path spelling in examples.

## Guardrails

- Never call `wily done` after a failed custom-workflow run.
- Never call `wily land` without explicit approval.
- For another actor's observed work, use `wily done <id> --observed` only when the user asks.

## Response Style

- Use Korean when the user is speaking Korean.
- Report the task id, current step, and next required action or blocker.
- Do not echo internal helper commands in normal user-facing responses.
