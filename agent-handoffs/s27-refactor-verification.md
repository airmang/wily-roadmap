# S27 Stage/Phase Contract Refactor Verification

## Package Creation Verification

- Check: Source requirements loaded.
- Evidence: `agent-handoffs/s27-refactor-contract-requirements.md` read and folded into the package.

- Check: Design spec loaded.
- Evidence: `docs/superpowers/specs/2026-05-17-s27-refactor-design.md` read and folded into the package.

- Check: Current repo guidance loaded.
- Evidence: root `AGENTS.md` read; package preserves marketplace metadata, plugin manifest, local-first behavior, approval-first remote actions, and no new hooks/MCP/app integrations.

- Check: Dirty worktree constraints captured.
- Evidence: Wily Roadmap and Wily Board dirty status were recorded in `agent-handoffs/s27-refactor-execution-package.md`.

## Execution Package Validator

- Command: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-refactor-execution-package.md`
- Exit: 0
- Evidence: `PASS: execution package contract is complete.`

## Future Checkpoint Evidence

Checkpoint evidence must be appended by the `/goal` runner after each checkpoint:

- CP01 Contract freeze and fixtures:
  - Commands: `python3 -m json.tool plugins/wily-roadmap/tests/fixtures/projection/v2-with-checkpoint-overlay/projection.json >/dev/null`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily_state_summary.py`; `git diff --check -- plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md docs/superpowers/specs/2026-05-17-s27-refactor-design.md plugins/wily-roadmap/tests/fixtures`
  - Exit: 0
  - Evidence: JSON fixture parsed; command skill tests ran 31 tests OK; state summary tests ran 12 tests OK; py_compile and diff check passed.
- CP02 State schema and parser boundary:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'v2'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily_state_summary.py`
  - Exit: 0
  - Evidence: Red run first failed on missing v2 schema/next Phase/aggregate status; green run passed 2 v2 tests and 14 full state summary tests.
- CP03 Explicit migration command:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'migrate_state'`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
  - Exit: 0
  - Evidence: Red run first failed because `migrate-state` was not dispatched; green run passed 2 migration tests and 135 full CLI tests with 1 skip.
- CP04 Phase-only lifecycle commands:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'complete_stage_local_child_phase_updates_stage_state'`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
  - Exit: 0
  - Evidence: Red run first failed on Stage execution and namespaced lookup; green run passed 2 v2 lifecycle tests, legacy child regression, and 137 full CLI tests with 1 skip.
- CP05 Runner adapter registry and Custom Workflow default:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_dry_run_resolves_v2'`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily_runner.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'run_'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py -k 'wily_run'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
  - Exit: 0
  - Evidence: Red run first failed on missing `--dry-run`; green run passed v2 dry-run, existing run tests, command skill route tests, and 138 full CLI tests with 1 skip.
- CP06 Shared projection core:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'projection_builder'`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily_projection.py plugins/wily-roadmap/scripts/wily_watch_ui.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py`
  - Exit: 0
  - Evidence: Red run first failed on missing module; green run passed projection targeted test, 15 state summary tests, and 63 watch UI tests with 1 skip.
- CP07 Checkpoint overlay and Board event contract:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync_records_v2'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k 'projection_builder'`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_projection.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
  - Exit: 0
  - Evidence: Red run first failed because `checkpoint.source` was the status-board path; green run passed v2 tuple checkpoint sync, legacy checkpoint sync, projection overlay, py_compile, and 139 full CLI tests with 1 skip.
- CP08 Wily Board backend alignment:
  - Commands: `uv run pytest tests/test_live_events.py -k 'duplicate_stage_local'`; `uv run pytest tests/test_api_routes.py -k 'owning_stage_phase'`; `python3 -m py_compile app/db/repo.py app/live/events.py app/api/routes.py app/web/routes.py`; `uv run pytest tests/test_live_events.py`; `uv run pytest tests/test_api_routes.py`; `uv run pytest`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'v2_start'`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k 'checkpoint_sync'`
  - Exit: 0
  - Evidence: Red runs first showed duplicate Stage-local Phase ids collapsing in live sessions and leaking overlays in repo detail; green runs passed Board py_compile, 12 live event tests, 16 API route tests, 94 full Board tests with warnings, and Wily bridge regression targets.
- CP09 Wily Board IA chrome:
  - Commands: `npm run lint`; `npm run build`
  - Exit: 0
  - Evidence: Frontend lint passed; production build generated `/`, `/me`, `/collab`, repo detail, and `/api/repos` routes.
- CP10 Wily Board `/me` and `/collab` surfaces:
  - Commands: `npm run lint`; `npm run build`
  - Exit: 0
  - Evidence: `/me` and `/collab` widget composition linted and built successfully.
