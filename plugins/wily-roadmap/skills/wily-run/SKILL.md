---
name: wily-run
description: Use when the user types $wily-run to prepare a reference-only external workflow handoff without completing the phase.
metadata:
  short-description: Prepare a Wily phase handoff
---

# Wily Run

Use `$wily-run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]` to prepare a selected Wily phase as a reference-only external workflow handoff.

This is state-changing. It may start or attach to a Wily execution session and creates external workflow handoff artifacts. It must not mark the phase `done`. Final completion remains a separate verified `$wily-complete <phase-id>` action.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]
```

## Arguments

- `<phase-id>` is required.
- `--runner <external-workflow-id>` optionally names an external workflow such as Custom Workflow.
- `--autonomy conservative|goal_scoped|yolo` optionally labels the requested autonomy mode.

## Handoff Responsibilities

`$wily-run` should:

- read applicable `AGENTS.md`
- read `.wily/roadmap.yaml`
- validate that the phase exists and is executable
- record the external workflow id and autonomy mode
- start or attach the Wily session
- build a concise phase context handoff
- write `agent-handoffs/<phase-slug>-external-workflow.md`
- write `.wily/sessions/<session>/external-workflow-handoff.md`
- create review handoff guidance for `needs_review`, `blocked`, and verified completion
- include an exact `/goal` command when the runtime cannot set it directly
- stop after dispatch unless the runtime can safely continue inside an active goal
- never mark the Wily phase `done`

The handoff does not execute Custom Workflow, does not execute any other external workflow, and does not require bundled runner files. An external workflow may recommend `needs_review`, `blocked`, `ready`, or `done`, but Wily completion still requires verification evidence and `$wily-complete`.

## Boundaries

The implementation prepares reference-only handoff artifacts and stops. It does not execute the external workflow, run verification, or complete the Wily phase. External workflow progress can be copied into the Wily session later when `$wily-block` or `$wily-complete` records the final state.

## Autonomy Policy

- `conservative`: remote actions and destructive actions require explicit approval.
- `goal_scoped`: local phase-scoped implementation and verification may continue; remote and destructive actions still require explicit approval.
- `yolo`: use only when explicitly requested for a safe repository; hard stops still apply for broad destructive commands, payments, credential exposure, forbidden actions, and repeated verification failure without new evidence.

Remote actions and destructive actions remain approval-first in every mode.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Report the phase id, selected external workflow, selected autonomy mode, and whether handoff is available.
- Report the session path, handoff path, and exact native goal command when handoff succeeds.
- Tell the user that `$wily-run` does not complete the phase; use `$wily-complete <phase-id>` only after verification evidence exists.
