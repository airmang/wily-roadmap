# S24 Realtime Board Bridge Verification

## Baseline

- Execution package validator:
  - Command: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s24-realtime-board-bridge-execution-package.md`
  - Exit: 0
  - Evidence: `PASS: execution package contract is complete.`

## Checkpoint Evidence

### Checkpoint 1 - Board live config, diagnostics, and hook contract

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_live_config_loads_repo_local_untracked_file plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_live_config_loads_repo_root_untracked_file plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_check_reports_missing_config_and_hook plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_check_redacts_secret_and_detects_hook plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_hooks_install_codex_writes_post_tool_use_command plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_checkpoint_sync_reads_custom_workflow_status_board_without_completing_phase`
- Exit: 0
- Evidence: `Ran 6 tests ... OK`

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest.test_render_shows_checkpoint_overlay_from_local_live_registry plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest.test_render_warns_when_active_work_has_no_board_live_config`
- Exit: 0
- Evidence: `Ran 2 tests ... OK`

### Checkpoint 2 - Wily checkpoint session bridge

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_checkpoint_sync_reads_custom_workflow_status_board_without_completing_phase`
- Exit: 0
- Evidence: `Ran 1 test ... OK`

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_live_worked_preserves_checkpoint_context_on_active_session`
- Exit: 0
- Evidence: `Ran 1 test ... OK`

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest.test_render_shows_checkpoint_overlay_from_local_live_registry`
- Exit: 0
- Evidence: `Ran 1 test ... OK`

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest.test_render_warns_when_active_work_has_no_board_live_config`
- Exit: 0
- Evidence: `Ran 1 test ... OK`

## Final Verification

### Checkpoint 3 - Board checkpoint overlay API, SSE, and UI parity

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_live_heartbeat_uses_repo_root_board_config`
- Exit: 0
- Evidence: `Ran 1 test ... OK`

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_live_heartbeat_preserves_checkpoint_context_on_active_session plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_live_heartbeat_reuses_active_checkpoint_session_without_session_arg`
- Exit: 0
- Evidence: heartbeat kept checkpoint `CP02` attached to the active live session.

- Check: Board API desk/repo/SSE local smoke
- Exit: 0
- Evidence: `/api/desk`, `/api/repos/R-W-LAB/wily-roadmap`, and `/api/sse/live` returned checkpoint `CP02`, `Checkpoint bridge`, and `proving local Board overlay`.

### Checkpoint 4 - Local E2E proof and production smoke gate

- Command: `wily board check`, `wily start 24-1`, `wily checkpoint-sync`, `wily live-worked`, `wily live-heartbeat`
- Exit: 0
- Evidence: temporary local Board API received signed live events and kept checkpoint overlay attached through heartbeat/work refresh.

- Check: Next UI/browser smoke
- Exit: 0
- Evidence: home desk rendered `CP02`; repo detail rendered checkpoint row `CP02 Checkpoint bridge` with action `proving local Board overlay`.
- Screenshot evidence:
  - `/var/folders/jt/sdwtj3bs31j9084n_bx85fsh0000gn/T/s24-board-e2e-home.png`
  - `/var/folders/jt/sdwtj3bs31j9084n_bx85fsh0000gn/T/s24-board-e2e-checkpoint-row.png`

### Final Regression

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest`
- Exit: 0
- Evidence: `Ran 121 tests ... OK (skipped=1)`

- Command: `cd /Users/wilycastle/Code/projects/wily-board && uv run pytest -q`
- Exit: 0
- Evidence: `80 passed, 31 warnings`

- Command: `cd /Users/wilycastle/Code/projects/wily-board/frontend && npm run lint`
- Exit: 0
- Evidence: ESLint completed with no reported errors.

- Command: `cd /Users/wilycastle/Code/projects/wily-board/frontend && npm run build`
- Exit: 0
- Evidence: Next.js production build completed successfully.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py status`
- Exit: 0
- Evidence: `24/24 - 100%`

- Command: `python3 plugins/wily-roadmap/scripts/wily.py next`
- Exit: 0
- Evidence: `Next phase: none`

Production smoke was not run. It remains approval-gated because it requires production URL/secret and may involve live remote events or deployment/restart boundaries.

### Fresh final verification after checkpoint validator hardening

- Command: `uv run pytest tests/test_live_events.py::test_live_event_accepts_signed_checkpoint_overlay_without_changing_durable_state tests/test_live_events.py::test_live_event_rejects_malformed_checkpoint_overlay -q`
- Exit: 0
- Evidence: `2 passed in 0.17s`

- Command: `uv run pytest tests/test_live_events.py tests/test_api_routes.py tests/test_web_routes.py -q`
- Exit: 0
- Evidence: `41 passed, 30 warnings in 0.70s`

- Command: `python3 -m unittest discover plugins/wily-roadmap/tests`
- Exit: 0
- Evidence: `Ran 212 tests in 6.876s - OK (skipped=2)`

- Command: `uv run pytest -q`
- Exit: 0
- Evidence: `82 passed, 31 warnings in 1.81s`

- Command: `npm run lint`
- Exit: 0
- Evidence: ESLint completed with exit 0.

- Command: `npm run build`
- Exit: 0
- Evidence: Next.js production build compiled successfully, type checks passed, and routes generated.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py status`
- Exit: 0
- Evidence: Roadmap v26 reports 24/24, 100%.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py next`
- Exit: 0
- Evidence: `Next phase: none`
