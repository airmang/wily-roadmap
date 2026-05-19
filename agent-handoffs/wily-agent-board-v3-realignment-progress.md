# Wily Agent Board V3 Realignment Progress

## 2026-05-19 - Execution package

Created the execution package, status board, and verification log placeholder for the approved direction:

- `wily-roadmap` owns the bundled `wily-agent`.
- `wily-board` owns `/agent/*` ingest and display cache behavior.

Next:
- Add failing roadmap tests for snapshot payload and CLI aliases.

## 2026-05-19 - Roadmap agent red/green

Files changed:
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/scripts/wily/agent/config.py`
- `plugins/wily-roadmap/scripts/wily/agent/registry.py`
- `plugins/wily-roadmap/scripts/wily/agent/snapshot.py`
- `plugins/wily-roadmap/scripts/wily/agent/client.py`
- `plugins/wily-roadmap/scripts/wily/agent/daemon.py`
- `plugins/wily-roadmap/scripts/wily/cli/agent.py`

Red tests:
- Missing `build_snapshot_payload` / `snapshot_sha`.
- Missing `login`, `unregister`, and `run` in `wily agent --help`.

Implemented:
- Board v3 snapshot payload builder with local `.wily` tasks, actors, progress summaries, checkpoint events, result Markdown, project Markdown, observed git commits, `project_id`, `remote_url`, `local_path`, and stable `snapshot_sha`.
- Agent config support for bearer token and machine id while preserving existing HMAC live-event config.
- CLI `login`, `unregister`, and `run` aliases.
- Daemon tick publishes snapshot and heartbeat through token endpoints when logged in, falling back to the legacy signed live event when only HMAC config exists.
- Long-running daemon loop polls `.wily` mtimes, debounces local changes, emits 5-second heartbeats by default, and forces snapshot refresh at least every 60 seconds.

Verification:
- `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state plugins.wily-roadmap.tests.v3.test_v3_core.CliLifecycleTest.test_agent_cli_dispatch_lists_lifecycle_subcommands`
- Result: PASS.

Next:
- Add failing Board `/agent/*` API tests.

## 2026-05-19 - Board agent API red/green

Files changed:
- `/Users/wilycastle/Code/projects/wily-board/tests/test_agent_routes.py`
- `/Users/wilycastle/Code/projects/wily-board/app/api/agent.py`
- `/Users/wilycastle/Code/projects/wily-board/app/config.py`
- `/Users/wilycastle/Code/projects/wily-board/app/db/schema.sql`
- `/Users/wilycastle/Code/projects/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-board/app/main.py`

Red tests:
- `/agent/register`, `/agent/snapshot`, and `/agent/heartbeat` returned 404.

Implemented:
- Isolated `app.api.agent` router mounted at `/agent`.
- Bootstrap-code machine registration that returns bearer token and stores hashed token.
- Snapshot endpoint that projects Wily v3 tasks into the existing Board stage/phase cache and stores `project_machines`, `task_snapshots`, and presence.
- Heartbeat endpoint that updates `actor_presence`.

Verification:
- `uv run pytest tests/test_agent_routes.py -q`
- Result: `3 passed`.

Next:
- Update design and plugin docs for the approved ownership model.

## 2026-05-19 - Docs realignment

Files changed:
- `docs/superpowers/specs/2026-05-19-wily-board-v3-design.md`
- `plugins/wily-roadmap/README.md`
- `plugins/wily-roadmap/commands/agent.md`
- `plugins/wily-roadmap/skills/wily-agent/SKILL.md`
- `plugins/wily-roadmap/.codex-plugin/plugin.json`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `/Users/wilycastle/Code/projects/wily-board/README.md`

Implemented:
- Replaced the old `wily-board/agent` package direction with the approved `wily-roadmap` bundled agent ownership model.
- Clarified Board owns `/agent/*`, DB cache, and UI, but not the `.wily` client/daemon implementation.
- Updated plugin onboarding from `wily agent configure --secret` to `wily agent login` for the Board v3 token path, while documenting legacy signed live-event compatibility.

Next:
- Run focused and final verification.

## 2026-05-19 - Final verification

Commands run:
- `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface`
- `cd /Users/wilycastle/Code/projects/wily-board && uv run pytest tests/test_agent_routes.py -q`
- `cd /Users/wilycastle/Code/projects/wily-board && uv run ruff check app/api/agent.py tests/test_agent_routes.py`
- `cd /Users/wilycastle/Code/projects/wily-board && uv run pytest -q`
- `cd /Users/wilycastle/Code/projects/wily-board && uv run ruff check .`
- `git diff --check`
- `git -C /Users/wilycastle/Code/projects/wily-board diff --check`

Results after final daemon polling update:
- Roadmap unittest: 102 tests passed.
- Board focused agent routes: 3 tests passed.
- Board full pytest: 102 passed, 16 existing Starlette cookie deprecation warnings.
- Board ruff: all checks passed.
- Diff checks: passed in both repos.

State:
- DONE.
