# S27 Stage/Phase Contract Refactor Progress

## 2026-05-17T14:01:04Z - Package drafting initialized

- User requested `custom-workflow-skillset:plan-goal-runner`.
- Scope is package-only; no S27 implementation was started.
- Loaded plan-goal-runner workflow and Superpowers routing guidance.
- Loaded source handoffs:
  - `agent-handoffs/s27-refactor-contract-requirements.md`
  - `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`
- Loaded current S27 roadmap files under `.wily/stages/s27-wily-roadmap-large-refactor/`.
- Checked Wily Roadmap and Wily Board dirty-worktree state so the future `/goal` runner can preserve user/pre-existing changes.

Superpowers routing recorded:

- `Superpowers:using-superpowers` loaded as discovery rule.
- `Superpowers:writing-plans` loaded for plan granularity.
- Future implementation must use `Superpowers:test-driven-development` for behavior changes.
- Future failures must use `Superpowers:systematic-debugging`.
- Future completion must use `Superpowers:verification-before-completion`.

Package files initialized:

- `agent-handoffs/s27-refactor-execution-package.md`
- `agent-handoffs/s27-refactor-status.md`
- `agent-handoffs/s27-refactor-progress.md`
- `agent-handoffs/s27-refactor-verification.md`

Next step: run execution package validator and update status/verification with the result.

## 2026-05-17T14:01:04Z - Specialist review notes captured locally

Plan-goal-runner specialist intent was applied as local package gates:

- Repo explorer: inspected source docs, S27 roadmap files, Wily script/test touchpoints, and Wily Board dirty files.
- Parallel planner: classified S27 as `PARALLEL_SAFE_WITH_LIMITS`.
- Plan architect: separated durable state, migration, lifecycle, runner, projection, Board backend, Board frontend, docs, and final E2E.
- Plan critic: flagged breadth, cross-repo dirty state, and remote/destructive approval boundaries as the main risks.

No subagent implementation was started. No source files were edited beyond requested package handoffs.

Next step: validate `agent-handoffs/s27-refactor-execution-package.md`.

## 2026-05-17T14:05:36Z - Execution package validated

- Ran the plan-goal-runner validator.
- Result: PASS.
- Evidence: `PASS: execution package contract is complete.`

Command:

```text
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-refactor-execution-package.md
```

No S27 implementation started. Next step: user can enter the exact `/goal` command from the execution package.

## 2026-05-17T14:09:28Z - Native goal activated and CP01 started

- User explicitly requested S27 refactor completion.
- Created native goal: `Complete S27, the Wily Roadmap Stage/Phase contract refactor, according to agent-handoffs/s27-refactor-execution-package.md.`
- Re-read the execution package and required Superpowers method skills.
- Recorded current dirty worktree state as user/pre-existing changes to preserve.
- CP01 scope: close remaining design defaults and add contract/fixture artifacts before runtime behavior changes.

Auto-resolved under active /goal: Superpowers execution choice and approval prompts -> proceed checkpoint-by-checkpoint under `agent-handoffs/s27-refactor-execution-package.md` unless a narrow hard-stop condition is reached.

Next step: add final contract reference and v1/mixed/v2 fixture set, then run CP01 verification.

## 2026-05-17T14:11:24Z - CP01 complete

Files changed:

- `plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md`
- `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`
- `plugins/wily-roadmap/tests/fixtures/migration/v1-only/.wily/roadmap.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/v1-only/.wily/phases/01-audit/phase.md`
- `plugins/wily-roadmap/tests/fixtures/migration/v1-only/.wily/phases/02-build/phase.md`
- `plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy/.wily/roadmap.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy/.wily/stages/s01-foundation/stage.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy/.wily/stages/s02-refactor/stage.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy/.wily/phases/legacy-build/verification.md`
- `plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy/.wily/phases/legacy-refactor/handoff.md`
- `plugins/wily-roadmap/tests/fixtures/migration/already-v2/.wily/roadmap.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/already-v2/.wily/stages/s01-foundation/stage.yaml`
- `plugins/wily-roadmap/tests/fixtures/migration/already-v2/.wily/stages/s02-refactor/stage.yaml`
- `plugins/wily-roadmap/tests/fixtures/projection/v2-with-checkpoint-overlay/projection.json`

