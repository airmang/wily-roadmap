# Wily Board Collaboration Ops Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Wily Board into a practical collaboration operating surface by adding fresh-claim conflict warnings, a review/awaiting-push queue, and repository sync health.

**Architecture:** Keep Board read-mostly and local-first. Reuse `live_sessions`, `events`, `repos.last_synced_at`, durable phase status, and existing Jinja dashboard routes. Add focused query helpers in `app/db/repo.py`; render compact dashboard sections in `board.html`; keep CLI warnings best-effort through the signed Board live endpoint without making local Wily commands depend on Board availability.

**Tech Stack:** FastAPI, SQLite, Jinja/htmx, Python stdlib CLI, pytest/unittest.

---

## Task 1: Claim Conflict Warnings

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/_phase_row.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`
- Modify: `plugins/wily-roadmap/scripts/wily.py`
- Modify: `plugins/wily-roadmap/tests/test_wily_cli.py`

- [ ] Write failing Board DB tests for detecting two fresh actors on the same `repo_id` + `stage_id` + `phase_id`.
- [ ] Write failing Board route tests proving multi-actor conflicts render a visible warning and stale actors are ignored.
- [ ] Write failing Wily CLI tests proving `start` prints a warning when Board reports a fresh claim by another actor.
- [ ] Implement freshness-aware conflict query helpers.
- [ ] Render conflict chips on repo detail and active/up-next rows without changing durable roadmap status.
- [ ] Add an optional `GET /api/live/claims/{repo}/{phase_id}` style read endpoint or equivalent helper used by Wily CLI before start.
- [ ] Keep CLI warning best-effort: Board unavailable must not fail `start`.
- [ ] Verify targeted Board and Wily CLI tests.

## Task 2: Review And Awaiting-Push Queue

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Write failing DB tests for a follow-up queue containing `completed_local`, durable `needs_review`, blocked-local review items, and PR-open rows.
- [ ] Write failing route tests proving the queue appears on the dashboard and links to repo detail anchors.
- [ ] Implement `list_review_queue` with freshness labels, repo identity, phase identity, owner, status, live actor, and optional PR URL field.
- [ ] Render a compact `Needs follow-up` section below Active right now.
- [ ] Ensure durable `done` items disappear after sync confirmation by relying on existing live clear behavior.
- [ ] Verify Board DB and route tests.

## Task 3: Repository Sync Health Panel

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Write failing DB tests classifying repo health as `ok`, `stale`, or `not_initialized`.
- [ ] Write failing route tests proving missing `.wily` state and stale sync time are visible.
- [ ] Implement `list_repo_health` using `repos.last_synced_at`, stage counts, and latest sync event records.
- [ ] Render a read-only `Sync health` dashboard section with compact status chips.
- [ ] Verify Board DB and route tests.

## Task 4: Collaboration Ops Polish And Verification

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/status.md`
- Modify: Board templates/CSS only if visual polish is required by tests or QA.

- [ ] Document conflict warnings, follow-up queue, and sync health in operations docs.
- [ ] Run a local multi-repo Board smoke with one active conflict, one completed-local queue item, one initialized repo, and one uninitialized repo.
- [ ] Run full Board tests.
- [ ] Run Wily CLI tests.
- [ ] Run compile checks for touched Python files.
- [ ] Complete Stage 18 only after all four phases are `done` and final audit confirms the Stage acceptance criteria.

## Completion Criteria

- Stage 18 child phases 18-1 through 18-4 are `done`.
- Board warns on fresh multi-actor claims and ignores stale claims.
- Wily CLI `start` reports remote fresh-claim warnings without failing local start.
- Dashboard includes a follow-up queue for completed-local, needs-review, and awaiting-push work.
- Dashboard includes read-only sync health for initialized, stale, and missing-roadmap repositories.
- Board tests pass.
- Wily CLI tests pass.
- A local smoke confirms the collaboration surfaces work together.