- CP11 Wily Board repo detail refactor:
  - Commands: `python3 -m py_compile app/api/routes.py`; `uv run pytest tests/test_api_routes.py`; `npm run lint`; `npm run build`
  - Exit: 0
  - Evidence: API href regression passed; frontend lint/build passed after tuple-safe repo detail and checkpoint row component.
- CP12 Skills, commands, docs, and cache sync:
  - Commands: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py`; `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py`; `python3 -m json.tool plugins/wily-roadmap/.codex-plugin/plugin.json`; targeted CLI checks for `v2_start`, `migrate_state`, `run_dry_run_resolves_v2`, and `checkpoint_sync`; `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
  - Exit: 0
  - Evidence: Command skill tests ran 31 tests OK; script compile and manifest parse passed; targeted CLI regressions passed; full CLI ran 139 tests OK with 1 skip.
- CP13 End-to-end migration and dashboard verification:
  - Commands:
    - Isolated temp venv setup for exact Roadmap pytest gate: `python3 -m venv "$tmpvenv"`; `"$tmpvenv/bin/python" -m pip install -q pytest`
    - `"$tmpvenv/bin/python" -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py plugins/wily-roadmap/tests/test_wily_cli.py plugins/wily-roadmap/tests/test_wily_watch_ui.py plugins/wily-roadmap/tests/test_wily_command_skills.py`
    - `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py plugins/wily-roadmap/scripts/wily_projection.py`
    - `./plugins/wily-roadmap/wily status`
    - `./plugins/wily-roadmap/wily next`
    - `./plugins/wily-roadmap/wily watch --once --ui ascii`
    - `./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run`
    - Disposable `mixed-legacy` fixture `migrate-state --apply`, `wily status`, `wily next`, and `wily run s02/p01 --dry-run`
    - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest`
    - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint`
    - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build`
    - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run`
    - Local browser smoke against `127.0.0.1:3000` using dev API seed on `127.0.0.1:8765`
    - `git diff --check` in Wily Roadmap and Wily Board
    - `wily complete s27`
    - `./plugins/wily-roadmap/wily next`
    - `python3 -m unittest discover plugins/wily-roadmap/tests`
  - Exit: 0 for all required verification.
  - Evidence: Roadmap exact pytest gate passed in an isolated temp venv: 247 passed, 2 skipped. Fresh Roadmap current-state reruns passed: 46 state/command skill unittests, 5 targeted v2 CLI tests, 140 full CLI tests, 63 watch UI tests, and 249 unittest-discover tests with 2 skipped. Roadmap py_compile passed. `wily status`, `wily next`, `wily watch --once --ui ascii`, and real-repo migration dry-run passed. Disposable fixture apply passed and `wily next` printed `Next phase: s02/p01 - Legacy refactor`; `wily run s02/p01 --dry-run` printed Custom Workflow routing and native `/goal`. Board `uv run pytest` ran 94 passed with 37 warnings; frontend lint/build passed; Board repo migration dry-run passed. Browser smoke rendered `/me`, `/collab`, and repo detail with screenshots at `/tmp/s27-board-me.png`, `/tmp/s27-board-collab.png`, and `/tmp/s27-board-repo.png`. Diff hygiene passed and plugin manifest has no diff. Local Wily S27 state is now complete: `.wily/roadmap.yaml` has S27 `done`, and `wily next` prints `Next phase: none`.

## Completion Audit

### Remediation Corrections

- Board canonical Phase detail route was missing from the original CP11 completion evidence and has now been implemented in `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]/page.tsx`; see `agent-handoffs/s27-remediation-verification.md`.
- Superseded s25/s26 progress semantics were incomplete in the original final state and now report `27/27 - 100%`; see `agent-handoffs/s27-remediation-verification.md`.
- Command/skill/runner usage surfaces that still used primary `<phase-id>` forms were corrected to primary `<stage-id>/<phase-id>` forms; see `agent-handoffs/s27-remediation-verification.md`.
- Batch migration evidence originally included nested `plugins/wily-roadmap/tests/fixtures/**` paths as local repos. Corrected discovery excludes fixture/test-data paths and records four non-fixture candidates in `agent-handoffs/batch-migrate-wily-v2-corrected-candidates.tsv`.
- Historical batch fixture mutations were restored so migration tests continue to exercise clean v1/mixed fixture sources.
- Integration marker policy is corrected: `pytest -m integration plugins/wily-roadmap/tests/` currently selects 0 tests, so the gate is N/A, not PASS.

Objective: complete S27 Stage/Phase contract refactor according to `agent-handoffs/s27-refactor-execution-package.md`.

Prompt-to-artifact checklist:

- Execution package and live handoffs exist and are current: `agent-handoffs/s27-refactor-execution-package.md`, `agent-handoffs/s27-refactor-status.md`, `agent-handoffs/s27-refactor-progress.md`, and this verification file exist; status shows 13/13 checkpoints complete.
- Local Wily S27 state is closed: `.wily/roadmap.yaml` marks `s27` as `done`, `s25` and `s26` remain `superseded`, and `./plugins/wily-roadmap/wily next` prints `Next phase: none`.
- Contract and fixtures: `plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md` exists; migration fixtures exist for `v1-only`, `mixed-legacy`, and `already-v2`; projection fixture exists at `plugins/wily-roadmap/tests/fixtures/projection/v2-with-checkpoint-overlay/projection.json`.
- v2 durable schema and parser boundary: `wily_state_summary.py` contains `roadmap_schema`, `is_v2_roadmap`, `canonical_phase_ref`, `aggregate_stage_status`, `executable_v2_stages`, and `next_executable_child_phase`; pytest covers these paths.
- Migration command: `wily.py` implements `migrate-state --to wily-roadmap-v2 (--dry-run|--apply|--prune-legacy)` with backup/report output; disposable fixture apply passed; real repos were dry-run only.
- Phase-only lifecycle and `wily next`: CLI tests cover Stage rejection, `s02/p01` resolution, aggregate status, and the final regression `test_v2_next_reports_next_stage_and_executable_phase`; fixture smoke confirmed `Next phase: s02/p01`.
- Runner adapter: `wily_runner.py` routes `custom-workflow` to `custom-workflow-skillset`, emits request/result artifacts, and `wily run s02/p01 --dry-run` prints the native `/goal` without durable mutation.
- Projection/checkpoint overlay: `wily_projection.py`, `wily_watch_ui.py`, and checkpoint-sync code attach non-durable `custom-workflow` checkpoint rows under owning `(stage_id, phase_id)`; tests cover tuple identity and non-durable overlay fields.
- Wily Board backend: `app/db/schema.sql`, `app/db/repo.py`, `app/live/events.py`, and `app/api/routes.py` use `(repo, stage_id, phase_id)` for live sessions, live items, claims, and repo detail placement; Board pytest passed.
- Wily Board frontend: `/me`, `/collab`, root redirect, shared surface nav, repo detail canonical refs, and checkpoint rows are implemented under `frontend/app/**` and `frontend/components/**`; lint/build passed and local browser smoke rendered the changed pages.
- Docs and skills: README, command docs, skill docs, and workflow references document v2, `<stage-id>/<phase-id>`, migration, checkpoint overlays, Custom Workflow black-box routing, and approval-first boundaries.
- Forbidden boundaries respected: no Custom Workflow plugin edits, no production deploy/restart, no remote push/PR/GitHub mutation, no real repo apply/prune, no plugin manifest diff, and `git diff --check` passed in both repos.

Audit result: achieved. No missing or weakly verified S27 requirement remains after the isolated pytest rerun and local Wily S27 completion-state correction.

## Final Verification Plan

Wily Roadmap:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py
# Integration marker policy: currently N/A because this selects 0 tests.
# Do not count this as PASS unless at least one integration test is selected.
python3 -m pytest -m integration plugins/wily-roadmap/tests/
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Disposable fixture migration apply:

```bash
tmp="$(mktemp -d)"
cp -R plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy "$tmp/project"
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --apply)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily status)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily next)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily run s02/p01 --dry-run)
```

Wily Board:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
cd frontend && npm run lint && npm run build
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Manual smoke:

- Synthetic `v1 only`, `mixed legacy`, and `already v2` migration fixtures behave as intended.
- Stage id passed to `wily run` fails with namespace guidance.
- `wily run <stage-id>/<phase-id> --dry-run` resolves a Stage-local Phase without durable mutation.
- `wily-watch` renders Stage rows, Phase rows, and temporary checkpoint child rows from one projection model.
- Board `/me` and `/collab` render visibility-appropriate surfaces.
- Board repo detail renders checkpoint rows under the owning Phase.
- Two-repo projection semantics remain consistent.

## Final Verification

Status: complete after remediation. Package validation, S27 implementation checkpoints, local Wily S27 completion, final Roadmap verification, final Board verification, disposable migration apply, browser/SSR smoke, corrected Board canonical Phase route verification, corrected superseded progress semantics, corrected command/skill/runner active surfaces, corrected batch discovery, fixture restoration, and diff hygiene passed. Integration marker verification is N/A because the marker selects 0 tests. Board bridge reflection for the final `wily complete s27` attempt failed due unavailable network/config and was recorded in `.wily/status.md`; this is non-blocking under the local-first contract.