Implemented:

- Resolved the S27 open defaults:
  - direct Stage conversion keeps the Stage title exactly;
  - `/` redirects to `/me`;
  - Board live stale threshold is 15 minutes;
  - migration backups are retained indefinitely by default.
- Added a dedicated v2 Stage/Phase contract reference.
- Added migration fixtures for `v1-only`, `mixed-legacy`, and `already-v2`.
- Added a projection fixture with a non-durable Custom Workflow checkpoint overlay under `s27/p04`.

Commands:

```text
python3 -m json.tool plugins/wily-roadmap/tests/fixtures/projection/v2-with-checkpoint-overlay/projection.json >/dev/null
python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py
rg -n "TBD|TODO|implement later|fill in details|unresolved" plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md docs/superpowers/specs/2026-05-17-s27-refactor-design.md plugins/wily-roadmap/tests/fixtures || true
git diff --check -- plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md docs/superpowers/specs/2026-05-17-s27-refactor-design.md plugins/wily-roadmap/tests/fixtures
python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m py_compile plugins/wily-roadmap/scripts/wily_state_summary.py
```

Result:

- JSON fixture parse: PASS.
- `python3 -m pytest ...`: environment failure, `No module named pytest`; switched to `unittest` for CP01 because no runtime behavior depends on pytest.
- Command skill tests: 31 tests OK.
- State summary tests: 12 tests OK.
- Diff whitespace check: PASS.
- Placeholder scan: only the existing self-review sentence mentioning `TBD/TODO` as forbidden text was found.

Next step: CP02 TDD for v2 state parser and aggregate status boundaries.

## 2026-05-17T14:12:25Z - CP02 started

- Updating status board before code changes.
- TDD scope: add failing tests that require `wily-roadmap-v2` summary output to show Stage aggregate status from child Phases and next executable Phase identity as `<stage-id>/<phase-id>`.

Next step: run the new tests and confirm they fail for the intended missing v2 behavior.

## 2026-05-17T14:14:34Z - CP02 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- `plugins/wily-roadmap/scripts/wily_state_summary.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'v2'
```

Expected failure:

- `로드맵 스키마: wily-roadmap-v2` was missing.
- `다음 Phase: s02/p01 - Refactor` was missing.
- Stage status came from Stage row readiness instead of child Phase aggregate.

Implemented:

- `roadmap_schema` / v2 detection.
- Canonical child Phase identity `<stage-id>/<phase-id>`.
- Child Phase dependency resolution, including cross-Stage refs such as `s01/p01`.
- v2 Stage aggregate status from child Phases.
- v2 summary output with next Stage and next Phase.
- Child Phase rows under each v2 Stage.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'v2'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m py_compile plugins/wily-roadmap/scripts/wily_state_summary.py
```

Result:

- v2 targeted tests: 2 tests OK.
- Full state summary tests: 14 tests OK.
- py_compile: PASS.

Next step: CP03, implement `wily migrate-state --to wily-roadmap-v2` with dry-run/apply/prune guard using TDD.

