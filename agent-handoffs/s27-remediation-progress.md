# S27 Remediation Progress

## 2026-05-18T00:41:14Z - CP01 started

Scope:

- Implement and verify all previously identified S27 omissions.
- Preserve dirty worktrees in Wily Roadmap and Wily Board.
- Do not run production, remote, destructive, or `--prune-legacy` actions.

Initial confirmed omissions:

- Board canonical Phase route missing.
- Roadmap status/progress treats superseded s25/s26 as incomplete.
- v2 command docs still expose legacy `<phase-id>` as primary surface.
- Batch migration included nested test fixtures as repo candidates.
- Integration marker gate was not applicable but was treated as a normal final gate.

Next step: validate remediation execution package, then implement CP02 with TDD.

## 2026-05-18T00:44:39Z - CP01 complete

Validation:

- `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.10/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-remediation-execution-package.md`
- Result: PASS.

Notes:

- Added explicit pre-existing modified file guard, active goal auto-resolution log, and reviewer gate markers to the package.
- CP02 is now running: Board canonical Stage/Phase route support.

## 2026-05-18T00:49:15Z - CP02 complete

Changed in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- Added canonical API route `/api/repos/{owner}/{name}/stages/{stage_id}/phases/{phase_id}`.
- Kept legacy `/api/repos/{owner}/{name}/phases/{phase_id}?stage_id=...` on the same lookup helper.
- Added duplicate-safe API test for `s01/p01` and `s02/p01`.
- Added frontend App Router page `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.
- Updated phase row links and desk phase links to use canonical tuple routes while stage-only draft followups keep stage anchors.

Verification:

- `uv run pytest tests/test_api_routes.py` -> 17 passed.
- `npm run lint` -> PASS.
- `npm run build` -> PASS; route table includes `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.

Next step: CP03 Roadmap closed/progress semantics for superseded stages.

## 2026-05-18T00:53:59Z - CP03 complete

Changed:

- Added v2 closed-state semantics: `done` and `superseded` are both closed, while counts still report them separately.
- `wily_state_summary.py` now reports v2 closed totals as `닫힘 closed/total`.
- `wily_watch_ui.py` uses closed counts for v2 Stage progress and collapses superseded Stage/child Phase rows as completed work.
- `.wily/status.md` now reflects that s27 is complete and no next executable Stage/Phase is pending.

Verification:

- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py` -> 17 tests passed.
- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py` -> 65 tests passed, 1 skipped.
- `./plugins/wily-roadmap/wily status` -> `27/27 - 100%` and `27 stages done`.

Next step: CP04 command/skill v2 docs and usage.

## 2026-05-18T00:57:24Z - CP04 complete

Changed:

- Updated `wily-start`, `wily-complete`, `wily-block`, `wily-retry`, and `wily-run` skill usage to prefer `<stage-id>/<phase-id>` as the primary v2 Phase ref.
- Updated `commands/retry.md` to use canonical v2 Phase refs.
- Updated CLI usage for `live-worked` to show `[<stage-id>/<phase-id>|item-id]`.
- Kept legacy phase-only refs documented only as legacy non-v2 compatibility.

Verification:

- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py` -> 33 tests passed.
- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k UsageContractTest` -> 4 tests passed.
- `rg` scan found no primary `$wily-* <phase-id>`, retry `<phase-id>`, or `live-worked [item-id]` surfaces in the command/skill/live usage paths checked at CP04; the runner handoff surface was audited and fixed in CP06.

Next step: CP05 batch migration discovery and integration policy.

## 2026-05-18T01:00:38Z - CP05 complete

Changed:

- Corrected batch migration discovery contract to exclude `*/tests/fixtures/**`, `*/fixtures/**`, dependency/cache directories, and test data.
- Added `agent-handoffs/batch-migrate-wily-v2-corrected-candidates.tsv`.
- Updated batch migration package/status/progress/verification to invalidate the three historical fixture paths as repo candidates.
- Updated S27 verification/package evidence so `pytest -m integration` is N/A when zero tests are selected.

Verification:

- Raw discovery found 7 `.wily/roadmap.yaml` paths.
- Corrected discovery excludes 3 fixture paths and records 4 non-fixture candidates: DIVE-2, Digit, hwpx, wily-roadmap.
- Isolated pytest command for `-m integration` collected 256 items, deselected 256, selected 0, and exited 5; this is recorded as N/A, not PASS.

Next step: CP06 final verification and completion audit.

## 2026-05-18T01:10:05Z - CP06 complete

Changed:

- Restored migration fixture source directories after discovering the earlier batch migration loop had mutated test fixtures; full CLI migration tests now pass from clean fixture inputs.
- Added the missing active-surface cleanup in `wily_runner.py`: Custom Workflow result instructions now use `<stage-id>/<phase-id>` as the primary completion/blocking form and mention legacy phase-only ids only for non-v2 roadmaps.
- Added CLI regression coverage so the Custom Workflow request text cannot regress to `$wily-complete <phase-id>` or `$wily-block <phase-id>`.
- Completed the Board canonical Stage/Phase route smoke with a live API and Next frontend.

Verification:

- `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py plugins/wily-roadmap/scripts/wily_projection.py` -> exit 0.
- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py plugins/wily-roadmap/tests/test_wily_watch_ui.py plugins/wily-roadmap/tests/test_wily_command_skills.py plugins/wily-roadmap/tests/test_wily_cli.py` -> 256 tests OK, 2 skipped.
- Active command/skill/script usage scan for primary `$wily-* <phase-id>`, `argument-hint: '<phase-id>`, and `live-worked [item-id]` -> no matches.
- `./plugins/wily-roadmap/wily status` and `./plugins/wily-roadmap/wily watch --once --ui ascii` -> `27/27 - 100%`; `./plugins/wily-roadmap/wily next` -> `Next phase: none`.
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest` -> 95 passed, 38 warnings.
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint` -> exit 0.
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build` -> exit 0; route table includes `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.
- Canonical route smoke returned `HTTP/1.1 200 OK` and rendered `R-W-LAB/wily-roadmap · s02/p01`, `Canonical route smoke`, and `Render the tuple-safe phase detail route.`
- `git diff --check` -> exit 0 in both Wily Roadmap and Wily Board.
- Execution package validator -> `PASS: execution package contract is complete.`

Final audit:

- Board canonical Phase route omission: resolved and smoke-tested.
- Superseded progress omission: resolved; current status/watch report `27/27 - 100%`.
- Command/skill/runner v2 primary usage omission: resolved; active surface scan is clean.
- Batch discovery fixture omission: resolved; corrected candidate set excludes fixtures and source fixtures are restored for tests.
- Integration marker overstatement: resolved; zero-selected marker is recorded as N/A, not PASS.

Result: S27 remediation is complete.
