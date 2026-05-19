# Wily Board Personal Shared Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `airmang` see shared repositories plus personal repositories while `Julirsia` sees only shared collaboration repositories.

**Architecture:** Add two fields to `repos`: `visibility` and `visible_to`. Keep the model intentionally small: shared repos are visible to all allowed logins; personal repos are visible only to their configured owner. Apply filtering in Board query helpers and direct repo detail routes; ingestion remains able to store any configured repo.

**Tech Stack:** FastAPI, SQLite, Jinja/htmx, pytest.

---

## Task 1: Repo Visibility Fields And Config Contract

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] Write failing tests for `PERSONAL_REPOS=owner/name:login` parsing.
- [ ] Write failing tests proving new repos default to `shared` and optional `visible_to` persists.
- [ ] Add schema columns with safe defaults.
- [ ] Update repo upsert to accept `visibility` and `visible_to` without breaking existing callers.
- [ ] Seed personal repos from config during app startup.
- [ ] Verify config and DB tests.

## Task 2: Login-Scoped Filtering And Access Control

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Write failing DB tests for shared visibility and personal visibility by login.
- [ ] Write failing route tests proving `Julirsia` cannot see or directly open `airmang` personal repos.
- [ ] Apply repo visibility filtering to dashboard query helpers.
- [ ] Return a non-exposing 404 for unauthorized direct repo detail URLs.
- [ ] Keep sync/live ingestion unfiltered.
- [ ] Verify Board tests.

## Task 3: Simple Shared And Mine Filters

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] Write failing route tests for `filter=all`, `filter=shared`, and `filter=mine`.
- [ ] Keep existing owner filters only if they do not conflict with the simpler shared/mine model.
- [ ] Render All, Shared, and Mine segmented filters.
- [ ] Ensure `Mine` includes personal repos visible to the login and login-owned phase work.
- [ ] Verify route tests.

## Task 4: Personal Repo Onboarding Docs And Verification

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/status.md`

- [ ] Document `PERSONAL_REPOS` setup and examples.
- [ ] Run smoke proving `airmang` sees shared + personal.
- [ ] Run smoke proving `Julirsia` sees shared only and direct personal URL returns 404.
- [ ] Run full Board tests and compile checks.
- [ ] Complete Stage 20 and final roadmap QA only after all remaining stages are `done`.

## Completion Criteria

- Stage 20 child phases 20-1 through 20-4 are `done`.
- Existing repos remain shared by default.
- Personal repo config maps repo full names to one login.
- `airmang` sees shared plus personal repos.
- `Julirsia` sees shared repos only.
- Unauthorized direct repo URLs do not expose personal repo details.
- Board tests pass.
- Final QA covers all completed Stage 18-20 surfaces together.