## 2026-05-17T14:19:40Z - CP03 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/scripts/wily.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'migrate_state'
```

Expected failure:

- `migrate-state` was missing from command dispatch and usage.

Implemented:

- `wily migrate-state --to wily-roadmap-v2 --dry-run`.
- `wily migrate-state --to wily-roadmap-v2 --apply`.
- Explicit `--prune-legacy` mode, not used by tests or this goal.
- Backup writer under `.wily/backups/<timestamp>-wily-roadmap-v2/`.
- Human and machine migration reports under `.wily/migrations/`.
- Mixed legacy top-level Phase to Stage-local Phase mapping, for example `legacy-refactor -> s02/p01`.
- Dependency remapping from legacy Phase ids to `<stage-id>/<phase-id>`.
- Legacy `.wily/phases/**` preservation during apply.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'migrate_state'
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
```

Result:

- Migration targeted tests: 2 tests OK.
- py_compile: PASS.
- Full CLI tests: 135 tests OK, 1 skipped.

Next step: CP04, make lifecycle commands Phase-only for v2 and reject Stage ids with actionable next-Phase guidance.

## 2026-05-17T14:20:14Z - CP04 started

- Updating status board before lifecycle behavior changes.
- TDD scope: v2 lifecycle commands must reject Stage ids and accept canonical `<stage-id>/<phase-id>` Phase refs.

Next step: add red tests for Stage rejection and namespaced Phase start.

## 2026-05-17T14:23:50Z - CP04 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/scripts/wily.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'
```

Expected failure:

- `wily start s02` still started a Stage.
- `wily start s02/p01` could not resolve a Stage-local Phase.

Implemented:

- Namespaced Stage-local Phase lookup in `find_stage_phase`.
- v2 Stage execution rejection with `Next phase: <stage-id>/<phase-id>` guidance.
- v2-aware `save_stage_state` that preserves `schema: "wily-roadmap-v2"`.
- Namespaced display for v2 Stage-local lifecycle actions while preserving legacy decomposed Stage output.

Debugging note:

- Full CLI initially failed because non-v2 decomposed Stage output changed from `p02` to `s01/p02`. Root cause was display policy being applied too broadly. Fixed by using canonical refs only for v2 roadmaps or explicit namespaced requests.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'complete_stage_local_child_phase_updates_stage_state'
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
```

Result:

- v2 lifecycle targeted tests: 2 tests OK.
- legacy child complete regression: 1 test OK.
- py_compile: PASS.
- Full CLI tests: 137 tests OK, 1 skipped.

Next step: CP05, update runner adapter request generation to resolve Stage-local Phase refs and produce Custom Workflow plan-goal-runner routes without mutating durable state in dry-run.

## 2026-05-17T14:26:32Z - CP05 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/scripts/wily_runner.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_dry_run_resolves_v2'
```

Expected failure:

- `wily run s02/p01 --dry-run` failed with `Unknown option: --dry-run`.

Implemented:

- `--dry-run` support in `wily_runner.py`.
- Stage-local Phase resolver for `wily run <stage-id>/<phase-id>`.
- v2 Stage id rejection through the same lifecycle guard.
- Stage-local Phase executability using v2 child Phase dependency rules.
- Dry-run route output for `custom-workflow-skillset:plan-goal-runner` without writing sessions or handoffs.
- Non-dry-run session support for Stage-local Phases.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_dry_run_resolves_v2'
python3 -m py_compile plugins/wily-roadmap/scripts/wily_runner.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py -k 'wily_run'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
```

Result:

- v2 runner dry-run test: 1 test OK.
- py_compile: PASS.
- Existing run tests: 9 tests OK.
- Wily run command skill tests: 2 tests OK.
- Full CLI tests: 138 tests OK, 1 skipped.

Next step: CP06, introduce a shared projection builder and move Watch/status semantics toward Stage/Phase/checkpoint projection.

## 2026-05-17T14:28:34Z - CP06 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- `plugins/wily-roadmap/scripts/wily_projection.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'projection_builder'
```

Expected failure:

- `No module named 'wily_projection'`.

Implemented:

- `wily_projection.build_projection(root)` returning `wily-roadmap-projection-v1`.
- Stage rows with aggregate progress, dependencies, owner, write scope, and child Phase rows.
- Phase rows with canonical `ref`, runner, session, dependencies, and checkpoint overlay.
- Non-durable Custom Workflow checkpoint overlay attachment from `.wily/local/live/active/*.json`.
- V2 Watch loader normalization through the same aggregate helpers used by state summary.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'projection_builder'
python3 -m py_compile plugins/wily-roadmap/scripts/wily_projection.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py
```

Result:

- Projection targeted test: 1 test OK.
- py_compile: PASS.
- State summary tests: 15 tests OK.
- Watch UI tests: 63 tests OK, 1 skipped.

Next step: CP07, standardize checkpoint-sync and Board payloads around `(stage_id, phase_id)` with non-durable checkpoint child rows.

## 2026-05-17T14:32:23Z - CP07 started

- Continued from the red checkpoint-sync test for v2 tuple identity and non-durable overlays.
- TDD scope: `checkpoint-sync <stage-id>/<phase-id>` must keep durable Phase state unchanged, write a local live overlay with `stage_id`/`phase_id`, mark the checkpoint source as `custom-workflow`, preserve the relative status-board path, and emit the same tuple payload to Board.

Next step: update the checkpoint status-board parser and run the targeted checkpoint-sync tests.

## 2026-05-17T14:33:31Z - CP07 complete

Files changed:

- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/scripts/wily.py`

Red test:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync_records_v2'
```

Expected failure:

- Checkpoint parser stored the status-board path as `checkpoint.source` instead of the runner source.

Implemented:

- Checkpoint status-board parser now emits `source: "custom-workflow"`.
- Parsed checkpoint overlays include `is_durable: false`.
- Parsed checkpoint overlays include a root-relative `status_board` artifact path when available.
- Existing `checkpoint-sync <stage-id>/<phase-id>` path writes tuple identity into the local live registry and emitted Board payload without mutating durable Phase status.

Green verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync_records_v2'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'projection_builder'
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_projection.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
```

Result:

- V2 checkpoint tuple test: 1 test OK.
- Checkpoint-sync tests: 2 tests OK.
- Projection checkpoint overlay test: 1 test OK.
- py_compile: PASS.
- Full CLI tests: 139 tests OK, 1 skipped.

Next step: CP08, align the Wily Board backend with `(repo, stage_id, phase_id)` identity and checkpoint overlays.

## 2026-05-17T14:36:54Z - CP08 started

- Entered `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- No repo-local `AGENTS.md` applies in Wily Board.
- Current Board worktree is dirty; treating those changes as user/pre-existing and preserving them.
- TDD scope: backend storage and API projection must distinguish duplicate Stage-local Phase ids by `(repo, stage_id, phase_id)`, keep checkpoint overlays read-only, and place live/checkpoint rows under only the owning Stage/Phase.

Next step: add red backend tests for tuple identity collisions and repo-detail overlay placement.

## 2026-05-17T14:43:29Z - CP08 complete

Files changed:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`
- `plugins/wily-roadmap/scripts/wily.py`

Red tests:

```text
uv run pytest tests/test_live_events.py -k 'duplicate_stage_local'
uv run pytest tests/test_api_routes.py -k 'owning_stage_phase'
```

Expected failures:

- Board `live_sessions` collapsed `s01/p01` and `s02/p01` because the unique key omitted `stage_id`.
- Repo detail grouped live/checkpoint overlays by bare `phase_id`, so an `s02/p01` checkpoint appeared under `s01/p01`.

Implemented:

- Board `live_sessions` schema and migration now use `UNIQUE(repo_id, stage_id, phase_id, actor, session_path)`.
- Board live/API/web projection maps now key live sessions and live items by `(stage_id, phase_id)`.
- Board claims endpoint accepts optional `stage_id`, and Wily claim lookup sends it for Stage-local Phase refs.
- Checkpoint validation recognizes `status_board` text and `is_durable` boolean metadata.
- Full Board tests were made deterministic where sync-health assertions depended on the wall clock.

Green verification:

```text
python3 -m py_compile app/db/repo.py app/live/events.py app/api/routes.py app/web/routes.py
uv run pytest tests/test_live_events.py
uv run pytest tests/test_api_routes.py
uv run pytest
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync'
```

Result:

- Board py_compile: PASS.
- Board live event tests: 12 passed.
- Board API route tests: 16 passed.
- Board full test suite: 94 passed, 37 warnings.
- Wily py_compile: PASS.
- Wily `v2_start`: 2 tests OK.
- Wily `checkpoint_sync`: 2 tests OK.

Next step: CP09, add Board `/me`, `/collab`, root redirect behavior, and shared chrome without mutating roadmap state.

## 2026-05-17T14:44:49Z - CP09 started

- CP09 scope: make `/` redirect to `/me`, add `/me` and `/collab` routes, and add shared web-native Board chrome with surface navigation and search.
- Existing frontend already has App Router pages, repo detail, command search, theme toggle, and compact dashboard components; changes will reuse those instead of adding a separate UI system.

Next step: add route files and shared chrome components, then run `npm run lint` and `npm run build`.

## 2026-05-17T14:46:33Z - CP09 complete

Files changed:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/me/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/collab/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/header.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/surface-nav.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

Implemented:

- `/` redirects deterministically to `/me`.
- `/me` and `/collab` are App Router surfaces.
- Shared top chrome now links brand to `/me`, keeps search/theme controls, and adds a compact surface switcher.
- Repo list has a stable `#repos` anchor for surface navigation.
- Mobile header wraps without overlapping the search/theme controls.

Verification:

```text
npm run lint
npm run build
```

Result:

- Frontend lint: PASS.
- Frontend production build: PASS. Routes generated: `/`, `/me`, `/collab`, `/repos/[owner]/[name]`, and `/api/repos`.

Next step: CP10, make `/me` and `/collab` distinct operational surfaces with expected personal/collaboration widgets.

## 2026-05-17T14:47:24Z - CP10 started

- CP10 scope: make `/me` and `/collab` meaningfully different surfaces instead of two copies of the same dashboard.
- `/me` will prioritize active personal work, next ready work, attention items, and repo grids.
- `/collab` will prioritize live activity, review/blocked queue, next collaboration action, and shared repo grid.

Next step: add reusable surface widgets and wire the two pages through them.

## 2026-05-17T14:49:42Z - CP10 complete

Files changed:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/me/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/collab/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/surface-widgets.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

Implemented:

- `/me` now prioritizes Active Phase, Next Ready Phase, Needs Attention, and personal/shared repo grids.
- `/collab` now prioritizes Live Activity, Review Queue, Next Collaboration Action, and shared repo grid.
- Added reusable surface widgets with compact rows, stable links into repo detail, and responsive layout.

Verification:

```text
npm run lint
npm run build
```

Result:

- Frontend lint: PASS.
- Frontend production build: PASS.

Next step: CP11, tighten repo detail around Stage/Phase/checkpoint topology and tuple-safe anchors.

## 2026-05-17T14:50:29Z - CP11 started

- CP11 scope: repo detail must make Stage/Phase/checkpoint topology explicit and avoid bare `phase_id` anchors that collide in v2.
- Existing detail already has Stage map, attention, phase list, and checkpoint rows; this checkpoint will make those rows tuple-safe and more legible.

Next step: add checkpoint row component, update PhaseList anchors/keys to `<stage-id>/<phase-id>`, and run frontend plus API regression checks.

## 2026-05-17T14:52:10Z - CP11 complete

Files changed:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/page.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/checkpoint-rows.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

Implemented:

- Repo detail Phase anchors now use `phase-<stage-id>-<phase-id>`.
- Desk/API links now target tuple-safe anchors.
- Phase rows display canonical `<stage-id>/<phase-id>` refs and dependencies.
- Checkpoint overlay rows are a dedicated component with source, non-durable state, status-board artifact, current/next checkpoint, progress, blocker, and verification evidence.
- Repo detail headline includes visibility.

Verification:

```text
python3 -m py_compile app/api/routes.py
uv run pytest tests/test_api_routes.py
npm run lint
npm run build
```

Result:

- Board API py_compile: PASS.
- API route tests: 16 passed, 11 warnings.
- Frontend lint: PASS.
- Frontend production build: PASS.

Next step: CP12, sync skills, command docs, references, and package handoffs with the implemented S27 contract.

## 2026-05-17T14:53:44Z - CP12 started

- CP12 scope: align Wily skill docs, Claude command shims, README, and references with the implemented v2 contract.
- Main stale language found: several docs still say bare `<phase-id>` and describe Stage execution as possible. They need to name canonical `<stage-id>/<phase-id>` for v2 and direct users to migration/decomposition for Stage ids.

Next step: patch the command docs and references, then run command-skill tests and documentation scans.

## 2026-05-17T14:57:36Z - CP12 complete

Files changed:

- `plugins/wily-roadmap/README.md`
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_runner.py`
- `plugins/wily-roadmap/commands/start.md`
- `plugins/wily-roadmap/commands/complete.md`
- `plugins/wily-roadmap/commands/block.md`
- `plugins/wily-roadmap/commands/run.md`
- `plugins/wily-roadmap/commands/next.md`
- `plugins/wily-roadmap/skills/wily-start/SKILL.md`
- `plugins/wily-roadmap/skills/wily-complete/SKILL.md`
- `plugins/wily-roadmap/skills/wily-block/SKILL.md`
- `plugins/wily-roadmap/skills/wily-run/SKILL.md`
- `plugins/wily-roadmap/skills/wily-next/SKILL.md`
- `plugins/wily-roadmap/skills/wily-workflow/SKILL.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/board-operations.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/board-reflection-contract.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/routing-policy.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/commit-policy.md`

Implemented:

- User-facing docs now describe `wily-roadmap-v2`, Stage-as-aggregation, Phase-as-execution, and canonical `<stage-id>/<phase-id>` refs.
- README documents `migrate-state`, `run --dry-run`, `checkpoint-sync`, and explicit `--prune-legacy`.
- Run/start/complete/block/next command docs now guide users away from executable Stage ids.
- Runner and Board reflection references now document non-durable Custom Workflow checkpoint overlays with `source`, `status_board`, and `is_durable`.
- CLI usage strings now show v2 Phase refs and `run --dry-run`.

Verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py
python3 -m json.tool plugins/wily-roadmap/.codex-plugin/plugin.json >/dev/null
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'migrate_state'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_dry_run_resolves_v2'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
```

Result:

- Command skill tests: 31 tests OK.
- py_compile: PASS.
- Manifest JSON parse: PASS.
- v2 start: 2 tests OK.
- migrate-state: 2 tests OK.
- v2 run dry-run: 1 test OK.
- checkpoint-sync: 2 tests OK.
- Full CLI tests: 139 tests OK, 1 skipped.

Next step: CP13, run final two-repo verification and disposable fixture migration apply before any real repo migration apply.

## 2026-05-17T14:58:39Z - CP13 started

- Final verification scope: Roadmap scripts/tests/smoke commands, disposable fixture migration apply, Wily Board backend tests, Wily Board frontend lint/build, Board repo dry-run migration, and local browser smoke for changed frontend routes when servers are available.
- Roadmap `pytest` is unavailable in this Python environment (`No module named pytest`), so Roadmap final test evidence will use the existing `unittest` suites after recording that fallback.

Next step: run Roadmap verification commands, then Board verification, then local browser smoke.

## 2026-05-17T15:03:05Z - CP13 Roadmap gap fixed during final verification

Finding:

- Disposable `mixed-legacy` fixture apply succeeded, but `wily next` on the migrated v2 fixture printed the next Stage without the executable Stage-local Phase. That violated the S27 v2 contract because execution identity must be the canonical `<stage-id>/<phase-id>` tuple.

Implemented:

- Added `test_v2_next_reports_next_stage_and_executable_phase`.
- Updated `command_next` so v2 roadmaps normalize aggregate Stage status from child Phases, select executable v2 Stages, and print canonical Phase refs such as `s02/p01`.

Verification:

```text
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_next_reports'
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'complete_stage_local_child_phase_updates_stage_state'
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'
```

Result:

- New v2 `wily next` regression: PASS.
- Legacy child Phase regression: PASS.
- v2 start regressions: PASS.

## 2026-05-17T15:08:06Z - CP13 complete

Files changed during CP13:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `agent-handoffs/s27-refactor-status.md`
- `agent-handoffs/s27-refactor-progress.md`
- `agent-handoffs/s27-refactor-verification.md`

Final verification:

```text
python3 -m pytest --version
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py plugins/wily-roadmap/scripts/wily_projection.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Result:

- Roadmap `pytest`: unavailable (`No module named pytest`), recorded as environment limitation.
- Roadmap py_compile: PASS.
- State summary tests: 15 OK.
- Command skill tests: 31 OK.
- Full CLI tests: 140 OK, 1 skipped.
- Watch UI tests: 63 OK, 1 skipped.
- Roadmap smoke commands: PASS.
- Roadmap real-repo migration dry-run: PASS.

Disposable migration apply:

```text
tmp=$(mktemp -d)
cp -R plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy "$tmp/project"
cd "$tmp/project"
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --apply
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily status
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily next
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily run s02/p01 --dry-run
```

Result:

- Migration apply: PASS.
- `wily status`: PASS.
- `wily next`: PASS, printed `Next phase: s02/p01 - Legacy refactor`.
- `wily run s02/p01 --dry-run`: PASS, printed Custom Workflow routing and native `/goal`.

Wily Board verification:

```text
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Result:

- Board pytest: 94 passed, 37 warnings.
- Frontend lint: PASS.
- Frontend build: PASS.
- Board repo migration dry-run: PASS.

Browser smoke:

- Started `uv run python dev_server.py` on `127.0.0.1:8765`.
- Started Next dev server with `WILY_BOARD_API_URL=http://127.0.0.1:8765` on `127.0.0.1:3000`.
- Used dev login cookie and captured Chrome screenshots:
  - `/tmp/s27-board-me.png`
  - `/tmp/s27-board-collab.png`
  - `/tmp/s27-board-repo.png`
- Verified `/me`, `/collab`, and `/repos/R-W-LAB/wily-roadmap` returned 200 and rendered the expected surface text plus canonical Stage/Phase refs.
- Stopped both local dev servers after verification.

Diff hygiene:

```text
git diff --check
```

Result:

- Wily Roadmap: PASS.
- Wily Board: PASS.
- `plugins/wily-roadmap/.codex-plugin/plugin.json`: no diff.

Final state:

- CP13 is DONE.
- S27 is complete under `agent-handoffs/s27-refactor-execution-package.md`.

## 2026-05-17T15:10:22Z - Completion audit complete

Audit correction:

- The earlier CP13 closeout recorded Roadmap `pytest` as unavailable and used `unittest` fallback.
- The execution package requires exact Roadmap pytest commands, so the audit created an isolated temp venv, installed `pytest`, and ran the exact Roadmap test files through pytest.

Verification:

```text
"$tmpvenv/bin/python" -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py plugins/wily-roadmap/tests/test_wily_cli.py plugins/wily-roadmap/tests/test_wily_watch_ui.py plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
disposable mixed-legacy apply/status/next/run dry-run smoke
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Result:

- Roadmap pytest: 247 passed, 2 skipped.
- Roadmap py_compile and smoke commands: PASS.
- Disposable fixture migration apply/status/next/run dry-run: PASS.
- Board pytest: 94 passed, 37 warnings.
- Board frontend lint/build: PASS.
- Board migration dry-run: PASS.

Audit result:

- Prompt-to-artifact checklist is recorded in `agent-handoffs/s27-refactor-verification.md`.
- No missing, incomplete, weakly verified, or uncovered execution-package requirement remains.

## 2026-05-17T15:11:55Z - Local Wily S27 completion state closed

Audit correction:

- The implementation and handoff evidence was complete, but the repository's local `.wily` state still reported S27 as the next Stage.
- Ran `wily complete s27` to close the local Wily Stage.
- Board bridge reflection failed with a network/config error; this was recorded in `.wily/status.md`. The repository contract is local-first, so local `.wily` state remains authoritative.

Verification:

```text
rg -n 'id: "s25"|id: "s26"|id: "s27"|status: "done"|status: "superseded"' .wily/roadmap.yaml
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily status
python3 -m unittest discover plugins/wily-roadmap/tests
git diff --check
```

Result:

- `.wily/roadmap.yaml` now has `s25` and `s26` superseded and `s27` done.
- `wily next`: `Next phase: none`.
- `wily status`: 25/27 complete with S27 removed from the next-work display.
- Roadmap unittest discovery: 249 tests OK, 2 skipped.
- Roadmap diff hygiene: PASS.

Final remaining work:

- None for S27. No production deploy, remote mutation, PR, real repo v2 apply, or `--prune-legacy` was run.
