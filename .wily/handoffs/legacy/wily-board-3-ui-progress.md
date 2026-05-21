# Wily Board Plan 3 UI SSE Realtime Progress

## 2026-05-19 - Checkpoint 1

- Checkpoint: Handoff/status/progress files.
- Files changed:
  - `agent-handoffs/wily-board-3-ui-execution-package.md`
  - `agent-handoffs/wily-board-3-ui-status.md`
  - `agent-handoffs/wily-board-3-ui-progress.md`
- Commands run: none.
- Result: runtime contract initialized.
- Next step: implement SSE broker and route with targeted tests.
- Notes: Plan 2 dirty files in `/Users/wilycastle/Code/projects/wily-plugin/wily-board` are treated as pre-existing and preserved.

## 2026-05-19 - Checkpoint 2

- Checkpoint: SSE broker and route.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/uv.lock`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sse/__init__.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sse/broker.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sse/routes.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_sse_broker.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_sse_route.py`
- Commands run:
  - `uv sync --extra dev`
  - `uv run pytest tests/test_sse_broker.py tests/test_sse_route.py -v`
- Result: 6 tests passed.
- Adjustment: direct HTTP streaming test was replaced with an iterator-level stream formatting test because `httpx.ASGITransport` can hang on infinite SSE responses.
- Next step: add broker publish hooks for snapshot and heartbeat.

## 2026-05-19 - Checkpoint 3

- Checkpoint: Agent event publishing.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/agent.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_agent_publishes_events.py`
- Commands run:
  - `uv run pytest tests/test_agent_publishes_events.py -v` (RED: unexpected `broker` keyword)
  - `uv run pytest tests/test_agent_publishes_events.py tests/test_api_agent_snapshot.py tests/test_api_agent_heartbeat.py -v`
- Result: 9 tests passed.
- Next step: implement tab classification and card view-models.

## 2026-05-19 - Checkpoint 4

- Checkpoint: Tab classification and card view-models.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/tabs.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/cards.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_tabs.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_cards.py`
- Commands run:
  - `uv run pytest tests/test_web_tabs.py tests/test_web_cards.py -v`
- Result: 6 tests passed.
- Next step: dashboard route/templates and card partial.

## 2026-05-19 - Checkpoint 5

- Checkpoint: Dashboard UI.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/base.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/dashboard.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/project_card.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/partials/presence_chip.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_dashboard_render.py`
- Commands run:
  - `uv run pytest tests/test_web_dashboard_render.py -v` (RED: `attach_web_routes` signature)
  - `uv run pytest tests/test_web_dashboard_render.py tests/test_web_routes.py tests/test_main_app.py -v`
- Result: 7 tests passed.
- Next step: project detail page, activity timeline, and parallel lane rendering.

## 2026-05-19 - Checkpoint 6

- Checkpoint: Detail UI and parallel lanes.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/details.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/project_detail.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/partials/cp_timeline.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/partials/activity_timeline.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/partials/parallel_lane.html`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_project_detail.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_parallel_lane.py`
- Commands run:
  - `uv run pytest tests/test_web_project_detail.py tests/test_web_parallel_lane.py -v` (RED: missing detail route)
  - `uv run pytest tests/test_web_project_detail.py tests/test_web_parallel_lane.py tests/test_web_dashboard_render.py -v`
- Result: 8 tests passed.
- Next step: client JS/CSS, htmx asset, and realtime smoke test.

## 2026-05-19 - Checkpoint 7

- Checkpoint: Client realtime and smoke.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.js`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/htmx.min.js`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_smoke_realtime.py`
- Commands run:
  - `curl -L https://unpkg.com/htmx.org@2/dist/htmx.min.js -o app/web/static/htmx.min.js`
  - `uv run pytest tests/test_web_smoke_realtime.py tests/test_sse_route.py tests/test_agent_publishes_events.py -v`
- Result: 6 tests passed.
- Next step: docs and final verification.

## 2026-05-19 - Checkpoint 8

- Checkpoint: Docs.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/deploy.md`
- Commands run: none.
- Result: Plan 3 dashboard/detail/SSE usage and production checks documented.
- Next step: full verification.

## 2026-05-19 - Checkpoint 9

- Checkpoint: Final verification.
- Commands run:
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv sync --extra dev && uv run pytest -v`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .`
- Result:
  - Server tests: 66 passed, 2 warnings.
  - Agent tests: 31 passed.
  - Server lint: all checks passed.
  - Agent lint: all checks passed.
- Notes:
  - Agent dev dependencies now include `sse-starlette` because its E2E test imports the server app.
  - Server warnings are existing Starlette TestClient cookie deprecation warnings in auth session tests.
  - `wily-board` still contains pre-existing Plan 2 dirty files and the untracked `agent/` package.
