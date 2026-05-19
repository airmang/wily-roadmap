# Wily Board Risk View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact risk view that ranks blockers, dependency bottlenecks, stale work, awaiting-push items, and unclaimed ready work without LLM calls.

**Architecture:** Keep risk computation deterministic in `app/db/repo.py`. Reuse existing Board state: durable phase statuses/dependencies, live session freshness, and review queue data. Render only the highest-priority attention items on the dashboard as a quiet, linked list.

**Tech Stack:** FastAPI, SQLite, Jinja/htmx, pytest.

---

## Task 1: Risk Signal Model And Scoring

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] Write failing tests for deterministic risk severity ordering: blocker, dependency bottleneck, stale live session, awaiting push, unclaimed ready.
- [ ] Add a small risk item builder with stable fields: `risk_type`, `severity`, `reason`, `repo_owner`, `repo_name`, `stage_id`, `phase_id`, `phase_title`, and optional `pr_url`.
- [ ] Keep scores local-only and data-driven; do not call external analytics or LLMs.
- [ ] Verify targeted DB tests.

## Task 2: Critical Path And Bottleneck Queries

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] Write failing tests for blocked phases, high-fanout dependency blockers, ready-but-unclaimed phases, stale live sessions, and awaiting-push live sessions.
- [ ] Implement `list_risk_items` by composing durable phase queries, live freshness checks, dependency fanout counts, and `list_review_queue`.
- [ ] Limit to a compact top-N result set sorted by severity then repo/stage/phase.
- [ ] Verify DB tests.

## Task 3: Risk View UI

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Write failing route tests proving dashboard renders ranked risk items with reason text and repo/phase links.
- [ ] Write failing route tests proving clean boards show a quiet empty state.
- [ ] Pass `risk_items` from the route to `board.html`.
- [ ] Render a compact `Attention` section near the top of the dashboard.
- [ ] Verify Board route tests.

## Task 4: Risk View Verification And Tuning

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/status.md`

- [ ] Document the risk view and its deterministic ranking.
- [ ] Run a local Board smoke with blocked, stale, awaiting-push, and unclaimed-ready scenarios.
- [ ] Run full Board tests.
- [ ] Run compile checks for touched Python files.
- [ ] Complete Stage 19 only after all child phases are `done` and final audit confirms Stage acceptance criteria.

## Completion Criteria

- Stage 19 child phases 19-1 through 19-4 are `done`.
- Risk signals cover blockers, dependency bottlenecks, stale sessions, awaiting-push local completions, and unclaimed ready work.
- Dashboard renders ranked attention items and a quiet empty state.
- Board tests pass.
- Local smoke confirms predictable multi-repo ranking.
