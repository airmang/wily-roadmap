# Progress Log: Board Live Local State And Checkpoint Visibility

## 2026-05-17T08:55:39Z

Checkpoint: planning

Files changed:

- `agent-handoffs/board-live-local-state-requirements.md`
- `agent-handoffs/board-live-local-state-execution-package.md`
- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `git status --short` in `wily-roadmap`
- `python3 plugins/wily-roadmap/scripts/wily.py status`
- `python3 plugins/wily-roadmap/scripts/wily.py next`
- `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`
- repo/API/code inspection commands in `wily-roadmap` and `wily-board`

Result:

- Confirmed local Wily state is at Stage `s25`.
- Confirmed Board live config and endpoint probe are OK.
- Found likely root cause: Board Next/API path does not project `live_drafts`, and Wily CLI lacks a local replay command for topology created outside `decompose-stage`.

Next step:

- Validate execution package, start goal, then begin CP01 regression tests.

Blockers / risks:

- None yet.

## 2026-05-17T08:56:10Z

Checkpoint: planning

Files changed:

- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/board-live-local-state-execution-package.md`

Result:

- PASS: execution package contract is complete.

Next step:

- Start native goal and begin CP01 regression tests.

Blockers / risks:

- None.

## 2026-05-17T09:54:30Z

Checkpoint: production deploy and actual-site synchronization

Files changed:

- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `rsync ... /opt/wily-board/`
- `ssh ... 'cd /opt/wily-board && ./deploy/apply.sh'`
- `python3 plugins/wily-roadmap/scripts/wily.py board sync-local s25`
- authenticated `curl` checks against `https://rnwlab.duckdns.org/api/repos`, `/api/repos/R-W-LAB/wily-roadmap`, `/`, and `/repos/R-W-LAB/wily-roadmap`
- production SSE check against `/api/sse/live?repo=R-W-LAB/wily-roadmap` while replaying `sync-local s25`
- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- `uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py -q`
- `npm run lint && npm run build`
- `git diff --check` in both repos
- `curl -sk https://rnwlab.duckdns.org/healthz`
- `systemctl is-active wily-board.service wily-board-frontend.service`

Result:

- PASS: production deploy applied and both services are active.
- PASS: production `s25` live draft stored with 4 phases.
- PASS: actual site API reports `R-W-LAB/wily-roadmap` as `24 / 25` with `local draft`.
- PASS: actual site repo detail renders `DAG STAGE MAP 25 stages`, `s25`, `0/4 phases`, `local draft`, and phases `25-1`..`25-4`.
- PASS: SSE emitted `durable.synced` for a `live_event` after replaying `s25`.
- PASS: local final verification commands passed.
- Cleanup: temporary verification auth session was deleted; only active production draft Stage is `s25`.

Next step:

- Final response.

Blockers / risks:

- Chrome extension automation was unavailable from Codex even though Chrome and the extension were installed/enabled, so visual browser verification used authenticated API/SSR HTML/SSE evidence instead of an interactive Chrome session.

## 2026-05-17T09:10:10Z

Checkpoint: CP05 Local smoke, evidence, and final verification

Files changed:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `agent-handoffs/board-live-local-state-*.md`

Commands run:

- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- `uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py -q`
- `npm run lint && npm run build`
- `git diff --check` in both repos
- `python3 plugins/wily-roadmap/scripts/wily.py status`
- `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`

Result:

- PASS: Wily CLI test class, 116 tests.
- PASS: Board API/live/web tests, 48 tests.
- PASS: frontend lint and production build.
- PASS: diff checks.
- PASS: Wily status still reports `s25` as current, `24/25`.
- PASS: Board config/signature/hook/endpoint probe OK with secret redacted.

Next step:

- Final response.

Blockers / risks:

- Production live draft emission was intentionally not run. To update the configured production Board with the current local `s25` draft, run `wily board sync-local s25` only after approval.

## 2026-05-17T09:01:30Z

Checkpoint: CP01 Baseline and regression tests

Files changed:

- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_sync_local_replays_existing_decomposed_stage_draft`
- `uv run pytest tests/test_api_routes.py::test_api_repos_counts_live_draft_stage_when_durable_sync_is_behind tests/test_api_routes.py::test_api_desk_includes_live_draft_followup tests/test_api_routes.py::test_api_repo_detail_projects_live_draft_stage_and_checkpoint_when_durable_sync_is_behind tests/test_api_routes.py::test_api_sse_live_emits_refresh_when_visible_repo_receives_live_event -q`

Result:

- RED confirmed.
- Wily CLI test fails because `wily board sync-local` is not implemented.
- Board API tests fail because live draft topology is not counted, projected into desk/repo detail, or emitted as a refresh-triggering event.

Next step:

- CP02: implement Wily CLI local draft replay with minimum code to pass the new CLI regression.

Blockers / risks:

- Test isolation was tightened so Wily CLI tests do not read the user's default Board config.

## 2026-05-17T09:04:10Z

Checkpoint: CP02 Wily CLI local draft replay

Files changed:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_board_sync_local_replays_existing_decomposed_stage_draft`

Result:

- PASS.
- Added `wily board sync-local <stage-id>`.
- Draft payload now includes Stage title, status, owner, dependencies, execution mode, raw path, and position when known.

Next step:

- CP03: project Board `live_drafts` into API repo progress, desk, repo detail, and SSE refresh.

Blockers / risks:

- Board API tests remain RED as expected.

## 2026-05-17T09:08:00Z

Checkpoint: CP03 Board API draft projection and CP04 Next.js rendering/live refresh

Files changed:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`
- `agent-handoffs/board-live-local-state-verification.md`

Commands run:

- `uv run pytest tests/test_api_routes.py::test_api_repos_counts_live_draft_stage_when_durable_sync_is_behind tests/test_api_routes.py::test_api_desk_includes_live_draft_followup tests/test_api_routes.py::test_api_repo_detail_projects_live_draft_stage_and_checkpoint_when_durable_sync_is_behind tests/test_api_routes.py::test_api_sse_live_emits_refresh_when_visible_repo_receives_live_event -q`
- `npm run lint`
- `npm run build`

Result:

- PASS: targeted Board API draft/progress/desk/SSE tests.
- PASS: frontend lint.
- PASS: frontend production build.
- Draft Stage/Phase payloads now have UI-visible `local draft` / `awaiting push` markers.

Next step:

- CP05: run final verification commands and local smoke evidence.

Blockers / risks:

- None.

## 2026-05-17T08:58:00Z

Checkpoint: CP01 Baseline and regression tests

Files changed:

- `agent-handoffs/board-live-local-state-status.md`
- `agent-handoffs/board-live-local-state-progress.md`

Commands run:

- `create_goal` with objective from `agent-handoffs/board-live-local-state-execution-package.md`
- Read `Superpowers:test-driven-development`
- Read `Superpowers:systematic-debugging`

Result:

- Native goal is active.
- Auto-resolved under active /goal: `Superpowers:brainstorming` approval gate -> proceeding from the user-requested handoff/goal package with local progress evidence.

Next step:

- Add CP01 failing regression tests in Wily CLI and Board API.

Blockers / risks:

- None.
