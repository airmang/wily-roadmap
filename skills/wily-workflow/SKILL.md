---
name: wily-workflow
description: Use when the user wants Wily's personal Codex workflow for software work: initialize or inspect per-repo .wily state, turn a large goal into dependency-aware roadmap phases, choose the next safe phase, execute a phase through an auditable session, revise future roadmap work, summarize progress, or keep remote/destructive actions approval-first.
metadata:
  short-description: Wily roadmap workflow for Codex
---

# Wily Workflow

## Purpose

Use this skill to manage large software work with Wily's local roadmap model. Wily stores project state in `.wily/`, splits large goals into Codex-sized phases, tracks dependencies and parallel candidates, records each execution attempt as a session, and preserves completed history when plans change.

Wily owns the Roadmap Plan. External planners may own detailed Phase Implementation Plans. Do not duplicate specialized implementation planning workflows inside Wily when a phase can be handed to a planner such as `superpowers:writing-plans`.

## First Move

1. Read every applicable `AGENTS.md`.
2. Inspect the target repo docs, source layout, and current `git status --short`.
3. If `.wily/` exists, summarize it with:

   ```bash
   python3 <plugin-root>/scripts/wily_state_summary.py
   ```

4. Classify the request:
   - `direct_work`: small local change or explanation; handle normally with verification.
   - `init_roadmap`: create `.wily/` project state and roadmap phases.
   - `show_status`: summarize roadmap state, blockers, and ready phases.
   - `select_phase`: recommend the next executable phase.
   - `execute_phase`: run one approved phase through a session.
   - `replan_roadmap`: revise future phases from the current implementation baseline.

## Core Commands

Use `$wily-workflow` as the general router when the right command is unclear. Prefer precise command skills when the user knows the intended action:

```text
$wily-init
$wily-status
$wily-next
$wily-start <phase-id>
$wily-complete <phase-id>
$wily-block <phase-id> "<reason>"
$wily-retry <phase-id>
$wily-replan
```

For deterministic local state operations, use the helper script:

```bash
python3 <plugin-root>/scripts/wily.py <command>
```

The script handles repeatable filesystem work such as `init`, `status`, `next`, `start`, `complete`, `block`, `retry`, `replan`, and one-shot `watch` rendering. Codex still owns interpretation, user approval, phase design, planner selection, implementation, and verification.

`$wily-init` scans the repository. If the user already provided a final goal, combine that goal with the scan. If not, summarize the current implementation first, then ask for the intended final outcome before creating a roadmap.

`$wily-next` shows the recommended ready phase, its dependencies, expected files, planner adapter, prompt, and verification. Ask before implementation.

`$wily-start <id>` records an approved phase execution session and marks the phase `in_progress`. Do not run it until the user approved starting that phase.

`$wily-complete <id>` marks a phase `done` after verification evidence and review requirements are satisfied.

`$wily-block <id>` records a blocker in roadmap state and the current session.

`$wily-retry <id>` creates a new execution session without deleting prior attempts.

`$wily-replan` keeps completed phases as history and revises only future or in-progress work unless the user explicitly requests a deeper reset.

## State Model

Each project owns this local state:

```text
.wily/
  project.md
  roadmap.yaml
  status.md
  decisions.md
  phases/
    <phase-id>-<slug>/
      phase.md
      planner.md
      prompt.md
      verification.md
      handoff.md
      plan.md
      notes.md
  sessions/
    <timestamp>-phase-<id>-attempt-<n>/
      input.md
      result.md
      verification.md
      changed-files.md
      status.yaml
  revisions/
    <date>-replan-<n>.md
```

Phase IDs may be sequential (`01`, `02`, `03`) or grouped (`04-1`, `04-2`, `04-3`) to show related work that can run in parallel after shared dependencies finish.

Supported phase statuses:

```text
pending
ready
in_progress
needs_review
done
blocked
superseded
```

## Operating Rules

- Prefer local completion. Do not push, open PRs, merge, delete user work, or run destructive commands unless the user explicitly asks.
- Before implementation, name the phase and the files or modules you expect to touch.
- If a detailed implementation plan is needed, use the phase's planner adapter before implementation.
- Implement only the approved phase. Do not silently advance into other phases.
- Keep phase and session separate: the phase is the planned work; the session is one execution attempt.
- A phase can have multiple sessions. Retry by creating a new session, not by overwriting old history.
- Run concrete verification before claiming success.
- If verification fails for an unclear reason, mark the session `needs_work` or the phase `blocked` and report the blocker.
- Before committing, summarize the diff and wait for explicit commit instruction unless the user asked for commits up front.

## Replanning Rules

- Completed phases remain history.
- Do not delete completed phases or silently move them back to pending.
- Revise, replace, split, remove, or supersede future phases as needed.
- Pause, block, or supersede in-progress phases when the target changes.
- If completed work no longer fits the target, add an adaptation phase instead of rewriting history.
- Record major changes in `.wily/revisions/`.

## References

Read detailed policy only when needed:

- Roadmap routing and command classification: `references/routing-policy.md`
- Phase and roadmap structure: `references/planning-style.md`
- Phase/session execution: `references/commit-policy.md`
- Remote and destructive action policy: `references/pr-policy.md`

## Response Style

- Be direct and concrete.
- Lead with current state, next action, and blockers.
- Use Korean when the user is speaking Korean, but keep file content and machine-facing markers in English.
