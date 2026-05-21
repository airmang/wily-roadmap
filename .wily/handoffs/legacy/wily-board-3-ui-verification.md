# Wily Board Plan 3 UI SSE Realtime Verification

Verification evidence will be appended checkpoint-by-checkpoint.

## 2026-05-19 - SSE Broker And Route

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_sse_broker.py tests/test_sse_route.py -v
```

Result: exit 0, 6 passed.

## 2026-05-19 - Final Verification

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v
```

Result: exit 0, 66 passed, 2 warnings.

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv sync --extra dev && uv run pytest -v
```

Result: exit 0, 31 passed.

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .
```

Result: exit 0, all checks passed.

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .
```

Result: exit 0, all checks passed.

## 2026-05-19 - Dashboard UI

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_web_dashboard_render.py tests/test_web_routes.py tests/test_main_app.py -v
```

Result: exit 0, 7 passed.

## 2026-05-19 - Detail UI And Lanes

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_web_project_detail.py tests/test_web_parallel_lane.py tests/test_web_dashboard_render.py -v
```

Result: exit 0, 8 passed.

## 2026-05-19 - Client Realtime Smoke

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_web_smoke_realtime.py tests/test_sse_route.py tests/test_agent_publishes_events.py -v
```

Result: exit 0, 6 passed.

## 2026-05-19 - Agent Event Publishing

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_agent_publishes_events.py tests/test_api_agent_snapshot.py tests/test_api_agent_heartbeat.py -v
```

Result: exit 0, 9 passed.

## 2026-05-19 - Tabs And Cards

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_web_tabs.py tests/test_web_cards.py -v
```

Result: exit 0, 6 passed.
