---
name: wily-workflow
description: "Use when the user wants Wily's personal agent workflow for software work: initialize or inspect per-repo .wily state, turn a large goal into dependency-aware roadmap phases, choose the next safe phase, execute a phase through an auditable session, revise future roadmap work, summarize progress, or keep remote/destructive actions approval-first."
metadata:
  short-description: Wily Roadmap workflow for agentic coding
---

# Wily Roadmap

## Purpose

Use this skill to manage large software work with Wily's local roadmap model. Wily stores project state in `.wily/`, splits large goals into Stage DAGs, tracks dependencies and parallel candidates, records each execution attempt as a session, and preserves completed history when plans change.

Wily owns the Roadmap Plan. Stage is the primary collaboration and merge-boundary unit. Phase is optional Stage-local decomposition created only by `$wily-decompose-stage`. Custom Workflow Skillset may own detailed Phase Implementation Plans and execution packages when a Stage or Phase truly needs one. `$wily-run` routes one selected Phase to `custom-workflow-skillset:plan-goal-runner`, with `custom-workflow-skillset:parallel-lane-runner` available only for approved bounded lanes. Wily still owns dependencies, attempts, status transitions, replans, and durable session history. Keep non-run command handling fast: Wily command skills should not invoke external planners or broad verification just to inspect, start, retry, block, or complete roadmap state.

When a repository shares Wily state through Git, Wily should guide collaborators toward a lightweight source-of-truth split: commit durable roadmap state, keep active execution sessions local, pull before claiming phases, and commit/push roadmap progress only when the user has approved remote work.

## First Move

1. Read every applicable `AGENTS.md`.
2. Inspect the target repo docs, source layout, and current `git status --short`.
3. If `.wily/` exists, summarize it with:

   ```bash
   python3 <plugin-root>/scripts/wily_state_summary.py
   ```

4. Classify the request:
   - `direct_work`: small local change or explanation; handle normally with verification.
   - `init_roadmap`: create `.wily/` project state and roadmap Stages.
   - `show_status`: summarize roadmap state, blockers, and ready Stages or legacy phases.
   - `select_phase`: recommend the next executable Stage or Phase.
   - `execute_phase`: run one approved Stage or Phase through a session.
   - `replan_roadmap`: revise future phases from the current implementation baseline.

## Core Commands

Use `$wily-workflow` as the general router when the right command is unclear. Prefer precise command skills when the user knows the intended action:

```text
$wily-init
$wily-status
$wily-watch
$wily-issues
$wily-next
$wily-start <phase-id>
$wily-decompose-stage <stage-id>
$wily-complete <phase-id>
$wily-block <phase-id> "<reason>"
$wily-retry <phase-id>
$wily-replan
$wily-run <phase-id>
```

For deterministic local state operations, use the helper script:

```bash
python3 <plugin-root>/scripts/wily.py <command>
```

The script handles repeatable filesystem work such as `init`, `status`, `next`, `start`, `complete`, `block`, `retry`, `replan`, and one-shot `watch` rendering. The active agent still owns interpretation, user approval, phase design, planner selection, implementation, and verification.

`$wily-init` scans the repository. If the user already provided a final goal, combine that goal with the scan. If not, summarize the current implementation first, then ask for the intended final outcome before creating a roadmap. New roadmaps should use top-level `stages:` with `depends_on`, `owner`, and `write_scope` so ready Stages can be assigned safely in parallel.

`$wily-next` shows the recommended executable Stage or legacy phase, including `pending` units whose dependencies are `done`, plus dependencies, expected files, prompt, and verification. Ask before implementation.

`$wily-status` renders the current `Wily Roadmap` pane once. It uses the same visual roadmap renderer as `$wily-watch`, including the progress bar, stage lines, phase glyphs, dependency hints, and git footer. Do not replace it with the fallback prose or stage-summary output.

`$wily-watch` renders the same `Wily Roadmap` pane in a continuously refreshing read-only view for tmux panes. It must not create sessions, change roadmap state, or implement phases.

`$wily-issues` explicitly inspects optional GitHub Issues linkage. Its default mode is read-only; approved local roadmap additions use Wily state only and do not write to GitHub.

