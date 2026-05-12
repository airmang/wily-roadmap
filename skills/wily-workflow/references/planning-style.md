# Planning Style

## Plan Levels

Wily has two plan levels:

- Roadmap Plan: Wily-owned project orchestration across all phases.
- Phase Implementation Plan: optional detailed execution plan for one phase, often produced by an external planner.

Keep Wily focused on the Roadmap Plan. Use planner adapters only when detailed phase implementation planning is worth the extra workflow overhead.

## Roadmap Format

Keep the machine-readable roadmap in `.wily/roadmap.yaml` and the human-readable phase details in `.wily/phases/`.

Example roadmap:

```yaml
roadmap_version: 1
goal: "Build the project to release-ready quality"
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

Status output may translate these markers for the user, but roadmap files should keep the English status values above.

## Phase Folder Format

Each phase should have:

```text
.wily/phases/<phase-id>-<slug>/
  phase.md
  planner.md
  prompt.md
  verification.md
  handoff.md
  plan.md
  notes.md
```

`phase.md` describes purpose, dependencies, parallel group, expected starting state, expected output, likely touched files, and known risks.

`planner.md` recommends how to create the detailed implementation plan when one is needed. The first recommendation line may use an external planner name, for example:

```text
Recommended planner: superpowers:writing-plans
```

`plan.md` is optional. It contains implementation steps only after an external planner or a Wily-native future planner creates them. Command skills must not invoke planner adapters just because this file is absent.

`prompt.md` contains the execution prompt that can be reused in a later session.

`verification.md` lists concrete commands or manual checks.

`handoff.md` contains resume context and boundaries for future sessions.

`notes.md` records observations that do not belong in durable decisions.

## Phase Quality

Each phase should:

- be executable in one focused Codex session,
- have a clear behavioral outcome,
- list dependencies and parallel eligibility,
- include expected files or modules,
- include focused verification,
- include a planner recommendation only when detailed implementation planning is expected,
- avoid unrelated refactors,
- avoid mixing planning changes with implementation changes.

## Parallel Work

Use parent-style IDs for related work that can run after the same dependency:

```text
04-1
04-2
04-3
```

Use `parallel_group: "04"` in `roadmap.yaml` to make that relationship explicit. Do not rely on folder names alone for execution order.

`$wily-status` shows the `Wily Roadmap` pane once. The pane keeps parallel phases near each other by stage, uses phase glyphs for status, and shows dependency hints such as `needs` instead of a prose-only summary. `$wily-watch` uses the same renderer continuously in a tmux pane.

## Replanning Style

When the target changes:

- preserve completed phases,
- revise future phases,
- supersede obsolete phases,
- create adaptation phases when completed work needs bridging,
- write a revision note under `.wily/revisions/`.

Use replacement metadata for revised work:

```yaml
id: "04R"
title: "Adapt completed foundation to revised direction"
status: "ready"
depends_on: ["03"]
replaces: ["04"]
```
