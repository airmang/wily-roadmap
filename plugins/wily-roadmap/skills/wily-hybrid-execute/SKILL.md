---
name: wily-hybrid-execute
description: Use when the user asks an agent to execute a Wily task end-to-end with pi hybrid-harness/hybrid_run instead of custom-workflow. Claims the task, emits the Wily goal, runs hybrid_run, keeps checkpoints synced with wily cp, verifies acceptance, and closes only after verification.
---

# Wily Hybrid Execute

Use this when the user asks to process a Wily task with pi hybrid-harness or
`hybrid_run`, for example "T32 hybrid로 진행해줘".

## Workflow

1. Run `wily status` or `wily next` to confirm the task id, readiness, owner,
   scope, blockers, and active mode.
2. Run `wily claim <id>` to record actor, timestamp, legacy claim SHA or
   coordination `claim_snapshot`, and `.wily/tasks/<id>/progress.jsonl`.
3. Run `wily go <id>` and use the emitted goal block as the source of truth for
   the `hybrid_run` task.
4. Tell `hybrid_run` to respect Wily scope, acceptance criteria, and required
   verification. The harness must not call `wily done`, `wily land`, or push.
5. During hybrid-harness work, record every checkpoint in Wily with
   `wily cp <id> start <cp-name>` and `wily cp <id> done <cp-name>` so
   `.wily/tasks/<id>/progress.jsonl` drives `wily watch` and `wily-agent`.
6. If hybrid-harness produced a status board before checkpoint events were
   recorded, run `wily cp <id> import-status .wily/handoffs/<id>/status.md` to
   backfill checkpoint progress. The equivalent template path is
   `.wily/handoffs/<task-id>/status.md`.
7. Compare the result against task acceptance criteria, required checks, and
   task scope. Report scope drift instead of silently adopting it.
8. Run `wily done <id>` only after the hybrid run and verification pass.
9. Run `wily land <id>` only after explicit user approval. Use
   `wily land --dry-run <id>` first in parent-owned coordination mode.

## Hybrid Run Guidance

- Use `mode: default` for normal tasks.
- Use `mode: thorough` for shared crates, protocol/transport changes, or risky
  cross-repo coordination work.
- Use `mode: fast` only for small, low-risk edits.
- Keep Wily as the task ledger; hybrid-harness progress does not update Wily by
  itself.

## Parent-Owned Coordination Mode

- `.wily/coordination.yaml` enables parent-owned coordination mode, where the
  parent `.wily/tasks.yaml` owns tasks and registered child repos own work
  files.
- In this mode, `wily claim` records `claim_snapshot` instead of a fake parent
  `claim_sha`.
- Done and land compare later repo-qualified changes against that snapshot.
- Mixed files block by default during `wily land --dry-run <id>` unless the user
  explicitly includes them with `--include-mixed` or `--include <repo:path>`.
- Coordination land is local-only and `--push` is rejected.

## Guardrails

- Never call `wily done` after a failed `hybrid_run`.
- Never call `wily land` or push without explicit user approval.
- Do not let hybrid-harness mutate the Wily lifecycle directly; record Wily
  checkpoints explicitly with `wily cp`.
- Do not log screen contents, secrets, or keystrokes in status artifacts.
- Keep task scope and acceptance criteria ahead of opportunistic refactors.

## Response Style

- Use Korean when the user is speaking Korean.
- Report the task id, current step, checkpoint sync status, and next required
  action or blocker.
- Do not echo internal helper commands in normal user-facing responses.
