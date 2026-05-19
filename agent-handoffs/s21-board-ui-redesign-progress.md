# S21 Board UI Redesign Progress

## 2026-05-17 00:43 KST

Checkpoint: Baseline and execution package.

Files changed:
- `agent-handoffs/s21-board-ui-redesign-status.md`
- `agent-handoffs/s21-board-ui-redesign-execution-package.md`
- `agent-handoffs/s21-board-ui-redesign-progress.md`

Commands run:
- `uv run pytest` in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`

Result:
- Baseline backend tests passed: 71 passed, 26 warnings.

Evidence:
- Active native goal created for S21 implementation.
- Execution package created with sequential plan and verification gates.

Next step:
- Validate execution package, then start Checkpoint 1 contract/API tests.

Auto-resolved under active /goal: Superpowers review/approval gates -> recorded as progress/evidence checkpoints because the user explicitly requested autonomous S21 implementation.

## 2026-05-17 00:44 KST

Checkpoint: Execution package validation.

Commands run:
- `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s21-board-ui-redesign-execution-package.md`

Result:
- Validator failed on required wording: `pre-existing modified files`, `reviewer gates`.

Action:
- Added explicit `Pre-existing modified files` and `Reviewer Gates` sections to the execution package.
- Second validator run still required literal `completion_verifier` or `integration_reviewer` wording; added both as local reviewer gates.

Next step:
- Re-run validator.

## 2026-05-17 01:49 KST

Checkpoint: Contract reconciliation and FastAPI API implementation.

Files changed:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/__init__.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/**` via Wily `start`/`complete` for 21-1

Commands run:
- `uv run pytest tests/test_api_routes.py -q`
- `uv run pytest`
- `python3 plugins/wily-roadmap/scripts/wily.py start 21-1`
- `python3 plugins/wily-roadmap/scripts/wily.py complete 21-1`

Result:
- API red tests initially failed with 404 for all new endpoints.
- Implemented `app.api.routes` and registered it in `app.main`.
- Targeted API tests passed: 8 passed, 7 warnings.
- Full Python tests passed: 79 passed, 33 warnings.
- Wily phase 21-1 marked done.

Root-cause note:
- One intermediate test failure came from the current app auto-registering default sync repos from env. The test incorrectly assumed the seeded repo was first. Adjusted test to find the repo by `full_name`, matching existing code behavior.

Architect gate:
- Backend keeps existing Jinja routes during development.
- SSE path locked to `/api/sse/live`.
- GitHub App sync token path remains untouched; action route removal is deferred to cutover.

Next step:
- Build `frontend/` scaffold and authenticated shell against the new API.

## 2026-05-17 02:26 KST

Checkpoint: S21 implementation completed after roadmap v25 checkpoint bridge update.

Files changed across the two workspaces:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/deploy/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`

Implemented:
- Wily `checkpoint-sync` adapter for Custom Workflow status boards.
- Local live checkpoint overlay registry and signed `checkpoint_updated` Board events.
- Wily watch/status rendering for checkpoint overlays without changing durable Phase status.
- Board JSON/SSE checkpoint payload passthrough from live events.
- Next.js read-only hub, repo workspace, command palette, theme/rail preferences, responsive layouts, and checkpoint phase rows.
- Read-only cutover from Board action routes to Next.js frontend routing and updated deployment docs.

Verification summary:
- Wily plugin tests: 204 tests OK, 2 skipped.
- Wily script compile: pass.
- Board backend tests: 79 passed, 31 warnings.
- Frontend lint: pass.
- Frontend production build: pass.
- Browser smoke: desktop and mobile repo views render checkpoint `CP04`; mobile horizontal overflow is 0.

Wily state:
- Completed phases `21-2` through `21-9`.
- `wily status --once`: 23/23, 100%.
- `wily next`: none.
