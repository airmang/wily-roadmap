# Wily Board Heartbeat Freshness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in heartbeat freshness so Wily Board can show active now, last seen, and stale local sessions without using LLM tokens.

**Architecture:** Reuse the existing signed live event endpoint and `live_sessions` table. Board classifies live sessions as fresh or stale from `last_seen_at` and configurable thresholds. Wily CLI adds an explicit `live-heartbeat` loop that sends `heartbeat`/`active` events on a safe interval and exits cleanly.

**Tech Stack:** FastAPI, SQLite, Jinja/htmx, Python stdlib CLI, pytest/unittest.

---

## Task 1: Board Heartbeat Contract And Freshness Model

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] Add failing tests proving `heartbeat` updates an existing live session to `active`.
- [ ] Add failing tests for fresh/stale classification from `last_seen_at`.
- [ ] Add settings for `LIVE_FRESH_SECONDS` and `LIVE_STALE_SECONDS`.
- [ ] Implement heartbeat validation and freshness helpers.
- [ ] Verify Board live event and DB tests.

## Task 2: Wily CLI Heartbeat Mode

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily.py`
- Modify: `plugins/wily-roadmap/tests/test_wily_cli.py`

- [ ] Add failing tests for `live-heartbeat` requiring a phase id.
- [ ] Add failing tests that heartbeat sends `event=heartbeat`, `live_status=active`.
- [ ] Add interval and count options for deterministic test/smoke execution.
- [ ] Keep Board failures best-effort and non-fatal.
- [ ] Verify Wily CLI tests and command skill references if needed.

## Task 3: Board Active Now And Stale UI

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/_phase_row.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Add failing tests showing fresh sessions render `active now`.
- [ ] Add failing tests showing stale sessions render `stale local session`.
- [ ] Ensure stale sessions do not block `Up next`.
- [ ] Render last-seen/freshness chips without changing durable status.
- [ ] Verify Board route tests.

## Task 4: Heartbeat Operations And Load Verification

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Modify: `.wily/status.md`

- [ ] Document heartbeat env vars, interval guidance, and load expectations.
- [ ] Run local Board server smoke with two heartbeat ticks.
- [ ] Run full Board tests.
- [ ] Run Wily CLI tests and compile checks.
- [ ] Complete Stage 17 only after objective audit passes.

## Completion Criteria

- Stage 17 child phases 17-1 through 17-4 are `done`.
- Board tests pass.
- Wily CLI tests pass.
- Local smoke proves CLI heartbeat reaches Board and updates `live_sessions`.
- `.wily/status.md` reflects Stage 17 completion.