`$wily-start <id>` records an approved Stage or Phase session and marks it `in_progress`. This command is session bookkeeping only: after reporting the session path, stop. Do not create plans, edit target files, run implementation verification, or continue into implementation in the same turn. A separate explicit user request after the start result is required before implementation.

`$wily-decompose-stage <id>` explicitly decomposes one Stage into Stage-local child Phases and optional lanes under `.wily/stages/<stage-id>/stage.yaml`. It must not run automatically from init or start. Use lane `write_scope` values to decide whether later subagent execution is parallel-safe.

`$wily-run <id>` records or attaches a Wily session, writes a Custom Workflow request/result artifact pair, and routes the active agent through `custom-workflow-skillset:plan-goal-runner`. If the generated execution package allows parallel lanes, route those bounded lanes through `custom-workflow-skillset:parallel-lane-runner`. The Custom Workflow result must be written to `custom-workflow-result.md` before `$wily-complete` or `$wily-block`.

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
  stages/
    <stage-id>-<slug>/
      stage.md
      prompt.md
      verification.md
      handoff.md
      notes.md
      stage.yaml
      phases/
        <phase-id>-<slug>/
          phase.md
          planner.md
          prompt.md
          verification.md
          handoff.md
          plan.md
          notes.md
  phases/
    <legacy-phase-id>-<slug>/
  sessions/
    <timestamp>-phase-<id>-attempt-<n>/
      input.md
      custom-workflow-request.md
      custom-workflow-result.md
      result.md
      verification.md
      changed-files.md
      status.yaml
  revisions/
    <date>-replan-<n>.md
```

In collaborative repositories, track durable project state (`roadmap.yaml`, `project.md`, `decisions.md`, `status.md`, `stages/**`, legacy `phases/**`, `revisions/**`) and keep active `.wily/sessions/**` local unless an explicit archive policy says otherwise.

Custom Workflow Skillset may be used as Wily's phase execution engine. Wily prepares the routing request with `$wily-run`, the active agent invokes the installed Custom Workflow skills, and Wily consumes the resulting `custom-workflow-result.md` during `$wily-complete` or `$wily-block`. The routing contract is documented in `references/runner-adapter-contract.md`.

Stage IDs should be stable and dependency-aware. Stage entries may include `owner` and `write_scope`; ready Stages with non-overlapping `write_scope` can be assigned in parallel. Legacy Phase IDs may be sequential (`01`, `02`, `03`) or grouped (`04-1`, `04-2`, `04-3`) to show related work that can run in parallel after shared dependencies finish.

Supported Stage and Phase statuses:

```text
pending
ready
in_progress
needs_review
done
blocked
superseded
```

Status summaries translate these markers only for display. Keep stored roadmap status values in English.

## Operating Rules

- Prefer local completion. Do not push, open PRs, merge, delete user work, or run destructive commands unless the user explicitly asks.
- Before implementation, name the Stage or Phase and the files or modules you expect to touch.
- In shared Wily repositories, remind the user to pull before claiming work and to keep code changes plus shared Wily state together in commits.
- If detailed internal breakdown is needed, use `$wily-decompose-stage` explicitly. Do not decompose automatically.
- Do not invoke planner adapters while merely handling `$wily-status`, `$wily-watch`, `$wily-next`, `$wily-start`, `$wily-retry`, `$wily-block`, or `$wily-complete`.
- Implement only the approved Stage or Phase. Do not silently advance into other units.
- Keep Stage/Phase and session separate: the Stage or Phase is the planned work; the session is one execution attempt.
- A Stage or Phase can have multiple sessions. Retry by creating a new session, not by overwriting old history.
- Run concrete, phase-scoped verification before claiming implementation success.
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
- Quiet user-facing responses: `references/response-style.md`
- Agent compatibility and Claude Code usage: `references/agent-compatibility.md`
- Optional GitHub Issues linkage: `references/github-issues-policy.md`
- Collaboration state sync: `references/collaboration-policy.md`
- External workflow reference: `references/runner-adapter-contract.md`

## Response Style

- Be direct and concrete.
- Lead with current state, next action, and blockers.
- Do not echo internal helper commands in normal user-facing responses.
- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Use Korean when the user is speaking Korean, but keep file content and machine-facing markers in English.
