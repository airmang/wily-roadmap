# Planning Style

## Plan Levels

Wily has three plan levels:

- Roadmap Plan: Wily-owned project orchestration across all Stages.
- Stage Plan: optional Stage-local decomposition into Phases and lanes under `.wily/stages/<stage-id>/stage.yaml`.
- Phase Implementation Plan: optional detailed execution plan for one Phase, often produced by an external planner.

Keep Wily focused on the Roadmap Plan. Use `$wily-decompose-stage` only when a Stage owner explicitly wants internal Phases or lanes.

## Roadmap Format

Keep the machine-readable roadmap in `.wily/roadmap.yaml` and the human-readable Stage details in `.wily/stages/`. Existing phase-only roadmaps remain supported as legacy input.

Example roadmap:

```yaml
roadmap_version: 1
goal: "Build the project to release-ready quality"
stages:
  - id: "s01-audit"
    title: "Current implementation audit"
    path: "stages/s01-audit"
    status: "done"
    depends_on: []
    owner: "shared"
    write_scope: ["docs", "src"]
    execution_mode: "direct"
    decomposition_status: "none"

  - id: "s02-settings"
    title: "Settings screen"
    path: "stages/s02-settings"
    status: "ready"
    depends_on: ["s01-audit"]
    owner: "wily"
    write_scope: ["src/settings"]
    execution_mode: "direct"
    decomposition_status: "none"
```

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

Status output may translate these markers for the user, but roadmap files should keep the English status values above.

## Stage Folder Format

Each Stage should have:

```text
.wily/stages/<stage-id>-<slug>/
  stage.md
  prompt.md
  verification.md
  handoff.md
  notes.md
  stage.yaml
  phases/
```

`stage.md` describes purpose, dependencies, owner, `write_scope`, expected starting state, expected output, likely touched files, and known risks.

`stage.yaml` stores Stage-local child Phases and lanes after explicit decomposition. Keep these details out of `.wily/roadmap.yaml` to reduce collaboration conflicts.

## Phase Folder Format

When a Stage is decomposed, each child Phase should have:

```text
.wily/stages/<stage-id>-<slug>/phases/<phase-id>-<slug>/
  phase.md
  planner.md
  prompt.md
  verification.md
  handoff.md
  plan.md
  notes.md
```

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

Each Stage should:

- be executable directly by one owner unless explicitly decomposed,
- have a clear behavioral outcome,
- list dependencies, owner, and `write_scope`,
- include expected files or modules,
- include focused verification,
- avoid unrelated refactors,
- avoid mixing planning changes with implementation changes.

## Parallel Work

Use Stage DAG dependencies and `write_scope` for top-level parallel work:

```yaml
stages:
  - id: "s02-api"
    depends_on: ["s01-foundation"]
    owner: "wily"
    write_scope: ["src/server/api"]

  - id: "s03-ui"
    depends_on: ["s01-foundation"]
    owner: "right"
    write_scope: ["src/client/ui"]
```

Ready Stages with non-overlapping `write_scope` are candidates for parallel assignment. If `write_scope` overlaps or is unclear, create an integration Stage or keep the work sequential.

Stage-local lanes may use `write_scope` too, but those lanes are for a Stage owner to route through subagents after `$wily-decompose-stage`.

`$wily-status` shows the `Wily Roadmap` pane once. The pane keeps ready Stages visible, uses glyphs for status, and shows dependency hints such as `needs` instead of a prose-only summary. `$wily-watch` uses the same renderer continuously in a tmux pane.

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
