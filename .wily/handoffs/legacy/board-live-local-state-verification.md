# Verification Evidence: Board Live Local State And Checkpoint Visibility

## Baseline

- `python3 plugins/wily-roadmap/scripts/wily.py status`
  - Exit: 0
  - Evidence: roadmap version 27; current/next Stage `s25`; progress `24/25`.
- `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`
  - Exit: 0
  - Evidence: live config OK, signature ready, Codex hook OK, endpoint HTTP 200, secret redacted.

## Pending

- Wily CLI regression tests.
- Board API/live/web route tests.
- Frontend lint/build.
- Final local smoke.

## Execution Package Validator

- Command: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/board-live-local-state-execution-package.md`
- Exit: 0
- Evidence: `PASS: execution package contract is complete.`

## CP01 RED Tests

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_sync_local_replays_existing_decomposed_stage_draft`
- Exit: 1
- Expected failure: `wily board sync-local` is not implemented and `command_board` prints usage.

- Command: `uv run pytest tests/test_api_routes.py::test_api_repos_counts_live_draft_stage_when_durable_sync_is_behind tests/test_api_routes.py::test_api_desk_includes_live_draft_followup tests/test_api_routes.py::test_api_repo_detail_projects_live_draft_stage_and_checkpoint_when_durable_sync_is_behind tests/test_api_routes.py::test_api_sse_live_emits_refresh_when_visible_repo_receives_live_event -q`
- Exit: 1
- Expected failures:
  - repo progress counts only durable stages;
  - desk followup list omits live drafts;
  - repo detail omits draft-only `s25`;
  - SSE does not refresh on `live_event`.

## CP02 Wily CLI Replay

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_sync_local_replays_existing_decomposed_stage_draft`
- Exit: 0
- Evidence: targeted test passed; replay payload includes existing local decomposed Stage metadata and child Phase topology.

## CP03 Board API Draft Projection

- Command: `uv run pytest tests/test_api_routes.py::test_api_repos_counts_live_draft_stage_when_durable_sync_is_behind tests/test_api_routes.py::test_api_desk_includes_live_draft_followup tests/test_api_routes.py::test_api_repo_detail_projects_live_draft_stage_and_checkpoint_when_durable_sync_is_behind tests/test_api_routes.py::test_api_sse_live_emits_refresh_when_visible_repo_receives_live_event -q`
- Exit: 0
- Evidence: `4 passed`; deprecation warnings only.

## CP04 Frontend Rendering

- Command: `npm run lint`
- Exit: 0
- Evidence: ESLint passed.
- Command: `npm run build`
- Exit: 0
- Evidence: Next production build completed successfully.

## CP05 Final Verification

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- Exit: 0
- Evidence: `Ran 116 tests ... OK`.

- Command: `uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py -q`
- Exit: 0
- Evidence: `48 passed, 33 warnings`.

- Command: `npm run lint && npm run build`
- Exit: 0
- Evidence: ESLint passed and Next production build completed successfully.

- Command: `git diff --check` in `wily-roadmap`
- Exit: 0
- Evidence: no output.

- Command: `git diff --check` in `wily-board`
- Exit: 0
- Evidence: no output.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py status`
- Exit: 0
- Evidence: current Stage `s25`, progress `24/25`.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`
- Exit: 0
- Evidence: config OK, signature ready, Codex hook OK, endpoint HTTP 200, secret redacted.

## Production Deploy And Actual Site Verification

- Command: `rsync ... /opt/wily-board/` followed by `ssh ... 'cd /opt/wily-board && ./deploy/apply.sh'`
- Exit: 0
- Evidence: backend package installed, `npm run build` completed, `wily-board` and `wily-board-frontend` restarted, `/healthz` passed.

- Command: `python3 plugins/wily-roadmap/scripts/wily.py board sync-local s25`
- Exit: 0
- Evidence: `Board live draft sent for s25: 4 phases`; `Board local draft synced for s25: 4 phases`.

- Check: production DB active live drafts for `R-W-LAB/wily-roadmap`
- Evidence: stray test draft `s01-mvp0` was cleared; active draft Stage ids are `['s25']`.

- Check: authenticated production API for `https://rnwlab.duckdns.org/api/repos`
- Evidence: `R-W-LAB/wily-roadmap` reports `stage_done: 24`, `stage_total: 25`, `percent: 96`, `live_badge: local draft`.

- Check: authenticated production API for `https://rnwlab.duckdns.org/api/repos/R-W-LAB/wily-roadmap`
- Evidence: draft Stage `s25` appears with title `Wily Board UI polish and usability improvements`, `phase_count: 4`, queue reason `4 draft phases awaiting push`, and phases `25-1`, `25-2`, `25-3`, `25-4`.

- Check: authenticated production HTML for `https://rnwlab.duckdns.org/`
- Evidence: rendered text includes `R-W-LAB/wily-roadmap 24 / 25 local draft` and `s25 decomposed locally 4 draft phases awaiting push`.

- Check: authenticated production HTML for `https://rnwlab.duckdns.org/repos/R-W-LAB/wily-roadmap`
- Evidence: rendered text includes `R-W-LAB/wily-roadmap · 24 / 25 stages · 1 left`, `DAG STAGE MAP 25 stages`, and `s25 Wily Board UI polish and usability improvements 0/4 phases · local draft`.

- Check: production SSE `https://rnwlab.duckdns.org/api/sse/live?repo=R-W-LAB/wily-roadmap` while replaying `sync-local s25`
- Evidence: stream received `event: durable.synced` with `kind: live_event`, which is the Next live refresh trigger.

- Cleanup: temporary verification auth session deleted from `oauth_sessions`.
- Evidence: after cleanup, active draft Stage ids remain `['s25']`.

## Final Fresh Verification After Production Work

- Command: `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- Exit: 0
- Evidence: `Ran 116 tests ... OK`.

- Command: `uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py -q`
- Exit: 0
- Evidence: `48 passed, 33 warnings`.

- Command: `npm run lint && npm run build`
- Exit: 0
- Evidence: ESLint produced no errors; Next production build completed.

- Command: `git diff --check` in both repos
- Exit: 0
- Evidence: no output in either repo.

- Command: `curl -sk https://rnwlab.duckdns.org/healthz`
- Exit: 0
- Evidence: `{"ok":true}`.

- Command: `systemctl is-active wily-board.service wily-board-frontend.service`
- Exit: 0
- Evidence: both services report `active`.

## Acceptance Checklist

- Local draft replay command exists: yes, `wily board sync-local <stage-id>`.
- Replay payload includes Stage metadata and child Phases: yes, covered by Wily CLI regression test.
- Missing config is non-fatal and visible: yes, existing and updated Wily tests pass.
- API includes draft-only Stages and draft child Phases: yes, Board API regression test passes.
- API progress overlays draft-only Stage totals: yes, Board API regression test passes.
- Draft Phase rows can show checkpoint overlays: yes, Board API regression test passes.
- Desk includes draft follow-up: yes, Board API regression test passes.
- SSE refresh covers live events: yes, Board API regression test passes.
- Durable sync reconciliation remains covered by existing web/live tests: yes, selected Board suite passes.
- Production live event emission: run after explicit user request; `s25` draft is stored and visible on the actual site.
