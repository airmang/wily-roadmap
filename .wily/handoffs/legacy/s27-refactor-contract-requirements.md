# Requirements Handoff: S27 Wily Roadmap Stage/Phase Contract Refactor

## Source Request

사용자는 Wily Roadmap을 누적 패치 구조에서 새 버전 수준으로 리팩토링하기를 원한다.

핵심 의도:

- Stage와 Phase 두 계층을 명확히 운영한다.
- Stage는 큰 흐름과 협업/집계 단위로 보고, Phase는 실제 실행 단위로 본다.
- 외부 플러그인인 Custom Workflow Skillset을 기본 실행 흐름으로 사용한다.
- Custom Workflow가 만드는 status board/checkpoint/progress 흐름을 Wily Phase 진행 현황과 결합한다.
- 그 결합 결과를 `wily-watch`와 웹 대시보드인 Wily Board 양쪽에 반영한다.
- Wily Board는 `wily-watch`의 상위 호환 웹 실시간 대시보드로 정의한다.
- Wily Roadmap은 개인 작업과 협업 작업의 Stage, Phase, 실행 상태, checkpoint, live session, 위험, 다음 작업을 모두 보여줄 수 있는 플러그인이 되어야 한다.

이번 산출물은 구현이 아니라 상세 요구사항/계약/분해 계획이다. 사용자는 이 문서를 Claude Opus 4.7에 교차 검토시킨 뒤, 검토 결과를 반영하여 `custom-workflow-skillset:plan-goal-runner`에 실행 패키지 생성을 맡길 예정이다.

## Desired Outcome

S27은 먼저 계약을 고정하고 구현을 분리한다.

목표 상태:

- Wily durable state는 `Stage -> Phase` 구조를 공식 모델로 가진다.
- Stage는 직접 실행하지 않는다. Stage는 큰 흐름, 협업 경계, dependency boundary, progress/risk 집계 단위다.
- Phase는 유일한 실행 단위다. `wily-run`, `wily-start`, `wily-complete`, `wily-block`, `wily-retry`는 Phase를 대상으로 한다.
- Custom Workflow Skillset은 Wily가 수정하지 않는 black-box runner다.
- Wily는 Custom Workflow의 기존 handoff/status/progress/verification/result artifacts만 읽고, 이를 Phase live overlay로 해석한다.
- Custom Workflow checkpoint는 durable `.wily` Phase로 materialize하지 않는다. Watch/Board에서 Phase 아래 임시 child row로 표시한다.
- `wily-watch`와 Wily Board는 같은 projection 모델을 사용한다. Watch는 터미널 축약판이고, Board는 multi-repo/read-only realtime web dashboard다.
- 상태 migration은 명시적 command로 수행한다. 사용자가 완성 후 각 코드 저장소에서 일괄 실행할 수 있어야 한다.

## In Scope

- Stage/Phase durable schema v2 계약 정의.
- Phase-only execution contract 정의.
- Stage status aggregate rule 정의.
- explicit local migration command 설계.
- Custom Workflow black-box adapter boundary 정의.
- checkpoint overlay contract 정의.
- Watch/Board shared projection contract 정의.
- Wily Board read-only dashboard scope 정의.
- S27을 실제 구현 가능한 Phase들로 세부 분해.
- Claude Opus 4.7 교차 검토에 필요한 review checklist 포함.
- Wily Roadmap repo와 Wily Board repo의 구현 touchpoint 분리.

## Non-Goals

- Custom Workflow Skillset 플러그인을 수정하지 않는다.
- Custom Workflow의 checkpoint 생성 방식, status board template, goal runtime, progress file policy를 변경하지 않는다.
- Board를 durable source of truth로 만들지 않는다.
- Board에서 Phase/Stage 상태를 직접 변경하는 mutation UI를 만들지 않는다.
- 새 hooks, MCP servers, app integrations를 추가하지 않는다.
- production deploy, remote push, GitHub mutation, destructive cleanup은 명시적 승인 없이 하지 않는다.
- 완료된 S01-S24의 Git history를 재작성하지 않는다.
- migration command가 기본 동작으로 legacy files를 삭제하지 않는다.

## Decision Boundaries

- Goal-scoped local design, documentation, tests, and implementation planning may proceed during later `plan-goal-runner` execution.
- Remote actions remain approval-first: push, PR creation/update, merge, production deploy, GitHub issue mutation, GitHub comments.
- Destructive actions remain approval-first: deleting `.wily` history, deleting legacy phase folders, overwriting user state, database destructive migrations.
- Secrets and credentials must never be copied into tracked files.
- Board live config remains local/env/user config only.
- Custom Workflow must be treated as an external black box. Wily may adapt to its artifacts, not require changes inside that plugin.
- The explicit migration command may create backups and reports without additional approval. It must require an explicit flag for irreversible cleanup.

