# S27 Remediation Verification

## Baseline Evidence

- Board canonical route file absent: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]/page.tsx`.
- Prior S27 package requires that route in `agent-handoffs/s27-refactor-execution-package.md`.
- `./plugins/wily-roadmap/wily status` showed `25/27 - 93%` after S27 migration, with s25/s26 superseded and s27 done.
- `plugins/wily-roadmap/skills/wily-run/SKILL.md`, `plugins/wily-roadmap/commands/retry.md`, and `plugins/wily-roadmap/skills/wily-retry/SKILL.md` still expose primary `<phase-id>` language.
- `agent-handoffs/batch-migrate-wily-v2-summary.tsv` includes nested fixture paths under `plugins/wily-roadmap/tests/fixtures`.
- `pytest -m integration plugins/wily-roadmap/tests/` selects zero tests and exits 5 in an isolated pytest environment.

## Checkpoint Evidence

### CP01 Package Validator

- Command: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.10/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-remediation-execution-package.md`
- Result: PASS.

### CP02 Board Canonical Phase Route

- RED command: `uv run pytest tests/test_api_routes.py::test_api_phase_detail_canonical_route_is_stage_scoped_for_duplicate_phase_ids`
- RED result: failed with 404 because canonical API route was absent.
- Targeted API verification: `uv run pytest tests/test_api_routes.py` -> 17 passed.
- Frontend lint: `npm run lint` -> PASS.
- Frontend build: `npm run build` -> PASS.
- Build route evidence: Next route table includes `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.

### CP03 Roadmap Closed Progress Semantics

- RED command: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py -k superseded`
- RED result: v2 summary did not report closed totals and superseded dependencies were not treated as non-blocking.
- RED command: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py -k superseded`
- RED result: v2 watch progress was `2/3 - 67%` and superseded child phases rendered as unfinished.
- Targeted verification: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py` -> 17 passed.
- Targeted verification: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py` -> 65 passed, 1 skipped.
- Smoke: `./plugins/wily-roadmap/wily status` -> `27/27 - 100%`, `27 stages done`.

### CP04 Command And Skill Usage

- RED command: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py -k canonical`
- RED result: lifecycle skills still used primary `$wily-* <phase-id>` forms.
- RED command: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k live_usage`
- RED result: `live-worked` usage showed `[item-id]` only.
- Targeted verification: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py` -> 33 passed.
- Targeted verification: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py -k UsageContractTest` -> 4 passed.
- Scan: `rg` found no primary `$wily-* <phase-id>`, retry `<phase-id>`, or `live-worked [item-id]` surfaces in updated command/skill/usage paths; the Custom Workflow runner handoff was added to the CP06 active-surface audit and fixed there.

### CP05 Batch Discovery And Integration Policy

- Batch discovery correction: raw `find /Users/wilycastle/Code/projects -path '*/.wily/roadmap.yaml' -print | sort` found 7 paths.
- Corrected non-fixture candidates: DIVE-2, Digit, hwpx, wily-roadmap.
- Invalidated historical fixture candidates: `plugins/wily-roadmap/tests/fixtures/migration/already-v2`, `mixed-legacy`, and `v1-only`.
- Restored mutated fixture source directories after detecting the historical batch run had modified `mixed-legacy` and `v1-only`; full CLI migration tests now pass from clean fixture inputs.
- Evidence file: `agent-handoffs/batch-migrate-wily-v2-corrected-candidates.tsv`.
- Integration marker command in isolated pytest venv: `python -m pytest -m integration plugins/wily-roadmap/tests/`
- Integration marker result: exit 5 with `collected 256 items / 256 deselected / 0 selected`.
- Policy result: N/A, not PASS, unless at least one integration test is selected in the future.

### CP06 Final Verification

- Package validator: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.10/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-remediation-execution-package.md` -> PASS.
- Roadmap compile: `python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py plugins/wily-roadmap/scripts/wily_projection.py` -> exit 0.
- Roadmap final unittest suite: `python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py plugins/wily-roadmap/tests/test_wily_watch_ui.py plugins/wily-roadmap/tests/test_wily_command_skills.py plugins/wily-roadmap/tests/test_wily_cli.py` -> 256 tests OK, 2 skipped.
- Roadmap current-state smoke: `./plugins/wily-roadmap/wily status` and `./plugins/wily-roadmap/wily watch --once --ui ascii` -> `27/27 - 100%`; `./plugins/wily-roadmap/wily next` -> `Next phase: none`.
- Active usage scan: `rg` found no active command/skill/script primary `$wily-* <phase-id>`, `argument-hint: '<phase-id>`, or `live-worked [item-id]` surfaces.
- Board final backend verification: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest` -> 95 passed, 38 warnings.
- Board final frontend verification: `npm run lint` -> pass; `npm run build` -> pass and route table includes `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.
- Board canonical route smoke: `curl` against `/repos/R-W-LAB/wily-roadmap/stages/s02/phases/p01` returned `HTTP/1.1 200 OK` and rendered `R-W-LAB/wily-roadmap · s02/p01`, `Canonical route smoke`, and `Render the tuple-safe phase detail route.`
- Diff hygiene: `git diff --check` passed in Wily Roadmap and Wily Board.

## Final Audit

Prompt-to-artifact checklist:

- Board canonical Phase route exists and is verified through backend tuple lookup, frontend route build output, and live SSR smoke.
- Roadmap v2 closed-state semantics count `done` and `superseded` as closed for progress/watch while preserving individual status counts.
- S27 local state is complete: status/watch report `27/27 - 100%`, and `wily next` reports no next Phase.
- Command, skill, CLI usage, and Custom Workflow runner handoff active surfaces use `<stage-id>/<phase-id>` as the primary v2 Phase ref.
- Batch migration discovery excludes fixture/test-data candidates, records the corrected non-fixture set, and preserves fixture source directories for migration tests.
- Integration marker evidence is not overstated: zero selected tests remain N/A rather than PASS.
- No forbidden boundary was crossed: no production deploy/restart, remote push/PR/GitHub mutation, real `--prune-legacy`, hook/MCP/app layer addition, or plugin manifest change.

Audit result: achieved. No uncovered S27 remediation requirement remains in the active implementation, command, skill, runner, Board route, migration, or verification surfaces.
