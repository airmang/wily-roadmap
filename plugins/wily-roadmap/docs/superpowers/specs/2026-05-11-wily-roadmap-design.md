# Wily Roadmap Design

## Purpose

Wily is a personal Codex workflow plugin for managing large project plans inside each target repository. It stores project state in a local `.wily/` directory, turns broad goals into executable phases, tracks dependency order, and keeps execution history separate from planning.

The plugin must not depend on or expose any external workflow brand, naming, or state model. All user-facing concepts use Wily terminology.

## Core Scenario

The main entry point is `wily init`.

If the user provides a goal, Wily combines that goal with a repository scan:

```text
wily init "Build the app to release-ready quality"
```

If the user does not provide a goal, Wily first scans the repository, summarizes the current implementation state, then asks the user for the intended final outcome:

```text
wily init
```

In both modes, Wily produces a project roadmap that starts from the current implementation baseline and breaks the remaining work into Codex-sized phases.

## Plan Levels

Wily separates project planning from phase implementation planning.

The Roadmap Plan is Wily's core responsibility. It defines the final goal, current baseline, phase graph, dependency order, parallel candidates, progress state, and revision history.

The Phase Implementation Plan is not Wily's core responsibility at first. A phase may delegate detailed implementation planning to an external planner such as `superpowers:writing-plans` or another Codex workflow. Wily records the selected planner, passes phase context to it, and stores execution results in sessions.

This keeps Wily focused on project orchestration instead of duplicating specialized implementation planning workflows.

## Local State

Each project owns its workflow state:

```text
.wily/
  project.md
  roadmap.yaml
  status.md
  decisions.md
  phases/
  sessions/
  revisions/
```

`project.md` describes the project, current baseline, final goal, major constraints, and important repository facts.

`roadmap.yaml` is the machine-readable source of truth for phase IDs, status, dependency edges, parallel groups, replacement relationships, and current roadmap version.

`status.md` is the human-readable summary of current progress, ready work, blocked work, and recommended next actions.

`decisions.md` records durable decisions that should affect future planning.

`phases/` contains one folder per planned work unit.

`sessions/` contains execution attempts. A phase can have multiple sessions.

`revisions/` records roadmap changes after the initial plan.

## Phase Model

A phase is a planned unit of work sized for one focused Codex implementation pass. It is smaller than a project milestone and larger than an individual edit.

Example phase layout:

```text
.wily/phases/04-1-settings-screen/
  phase.md
  planner.md
  prompt.md
  verification.md
  handoff.md
  plan.md
  notes.md
```

Each phase records:

- purpose
- expected starting conditions
- dependencies
- parallel group, if any
- likely files or modules touched
- planner recommendation
- optional implementation plan
- execution prompt
- completion criteria
- verification command or manual check
- known risks

`plan.md` is optional. It may be created by an external planner when a phase needs a detailed implementation checklist. Wily should not require it before a phase can start.

Phase IDs support both sequential and grouped work:

```text
01
02
03
04-1
04-2
04-3
05
```

Sequential IDs represent ordered work. Child IDs such as `04-1`, `04-2`, and `04-3` represent related work that can often be run in parallel after a shared dependency is complete.

## Roadmap Graph

The roadmap is a dependency graph, not just a numbered list.

Example:

```yaml
roadmap_version: 1
phases:
  - id: "01"
    title: "Current implementation audit"
    path: "phases/01-current-implementation-audit"
    status: "done"
    depends_on: []
    parallel_group: null

  - id: "04-1"
    title: "Settings screen"
    path: "phases/04-1-settings-screen"
    status: "ready"
    depends_on: ["03"]
    parallel_group: "04"

  - id: "04-2"
    title: "Keybinding editor"
    path: "phases/04-2-keybinding-editor"
    status: "ready"
    depends_on: ["03"]
    parallel_group: "04"
```

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

Wily recommends the next phase by selecting ready phases whose dependencies are done. If multiple ready phases share no dependency conflicts, Wily may present them as parallel candidates.

## Session Model

Phase and session are separate concepts.

```text
Phase = planned work unit
Session = one execution attempt against a phase
```

Example session layout:

```text
.wily/sessions/2026-05-11-phase-04-1-attempt-1/
  input.md
  result.md
  verification.md
  changed-files.md
  status.yaml
```

A session records:

- phase ID
- start and end time
- planner used, if any
- prompt used
- implementation summary
- changed files
- verification result
- blocker, if any
- final session status

A phase can be retried by creating a new session instead of overwriting old history.

## Approval-First Execution

Wily does not automatically start implementation just because a phase is ready.

Default flow:

```text
wily next
-> show recommended phase
-> show phase plan and execution prompt
-> ask for approval
-> implement only after explicit approval
```

This keeps phase boundaries intentional and prevents large plans from silently drifting.

Remote or destructive actions also require explicit approval. Wily should remain local-first by default.

## Replanning

Roadmaps are revised from the current implementation baseline. Wily does not recreate the plan from phase 1 after progress has already been made.

If phases 01, 02, and 03 are done, replanning starts from the completed state:

```text
01 done
02 done
03 done
04+ eligible for revision
```

Rules:

- Completed phases are preserved as history.
- Completed phases are not deleted or silently returned to pending.
- Future phases may be revised, replaced, removed, or split.
- In-progress phases may be paused, blocked, or superseded.
- Major roadmap changes create a revision note.
- If completed work is no longer useful, add a new adaptation phase instead of rewriting history.

Example revision:

```yaml
roadmap_version: 2
phases:
  - id: "04R"
    title: "Adapt completed foundation to revised direction"
    status: "ready"
    depends_on: ["03"]
    replaces: ["04"]

  - id: "05"
    title: "Build revised execution flow"
    status: "pending"
    depends_on: ["04R"]
```

Revision notes live in `.wily/revisions/`:

```text
.wily/revisions/2026-05-11-replan-01.md
```

Each revision records:

- previous roadmap state
- reason for change
- completed phases kept
- phases revised or superseded
- new phases added
- user approval summary

## Visualization

Visualization starts as text output and can later grow into optional adapters.

Core visualization:

```text
Wily Roadmap

[01] Audit                  done
[02] Core model             done
[03] CLI base               done

Ready:
+-- [04-1] Settings screen
+-- [04-2] Keybinding editor
`-- [04-3] Import export

Blocked:
+-- [05] Packaging            blocked by 04-1, 04-2, 04-3
`-- [06] Release readiness    blocked by 05
```

Optional display commands can be added later:

```text
wily watch
wily tmux
```

`wily watch` continuously renders roadmap state from `.wily/roadmap.yaml`.

`wily tmux` detects an active tmux session, creates a bottom pane, and runs `wily watch` there. Tmux support is optional and must not be required for normal operation.

## Expected Commands

The plugin can start with natural-language Codex commands and later move repeated logic into scripts.

Target command vocabulary:

```text
wily init
wily status
wily next
wily phase <id>
wily start <id>
wily complete <id>
wily block <id>
wily retry <id>
wily replan
wily watch
wily tmux
```

Initial implementation should prioritize:

```text
wily init
wily status
wily next
wily replan
```

## Success Criteria

The workflow succeeds when:

- every project can keep independent `.wily/` state
- large goals become Codex-sized executable phases
- dependencies and parallel candidates are visible
- each phase has enough metadata to execute safely
- each execution attempt leaves an auditable session record
- replanning preserves completed history
- remote and destructive actions remain approval-first
- no external workflow naming leaks into user-facing files or prompts