## Acceptance Criteria

Contract-level acceptance:

- A reviewer can identify exactly what Stage means, what Phase means, and why Stage is not executable.
- The official durable model is `Stage -> Phase`; top-level `phases:` is legacy input only.
- All execution commands target Phase identity, not Stage identity.
- Stage status display is derived or normalized from child Phase status and Stage dependencies using documented rules.
- Custom Workflow remains unmodified and black-box.
- Custom Workflow checkpoint rows are shown as non-durable child rows under a Wily Phase in Watch/Board.
- Wily Board is read-only for roadmap state and does not become a mutation surface.
- Watch and Board consume the same projection semantics.
- Migration is explicit, local-first, reversible by backup, and suitable for user-run batch migration across repositories.

Implementation-readiness acceptance:

- S27 is decomposed into implementation Phases with dependencies, write scopes, expected touchpoints, and verification ideas.
- The plan identifies which changes belong in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` and which belong in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- The plan identifies test suites and smoke checks needed before calling the refactor complete.
- The plan includes a Claude Opus 4.7 review checklist and concrete questions.
- The plan includes migration safety requirements: dry-run, backup, report, validation, and optional approved legacy cleanup.

Behavioral acceptance for later implementation:

- `wily run <stage-id>/<phase-id>` routes the Phase through Custom Workflow by default.
- Passing a Stage id to execution commands fails with a clear message and suggests the next ready Phase or migration/decomposition action.
- Existing direct Stage work is converted by migration into at least one Phase.
- `wily-watch` renders Stage rows, Phase rows, and temporary checkpoint child rows from one projection model.
- Wily Board renders the same Stage/Phase/checkpoint topology in a web dashboard, including live overlays and checkpoint rows, without writing durable state.
- `wily checkpoint-sync <stage-id>/<phase-id>` can attach a Custom Workflow status board to a Phase overlay even when the Phase is Stage-local.
- No durable `.wily/stages/*/stage.yaml` Phase is created merely because a Custom Workflow checkpoint exists.

## Constraints

Compatibility:

- Existing installed plugin discovery must keep `.agents/plugins/marketplace.json` pointing to `./plugins/wily-roadmap`.
- Plugin manifest must remain at `plugins/wily-roadmap/.codex-plugin/plugin.json`.
- Command skills under `plugins/wily-roadmap/skills/` must remain compatible with Codex plugin discovery.
- Existing legacy phase-only repos are migration inputs, not ongoing official model targets.

Data integrity:

- Migration must support dry-run and report-only mode.
- Migration must write a backup or reversible snapshot before modifying `.wily`.
- Migration must produce a machine-readable and human-readable migration report.
- Migration must not silently delete `.wily/phases`, `.wily/sessions`, `.wily/revisions`, or `agent-handoffs`.
- Migration must preserve completed work evidence, session paths, verification files, and handoff references when possible.

UX:

- Korean human-readable Wily docs and prompts should remain Korean unless the user asks otherwise.
- Machine fields, status values, commands, ids, and file paths stay English.
- Watch remains useful in a terminal and should not require Board connectivity.
- Board remains useful as a web realtime dashboard and should not require local filesystem access.

Security and remote boundaries:

- Board event signing stays local/env configured.
- Production Board visual verification remains explicit when required by existing contract.
- No new app integration layer is added in S27.

Performance:

- Watch projection should be cheap enough for periodic refresh.
- Board live projection should avoid polling local developer machines.
- Migration should be usable across multiple repositories without requiring remote access.

## Repo Facts

Wily Roadmap marketplace/plugin facts:

- Root marketplace metadata exists at `.agents/plugins/marketplace.json` and points to `./plugins/wily-roadmap`.
- Plugin manifest exists at `plugins/wily-roadmap/.codex-plugin/plugin.json` and exposes `skills: "./skills/"`.
- Plugin guide requires local-first/approval-first behavior, deterministic repeated logic in `scripts/`, and no hooks/MCP/app integrations unless explicitly asked.

Current Wily state facts:

- `.wily/roadmap.yaml` currently uses `roadmap_schema: "stage-v1"` with top-level `stages:`.
- Current S27 is `Wily Roadmap 대규모 리팩토링`, status `ready`, execution_mode `direct`, decomposition_status `none`.
- `.wily/stages/s27-wily-roadmap-large-refactor/stage.yaml` currently has no child phases.
- Existing state still includes legacy `.wily/phases/**` and many session artifacts, so migration must handle mixed history.

Code structure facts:

- `plugins/wily-roadmap/scripts/wily.py` is a monolith around 3,465 lines. It contains CLI dispatch, Board live config, live registry, checkpoint parsing, state mutation commands, watch launch, hooks, update flow, and migration-adjacent logic.
- `plugins/wily-roadmap/scripts/wily_watch_ui.py` renders the terminal dashboard and reads local live registry overlays.
- `plugins/wily-roadmap/scripts/wily_state_summary.py` contains custom YAML-ish parsing, stage/phase summary, readiness logic, and Stage-local enrichment.
- `plugins/wily-roadmap/scripts/wily_runner.py` currently prepares Custom Workflow artifacts but only resolves top-level legacy phases through `wily.find_phase()`. It does not yet support Stage-local Phase execution.
- Tests with broadest contract coverage are `plugins/wily-roadmap/tests/test_wily_cli.py`, `test_wily_watch_ui.py`, `test_wily_state_summary.py`, and `test_wily_command_skills.py`.

Board facts from `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- Wily Board is a separate repository, not part of the marketplace plugin repo.
- Board already has durable tables for `repos`, `stages`, `phases`, live tables for `live_sessions`, `live_items`, and `live_drafts`.
- Board already accepts signed `/api/live/events` with `checkpoint` payloads and `stage_decomposed_local` draft topology.
- Board frontend already has TypeScript types for `Stage`, `Phase`, `LiveChip`, `CheckpointOverlay`, and a `StageMap` component.
- Board is documented as a lightweight dashboard where repository `.wily/` files remain source of truth.

Existing contract facts:

- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md` already says Custom Workflow owns implementation execution package/progress/verification, while Wily owns lifecycle and final transitions.
- Existing `checkpoint-sync` already parses Custom Workflow status boards and emits `checkpoint_updated` live events.
- Existing Board reflection contract already says local `.wily` state mutates first, Board projection is best-effort, and Board failures do not roll back local state.

## Target Architecture Contract

### Durable State Model

Official schema:

```yaml
roadmap_schema: "wily-roadmap-v2"
stages:
  - id: "s27"
    title: "Wily Roadmap 대규모 리팩토링"
    path: "stages/s27-wily-roadmap-large-refactor"
    status: "ready"
    depends_on: ["s24"]
    owner: "codex"
    write_scope:
      - "plugins/wily-roadmap/scripts"
      - "plugins/wily-roadmap/skills"
      - "plugins/wily-roadmap/tests"
```

Stage-local Phase state:

```yaml
stage_id: "s27"
schema: "wily-roadmap-v2"
phases:
  - id: "p01"
    title: "Stage/Phase contract and migration fixtures"
    status: "pending"
    depends_on: []
    owner: "codex"
    runner: "custom-workflow"
    path: "stages/s27-wily-roadmap-large-refactor/phases/p01-contract"
```

Rules:

- `.wily/roadmap.yaml` contains Stage list only.
- `.wily/stages/<stage-id>-<slug>/stage.yaml` contains child Phase list.
- `.wily/phases/**` is legacy input/archive after migration. New commands do not write new Phase folders there.
- New Phase IDs are Stage-local by default, for example `p01`, `p02`, `p03`.
- Canonical user-facing references use `<stage-id>/<phase-id>`, for example `s27/p01`.
- Migration preserves old single Phase IDs through an explicit mapping report when needed for sessions or Board data. It does not keep growing Phase IDs merely to make them repository-unique.
- Canonical identity for projections and Board payloads is `(repo, stage_id, phase_id)`.
- Backward-compatible live session lookup uses `(stage_id, phase_id)` plus migration mappings, not a repository-unique `phase_id` requirement.

### Stage Status Aggregate

Stage status is displayed from child Phase status plus Stage dependencies. Commands may store a normalized `status` on the Stage for compatibility, but v2 logic must recompute it after Phase mutations.

Aggregate rules:

- `superseded`: explicit Stage-level terminal override.
- `done`: all non-superseded child Phases are `done`.
- `in_progress`: any child Phase is `in_progress`.
- `blocked`: no child Phase is `in_progress` and at least one child Phase is `blocked`.
- `needs_review`: no child Phase is `in_progress` or `blocked` and at least one child Phase is `needs_review`.
- `ready`: Stage dependencies are done and at least one child Phase is executable.
- `pending`: dependencies are not done or no child Phase is executable.

Invalid state:

- A non-superseded Stage with no child Phases after migration is invalid for execution.
- `wily status` and `wily watch` may display invalid state, but execution commands must refuse it and suggest `wily decompose-stage <stage-id>` or `wily migrate-state`.

### Execution Contract

Phase-only commands:

- `wily start <stage-id>/<phase-id>`
- `wily run <stage-id>/<phase-id>`
- `wily complete <stage-id>/<phase-id>`
- `wily block <stage-id>/<phase-id> [reason]`
- `wily retry <stage-id>/<phase-id>`
- `wily release <stage-id>/<phase-id>`
- `wily live-heartbeat <stage-id>/<phase-id>`
- `wily live-worked <stage-id>/<phase-id>`
- `wily checkpoint-sync <stage-id>/<phase-id> --status-board <path>`

Stage-aware read commands:

- `wily status`
- `wily next`
- `wily watch`
- `wily board sync-local <stage-id>`
- `wily decompose-stage <stage-id>`

Execution rules:

- Passing a Stage id to a Phase-only command is an error.
- Error text must include the nearest ready Phase if known.
- Wily must not implicitly create a Phase because the user typed a Stage id.
- `wily next` should show both the next ready Stage and the next executable Phase inside that Stage.
- `wily run <stage-id>/<phase-id>` uses the default runner adapter `custom-workflow`.
- `wily run <stage-id>/<phase-id> --dry-run` verifies resolution/request generation without mutating durable state or creating a session.
- `--runner` remains as a registry key/alias, not as a reason to keep legacy runner behavior.

### Runner Adapter Contract

Wily owns adapter boundaries. Custom Workflow remains external.

Default adapter:

```text
runner: custom-workflow
engine: custom-workflow-skillset
primary_skill: custom-workflow-skillset:plan-goal-runner
parallel_skill: custom-workflow-skillset:parallel-lane-runner
```

Adapter responsibilities:

- Resolve Phase context from Stage-local durable state.
- Create or attach a Wily Phase session.
- Write request/result artifact targets in `agent-handoffs/` and `.wily/sessions/<session>/`.
- Print or record the exact Custom Workflow route.
- Locate Custom Workflow status/progress/verification/result artifacts.
- Parse status board checkpoint rows into Wily checkpoint overlay shape.
- Never mark a Wily Phase `done` just because Custom Workflow checkpoints are complete.

Adapter non-responsibilities:

- Modify Custom Workflow skill files.
- Modify Custom Workflow templates.
- Force Custom Workflow to use Wily's checkpoint IDs.
- Create durable Wily child Phases from Custom Workflow checkpoints.

### Checkpoint Overlay Contract

Custom Workflow checkpoint rows are non-durable child rows below a Wily Phase.

Overlay shape:

```json
{
  "source": "custom-workflow",
  "status_board": "agent-handoffs/s27-p04-status.md",
  "state": "RUNNING",
  "progress": {"done": 2, "total": 6, "percent": 33},
  "current": {"id": "CP03", "title": "Runner adapter registry", "status": "RUNNING"},
  "next": {"id": "CP04", "title": "Projection contract", "status": "PENDING"},
  "rows": [
    {"id": "CP01", "title": "Baseline tests", "status": "DONE", "owner": "root"},
    {"id": "CP02", "title": "Phase resolver", "status": "DONE", "owner": "root"}
  ],
  "current_action": "Implementing Stage-local Phase resolver",
  "blocker": "",
  "verification": {"status": "PASS", "evidence": "pytest target suite"}
}
```

Projection rules:

- Checkpoint rows are rendered under the owning Phase.
- Checkpoint rows have `is_durable: false`.
- Checkpoint rows do not affect Phase status by themselves.
- Phase status changes only through Wily lifecycle commands or migration/normalization.
- Watch may show compact checkpoint current/progress under a Phase when space is limited.
- Board may show expanded checkpoint rows under the Phase in repo detail and active work surfaces.

### Shared Projection Contract

Wily should introduce a stable internal projection model, tentatively named `RoadmapProjection`.

Projection inputs:

- durable `.wily/roadmap.yaml`
- durable `.wily/stages/*/stage.yaml`
- session status under `.wily/sessions/**`
- local live overlay under `.wily/local/live/**`
- Custom Workflow status board artifacts
- Board last emit cache under `.wily/local/board-last-emit.json`

Projection output:

```json
{
  "schema": "wily-roadmap-projection-v1",
  "repo": "owner/name",
  "generated_at": "2026-05-17T00:00:00Z",
  "stages": [
    {
      "stage_id": "s27",
      "title": "Wily Roadmap 대규모 리팩토링",
      "status": "in_progress",
      "aggregate": {"done": 2, "total": 8, "percent": 25},
      "depends_on": ["s24"],
      "owner": "codex",
      "write_scope": ["plugins/wily-roadmap/scripts"],
      "phases": [
        {
          "phase_id": "p04",
          "title": "Runner adapter registry",
          "status": "in_progress",
          "runner": "custom-workflow",
          "current_session": "sessions/...",
          "live_items": [],
          "checkpoint_overlay": {}
        }
      ]
    }
  ],
  "live_overlays": [],
  "warnings": []
}
```

Consumers:

- `wily status`: one-shot text summary from projection.
- `wily watch`: terminal dashboard from projection.
- Board event emitters: derive signed event payloads from projection or overlay deltas.
- Wily Board: render equivalent Stage/Phase/checkpoint topology from durable sync plus live events.

Board should not require local filesystem access. It can reconstruct the same semantics from imported `.wily` files and signed live events.

### Wily Board Contract

Board role:

- Read-only realtime dashboard.
- Multi-repo overview.
- Stage/Phase/checkpoint visualization.
- Live session and activity visualization.
- Risk/attention/next work visualization.

Board must not:

- write `.wily` files directly;
- become the roadmap source of truth;
- change Phase status from the UI in S27;
- require Custom Workflow changes.

Required Board display:

- Stage list/map with aggregate progress.
- Phase list under each Stage.
- Temporary checkpoint child rows under a live Phase.
- `local draft` or `awaiting push` labels for non-durable topology or live overlays.
- live activity freshness/stale state.
- checkpoint current/next/progress.
- read-only links to repo detail, Phase anchors, and relevant handoff artifacts when available.

## Explicit Migration Plan

Proposed command:

```bash
wily migrate-state --to wily-roadmap-v2 --dry-run
wily migrate-state --to wily-roadmap-v2 --apply
```

Optional cleanup, approval-first:

```bash
wily migrate-state --to wily-roadmap-v2 --prune-legacy
```

Migration phases:

1. Preflight
   - detect `.wily/roadmap.yaml`;
   - parse schema;
   - detect top-level `phases:`;
   - detect Stage-local `stage.yaml`;
   - detect sessions and current_session references;
   - detect duplicated Phase IDs;
   - detect dirty Git worktree and warn, but do not require remote operations.

2. Backup
   - write `.wily/backups/<timestamp>-wily-roadmap-v2/`;
   - copy roadmap, stage files, legacy phase metadata, and migration-relevant session status;
   - do not copy secrets from `.wily/local`.

3. Transform
   - ensure every non-superseded Stage has at least one Phase;
   - convert direct Stage into single child Phase;
   - move top-level legacy Phase metadata into Stage-local `stage.yaml`;
   - preserve session references;
   - preserve completed and blocked statuses;
   - write `roadmap_schema: "wily-roadmap-v2"`;
   - remove official top-level `phases:` from `roadmap.yaml`.

4. Report
   - write `.wily/migrations/<timestamp>-wily-roadmap-v2.md`;
   - write `.wily/migrations/<timestamp>-wily-roadmap-v2.json`;
   - include changed files, id mapping, unresolved warnings, and post-migration commands.

5. Validate
   - run parser/projection validation;
   - confirm no executable Stage without Phase exists;
   - confirm `wily status`, `wily next`, and `wily watch --once --ui ascii` can read the new state;
   - confirm `wily run <stage-id>/<phase-id> --dry-run` can resolve a Stage-local Phase without mutating durable state.

Legacy policy:

- After successful migration, `.wily/phases/**` is legacy archive only.
- Commands should not read `.wily/phases/**` unless an explicit legacy compatibility flag is used.
- Destructive removal is allowed only through an explicit cleanup flag and should be unnecessary for normal operation.

## S27 Proposed Phase Breakdown

These are proposed child Phases for `.wily/stages/s27-wily-roadmap-large-refactor/stage.yaml` after review. They are intentionally implementation-oriented so `plan-goal-runner` can convert them into execution packages later.

### s27/p01: Contract Freeze and Fixtures

- Goal: Turn this requirements handoff and review feedback into a final schema/projection/migration contract.
- Write scope:
  - `agent-handoffs/`
  - `docs/superpowers/specs/`
  - `plugins/wily-roadmap/skills/wily-workflow/references/`
- Depends on: none.
- Expected output:
  - final contract doc;
  - fixture examples for v1, mixed legacy, and v2 state;
  - agreed review resolution notes.
- Verification:
  - markdown self-review;
  - no unresolved blanks or vague markers;
  - Claude Opus 4.7 findings triaged.

### s27/p02: State Schema and Parser Boundary

- Goal: Extract/clarify state parsing and serialization boundaries for `wily-roadmap-v2`.
- Write scope:
  - `plugins/wily-roadmap/scripts/wily_state_summary.py`
  - possible new state module under `plugins/wily-roadmap/scripts/`
  - `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- Depends on: s27/p01.
- Expected output:
  - v2 schema parser;
  - Stage-local Phase enrichment;
  - invariant checks;
  - aggregate status calculation tests.
- Verification:
  - focused state summary tests;
  - parser fixture tests for legacy and v2 state.

### s27/p03: Explicit Migration Command

- Goal: Implement `wily migrate-state --to wily-roadmap-v2 --dry-run|--apply` with backup/report/validation.
- Write scope:
  - `plugins/wily-roadmap/scripts/wily.py`
  - migration helper module if extracted
  - `plugins/wily-roadmap/tests/test_wily_cli.py`
  - docs/skill command references
- Depends on: s27/p02.
- Expected output:
  - dry-run report;
  - apply mode;
  - backup directory;
  - migration report files;
  - validation failures with actionable messages.
- Verification:
  - migration fixture tests;
  - id mapping tests;
  - no default destructive cleanup.

### s27/p04: Phase-only Lifecycle Commands

- Goal: Make lifecycle execution commands resolve Stage-local Phases and reject Stage execution.
- Write scope:
  - `plugins/wily-roadmap/scripts/wily.py`
  - state helper module
  - lifecycle command skills
  - CLI tests
- Depends on: s27/p02.
- Expected output:
  - `start/run/complete/block/retry/release/live-*` Phase-only behavior;
  - clear Stage-id error messages;
  - Stage aggregate status recomputation after Phase mutation.
- Verification:
  - CLI tests for Stage rejection;
  - CLI tests for Stage-local Phase lifecycle;
  - watch/status behavior after Phase transition.

### s27/p05: Runner Adapter Registry and Custom Workflow Default

- Goal: Replace ad hoc `wily_runner.py` assumptions with a runner adapter boundary that supports Stage-local Phases.
- Write scope:
  - `plugins/wily-roadmap/scripts/wily_runner.py`
  - possible new adapter module
  - `plugins/wily-roadmap/skills/wily-run/SKILL.md`
  - runner contract reference
  - runner tests
- Depends on: s27/p04.
- Expected output:
  - default `custom-workflow` adapter;
  - `wily run <stage-local-phase-id>` support;
  - request/result artifact paths;
  - native route text for `custom-workflow-skillset:plan-goal-runner`;
  - no Custom Workflow plugin file edits.
- Verification:
  - runner request generation tests;
  - Stage-local Phase runner tests;
  - no bundled Custom Workflow implementation files.

### s27/p06: Projection Core

- Goal: Introduce shared `RoadmapProjection` semantics for status/watch/Board emitters.
- Write scope:
  - new projection helper module
  - `plugins/wily-roadmap/scripts/wily_watch_ui.py`
  - `plugins/wily-roadmap/scripts/wily.py`
  - watch/status tests
- Depends on: s27/p02, s27/p04, s27/p05.
- Expected output:
  - projection builder from durable state + live overlays;
  - checkpoint overlay attachment under Phase;
  - warnings for invalid state;
  - watch/status consumers updated to use projection.
- Verification:
  - render tests for Stage/Phase/checkpoint rows;
  - projection fixture tests;
  - `wily watch --once --ui ascii` smoke.

### s27/p07: Checkpoint Overlay and Board Event Contract

- Goal: Standardize `checkpoint-sync` and Board event payloads around `(stage_id, phase_id)` and temporary checkpoint rows.
- Write scope:
  - `plugins/wily-roadmap/scripts/wily.py`
  - Board reflection contract reference
  - Wily CLI/watch tests
  - coordinated contract notes for Wily Board repo
- Depends on: s27/p05, s27/p06.
- Expected output:
  - Stage-local `checkpoint-sync`;
  - checkpoint rows under Phase projection;
  - signed `checkpoint_updated` payload with stable shape;
  - Board recovery instructions.
- Verification:
  - checkpoint parser tests;
  - local live registry tests;
  - Board emit cache tests.

### s27/p08: Wily Board Read-only Projection Alignment

- Goal: Update `/Users/wilycastle/Code/projects/wily-plugin/wily-board` to render the new projection semantics as a web superset of Watch.
- Write scope:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/`
- Depends on: s27/p07 contract.
- Expected output:
  - read-only Stage/Phase/checkpoint dashboard;
  - checkpoint child rows under Phase;
  - live overlay display parity with Watch;
  - no Board durable mutation UI in S27.
- Verification:
  - Board API tests;
  - Board live event tests;
  - frontend type/render tests;
  - local server smoke if UI changes.

### s27/p09: Skills, Commands, Docs, and Cache Sync

- Goal: Align command docs, skill bodies, references, README, and plugin cache/update guidance with the new model.
- Write scope:
  - `plugins/wily-roadmap/skills/**`
  - `plugins/wily-roadmap/commands/**`
  - `plugins/wily-roadmap/README.md`
  - root `README.md`
  - command skill tests
- Depends on: s27/p03, s27/p05, s27/p07.
- Expected output:
  - concise skills;
  - detailed policy in references;
  - no stale Stage-direct execution language;
  - migration runbook.
- Verification:
  - `test_wily_command_skills.py`;
  - README/manual command review;
  - plugin manifest remains valid.

### s27/p10: End-to-end Migration and Dashboard Verification

- Goal: Prove the refactor with local fixtures and at least one representative migrated repo state.
- Write scope:
  - tests and verification handoffs;
  - no production deploy unless separately approved.
- Depends on: all prior S27 phases.
- Expected output:
  - migration dry-run/apply evidence;
  - watch/status/next/run/checkpoint-sync evidence;
  - Board local API/UI evidence if Board changes are included;
  - final risk register and follow-up list.
- Verification:
  - Wily targeted pytest suite;
  - py_compile for scripts;
  - `wily status`;
  - `wily next`;
  - `wily watch --once --ui ascii`;
  - Board tests in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`;
  - local E2E Board smoke when UI/API changes exist.

## Assumptions

- User wants a review-ready plan document now, not implementation.
- User will run the final migration command across their code repositories after implementation is complete.
- Custom Workflow Skillset is available as an installed external plugin during execution, but Wily must not modify it.
- Wily Board can be planned as a coordinated follow-up implementation in its own repo.
- Board production smoke remains approval-gated.
- The exact visual style of checkpoint child rows can be refined in the Board implementation Phase as long as the data contract remains stable.

## Decision Log

- Q1: selected contract-first implementation split. S27 should define shared contracts and migration plan before implementation.
- Q2: selected Phase execution model with Custom Workflow black-box constraint. Stage is flow/container; Phase is execution unit.
- Q3: selected temporary checkpoint child rows. Custom Workflow checkpoints are visual/live overlay rows, not durable Wily Phases.
- Q4: selected read-only Board. Board is a realtime dashboard, not a mutation surface.
- Q5: selected explicit migration command. User will later run migration across repositories.
- Q6: selected Phase-only execution. Direct Stage execution is removed from the target model.
- Q7: selected Custom Workflow default plus adapter registry. Custom Workflow is default runner, but Wily keeps a clear adapter boundary.
- Q8: selected durable `.wily` plus live overlay separation. Live/Board/Custom Workflow data does not replace durable state.
- Q9: selected shared projection model. `wily-watch` and Wily Board show the same projection semantics through different UIs.
- Q10: selected detailed review-ready plan. This handoff should be suitable for Claude Opus 4.7 cross-review before `plan-goal-runner` packaging.

## Superpowers Routing

Used:

- `superpowers:using-superpowers` was read as the discovery/process rule.
- `superpowers:brainstorming` was read because this is product/architecture design work.

Deep-interview remains the governing workflow for this turn. The deliverable is this requirements handoff under `agent-handoffs/`, not a committed Superpowers design doc, because the user explicitly requested `custom-workflow-skillset:deep-interview` and intends to route the reviewed result to `plan-goal-runner` later.

Skipped for now:

- `custom-workflow-skillset:plan-goal-runner`: intentionally deferred until after Claude Opus 4.7 review.
- `superpowers:writing-plans`: deferred because this handoff itself is the review input; the later execution package should fold reviewed phase breakdown into a plan.
- `superpowers:test-driven-development`: not applicable yet because no implementation is happening in this turn.
- `superpowers:verification-before-completion`: not applicable to implementation completion, but this handoff is self-reviewed below.

## Open Questions

These are not blockers for review, but should be checked before implementation:

- Should the migration command be top-level `wily migrate-state`, or should an alias under `wily update --migrate-state` be provided for discoverability?
- Should migrated direct Stages use Phase title `"<Stage title> implementation"` or preserve the Stage title exactly?
- Should Board detail pages show all checkpoint rows by default, or collapse completed checkpoint rows under a compact summary?

Accepted assumptions for planning:

- Use `wily-roadmap-v2` as the public schema name.
- Use `wily migrate-state` as the proposed command.
- Use Stage-local Phase IDs such as `p01`; use `<stage-id>/<phase-id>` as the canonical command/reference syntax.
- Preserve old single-ID references through migration mappings when safe.
- Keep checkpoint rows collapsible in UI, but visible enough to prove progress.
- Do not require `phase_id` to be repository-unique after migration.

## Likely Touchpoints

Wily Roadmap repo:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_runner.py`
- `plugins/wily-roadmap/scripts/wily_state_summary.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- possible new helper modules under `plugins/wily-roadmap/scripts/`
- `plugins/wily-roadmap/skills/wily-run/SKILL.md`
- `plugins/wily-roadmap/skills/wily-watch/SKILL.md`
- `plugins/wily-roadmap/skills/wily-start/SKILL.md`
- `plugins/wily-roadmap/skills/wily-complete/SKILL.md`
- `plugins/wily-roadmap/skills/wily-block/SKILL.md`
- `plugins/wily-roadmap/skills/wily-retry/SKILL.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/board-reflection-contract.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/planning-style.md`
- `plugins/wily-roadmap/commands/*.md`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- `plugins/wily-roadmap/tests/test_wily_command_skills.py`

Wily Board repo:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_parser.py`

## Verification Ideas

Wily Roadmap verification:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
```

Migration verification:

```bash
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run

# Apply mode is verified first against a disposable fixture copy, not the working repo.
tmp="$(mktemp -d)"
cp -R plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy "$tmp/project"
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --apply)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily status)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily next)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily run s27/p04 --dry-run)
```

Board verification, when Board repo changes are included:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
cd frontend
npm run lint
npm run build
```

Manual smoke ideas:

- Create a fixture repo with one direct Stage and verify migration creates one Phase.
- Create a fixture repo with legacy top-level phases and verify they become Stage-local.
- Create a Custom Workflow-like status board and run `checkpoint-sync` against a Stage-local Phase.
- Confirm Watch shows checkpoint child rows under the Phase.
- Confirm Board local API shows the same checkpoint overlay under the Phase.
- Confirm passing a Stage id to `wily run` fails and suggests a Phase.
- Confirm Board remains read-only for roadmap state.

## Claude Opus 4.7 Review Packet

Ask Claude Opus 4.7 to review this document as an architecture and migration plan, not as implementation code.

Suggested review prompt:

```text
Please review agent-handoffs/s27-refactor-contract-requirements.md as a senior architecture reviewer.

Context:
- Wily Roadmap is a local-first Codex plugin.
- Wily Board is a separate read-only realtime dashboard repo.
- Custom Workflow Skillset is an external black-box plugin and must not be modified.
- The goal is to make Stage -> Phase the official durable model, use Phase-only execution, and show Custom Workflow checkpoints as non-durable child rows under a Phase in Watch/Board.

Please check:
1. Is the Stage/Phase contract coherent and implementable?
2. Are the migration rules safe enough for existing repos with legacy `.wily/phases`, sessions, revisions, and handoffs?
3. Are Wily Roadmap and Wily Board ownership boundaries clear?
4. Does the plan accidentally require modifying Custom Workflow?
5. Are checkpoint overlay semantics clear enough to implement without making checkpoints durable Phases?
6. Are the proposed S27 Phases correctly ordered and scoped?
7. What acceptance criteria or verification steps are missing?
8. What are the top 5 risks before `plan-goal-runner` turns this into execution packages?

Return findings ordered by severity, then concrete recommended edits to the handoff.
```

Reviewer success condition:

- The reviewer can produce actionable findings without needing extra repository discovery.
- The reviewer can identify whether the contract is ready for `plan-goal-runner`.
- The reviewer can flag any hidden coupling to Custom Workflow or Board mutation behavior.

## Handoff Self-Review

- No implementation code was changed.
- The handoff records the user's explicit decisions.
- The plan avoids modifying Custom Workflow.
- The plan preserves Board as read-only projection.
- The migration plan is explicit and non-destructive by default.
- The implementation breakdown separates Wily Roadmap and Wily Board work.
- The document is ready to send to Claude Opus 4.7 for cross-review.
