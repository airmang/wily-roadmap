# Wily Board Live Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show local Wily work activity on Wily Board before push while keeping committed `.wily` state authoritative.

**Architecture:** Wily Board stores provisional live work in `live_sessions` and accepts signed live events through a new API router. Durable GitHub sync remains the source of truth and clears matching live overlays when committed state catches up. Wily CLI later emits best-effort signed events only when opt-in Board config exists.

**Tech Stack:** FastAPI, SQLite, htmx/Jinja, pytest, Wily Python CLI.

---

## File Structure

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`: add `live_sessions`.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`: add live session upsert/list/clear helpers and call clear logic from `replace_repo_state`.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`: new signed live event router.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`: include live event router.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`: API and DB behavior tests.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`: durable sync clear behavior tests.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`: later join live overlays into dashboard and repo detail queries.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/_phase_row.html`: later render live chips.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`: later emit signed best-effort live events.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`: later test no-config and configured live event behavior.

## Task 1: Board Storage And Signed Live Event API

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] **Step 1: Write failing live event API tests**

Add tests that:

- create a Board app with a known `WILY_BOARD_SECRET`;
- post an invalid signature to `/api/live/events` and expect `401`;
- post a valid signed start event and expect `{"stored": true}`;
- verify the live session row was stored with actor, phase id, status, and session path;
- verify durable stages/phases remain unchanged.

Run:

```sh
uv run pytest tests/test_live_events.py -v
```

Expected: fails because `app.live.events` and `/api/live/events` do not exist.

- [ ] **Step 2: Implement live session schema and DB helpers**

Add `live_sessions` to `schema.sql`.

Add helpers in `app/db/repo.py`:

- `upsert_live_session(conn, repo_id, payload)`
- `list_live_sessions(conn, repo_id=None)`
- `clear_confirmed_live_sessions(conn, repo_id, stages)`

Run:

```sh
uv run pytest tests/test_live_events.py -v
```

Expected: still fails until the router exists.

- [ ] **Step 3: Implement signed live event router**

Create `app/live/events.py`.

The router:

- verifies `X-Wily-Signature` using existing `verify_signature`;
- validates required payload fields: `repo`, `phase_id`, `actor`, `event`, `live_status`;
- looks up repo by owner/name;
- calls `upsert_live_session`;
- records an `events` row with kind `live_event`;
- returns `{"stored": true}`.

Include the router in `app/main.py`.

Run:

```sh
uv run pytest tests/test_live_events.py -v
```

Expected: pass.

- [ ] **Step 4: Add durable sync clearing tests**

Extend DB tests so a `completed_local` live session is cleared when `replace_repo_state` stores a matching phase with durable status `done`.

Run:

```sh
uv run pytest tests/test_db.py -v
```

Expected: fails before clear logic exists, then passes after implementation.

- [ ] **Step 5: Run phase verification**

Run:

```sh
uv run pytest tests/test_live_events.py tests/test_db.py tests/test_webhook.py
uv run python -m py_compile app/db/repo.py app/sync/webhook.py app/live/events.py app/main.py
```

Expected: all selected checks pass.

## Task 2: Board Live Overlay Query And UI Chips

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/_phase_row.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Add failing tests for repo detail live chip rendering.
- [ ] Add failing tests for Active right now including fresh live sessions.
- [ ] Add live overlay query helpers and route context.
- [ ] Render chips as provisional text, not durable status.
- [ ] Verify with web route tests.

## Task 3: Wily CLI Best-Effort Event Emission

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`

- [ ] Add failing tests proving no network call occurs without Board config.
- [ ] Add failing tests for signed payload generation when Board config exists.
- [ ] Emit events from `command_start`, `command_block`, and `command_complete` after successful local writes.
- [ ] Keep Board failures best-effort and non-fatal.
- [ ] Verify Wily CLI tests.

## Task 4: Operations And End-To-End Verification

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/docs/superpowers/specs/2026-05-16-wily-board-live-overlay-review-ko.md` only if behavior changes from the approved design.

- [ ] Document local and production live sync environment variables.
- [ ] Verify start, block, complete, stale, and push-clear flows locally.
- [ ] Record verification evidence in the active Wily session.

## Self-Review

- Spec coverage: Task 1 covers storage/API/sync clear, Task 2 covers Board display, Task 3 covers Wily CLI emission, Task 4 covers operations and end-to-end verification.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: live status names match the design spec: `claimed`, `active`, `blocked_local`, `completed_local`, `stale`, `cleared`.
