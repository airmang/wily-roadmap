# Stage 28 Board Read-Only Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Wily Board a read-only Next.js surface by removing legacy Jinja rendering, board status mutation actions, and PR-opening UI/routes.

**Architecture:** The Wily Roadmap marketplace repo owns Stage 28 state, but the code changes happen in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`. FastAPI keeps auth, read-only JSON APIs, SSE, signed live ingest, GitHub webhook sync, and admin resync; Next.js owns user-facing `/`, `/me`, `/collab`, and `/repos/{owner}/{name}` surfaces. Legacy Jinja and `/actions/phase/status` are deleted after regression tests prove no read-only invariant was weakened.

**Tech Stack:** FastAPI, SQLite, pytest, Next.js 15 App Router, TypeScript, ESLint, Caddy.

---

## Current Facts

- Wily Stage: `s28` in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/stages/s28-board-readonly-cutover`.
- Target repo: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- Target repo is already dirty:
  - `app/api/routes.py`
  - `frontend/app/repos/[owner]/[name]/page.tsx`
  - `frontend/components/phase-list.tsx`
  - `frontend/lib/api.ts`
  - `frontend/lib/types.ts`
  - `tests/test_api_routes.py`
  - untracked `frontend/app/repos/[owner]/[name]/stages/`
- Preserve those existing changes. Re-check `git status --short` before editing and do not reset or checkout files.
- No repo-local `AGENTS.md` was found in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`; `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/AGENTS.md` still governs the plan artifact in this repo.

## Parallelization Decision

The Stage 28 roadmap currently records a serial dependency chain: `28-1 -> 28-2 -> 28-3 -> 28-4`. Keep Wily status transitions serial unless the roadmap is explicitly replanned.

Execution can still use bounded parallel lanes after starting `s28/28-1`:

- Lane A, serial integration owner: remove Jinja/templates/actions and adjust FastAPI packaging/routing.
- Lane B, tests-only owner: prepare read-only invariant tests in `tests/test_readonly_invariants.py` and update expectations in existing tests. This can run in parallel with Lane A because its write scope is tests only.
- Lane C, ops/docs reviewer: inspect `frontend/next.config.ts`, `deploy/Caddyfile`, and `docs/OPERATIONS.md` for route cutover consistency. This is read-only until Lane A settles; any doc patch should wait for integration.

Do not parallel-edit `app/main.py`, `app/web/routes.py`, or `app/actions/*`; those files overlap across `28-1`, `28-2`, and `28-3`.

## File Structure

### Wily Roadmap Repo

- Modify only through Wily commands during execution:
  - `.wily/roadmap.yaml`
  - `.wily/stages/s28-board-readonly-cutover/stage.yaml`
  - `.wily/sessions/**`
- This plan file:
  - `docs/superpowers/plans/2026-05-18-stage-28-board-readonly-cutover.md`

### Wily Board Repo

- Delete:
  - `app/web/templates/board.html`
  - `app/web/templates/repo_detail.html`
  - `app/web/templates/_phase_row.html`
  - `app/web/templates/base.html`
  - `app/web/templates/_toast.html`
  - `app/web/static/app.css`
  - `app/web/routes.py`
  - `app/actions/routes.py`
  - `app/actions/toggle_status.py`
  - `app/actions/pr_writer.py`
- Modify:
  - `app/main.py`: remove static mount, `asset_version`, `web_router`, PR writer initialization/imports, and action dependency wiring.
  - `pyproject.toml`: remove Jinja dependency only if no other import requires it; remove package-data entries for deleted web assets.
  - `tests/test_web_routes.py`: remove Jinja/web UI assertions and keep only auth/health/OAuth tests that still apply.
  - `tests/test_action_routes.py`, `tests/test_toggle_status.py`, `tests/test_pr_writer.py`: delete or replace with read-only invariant coverage.
  - `tests/test_packaging.py`: update package-data expectations if it asserts `web/templates` or `web/static`.
  - `deploy/Caddyfile`: confirm all non-backend paths proxy to Next.js; no change if current backend matcher stays `/api/* /auth/* /webhooks/* /admin/* /healthz /static/*`.
  - `docs/OPERATIONS.md`: update only if it still documents Jinja or `/actions/phase/status`.
- Create:
  - `tests/test_readonly_invariants.py`: route and import-level read-only guard tests.

---

## Task 1: Start and Snapshot `s28/28-1`

**Files:**
- Modify through Wily command: `.wily/stages/s28-board-readonly-cutover/stage.yaml`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`

- [ ] **Step 1: Start the executable phase**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py start s28/28-1
```

Expected: a new `.wily/sessions/<timestamp>-phase-28-1-attempt-1/` path and `28-1` marked `in_progress`.

- [ ] **Step 2: Read the session input**

Run:

```bash
latest_session=$(ls -td .wily/sessions/*phase-28-1* | head -1)
sed -n '1,240p' "$latest_session/input.md"
```

Expected: it names Stage 28, Phase `28-1`, target scope, and verification notes.

- [ ] **Step 3: Snapshot target repo state**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

```bash
git status --short
rg -n "TemplateResponse|Jinja2Templates|toggle_status|pr_writer|Open PR|new_status|/actions/phase/status" app tests frontend
```

Expected: dirty files are preserved; legacy Jinja/action references are visible before removal.

---

## Task 2: Add Failing Read-Only Invariant Tests

**Files:**
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_readonly_invariants.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_action_routes.py`

- [ ] **Step 1: Create route invariant tests**

Create `tests/test_readonly_invariants.py` with:

```python
from fastapi.testclient import TestClient

from app.main import create_app


ALLOWED_WRITE_ROUTES = {
    "/api/live/events",
    "/webhooks/github",
    "/admin/repos/{owner}/{name}/resync",
}


def test_board_exposes_no_user_facing_mutation_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "board.sqlite"))
    app = create_app()

    detected = []
    for route in app.routes:
        methods = getattr(route, "methods", set()) or set()
        path = getattr(route, "path", "")
        write_methods = methods & {"POST", "PUT", "PATCH", "DELETE"}
        if write_methods and path not in ALLOWED_WRITE_ROUTES:
            detected.append((path, sorted(write_methods)))

    assert detected == []


def test_legacy_action_route_is_gone(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "board.sqlite"))
    client = TestClient(create_app())

    response = client.post(
        "/actions/phase/status",
        data={
            "repo": "R-W-LAB/wily-roadmap",
            "base_branch": "main",
            "file_path": ".wily/stages/s28/stage.yaml",
            "phase_id": "28-1",
            "new_status": "done",
        },
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify current failure**

Run:

```bash
uv run pytest tests/test_readonly_invariants.py -q
```

Expected now: FAIL because `/actions/phase/status` is still mounted.

- [ ] **Step 3: Convert old web/action assertions**

In `tests/test_web_routes.py`, replace `test_repo_detail_renders_phase_status_pr_form` with:

```python
def test_repo_detail_path_is_no_longer_served_by_fastapi_templates(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "board.sqlite"))
    app = create_app()
    sid = create_oauth_session(app.state.db, "airmang", 1)
    client = TestClient(app)

    response = client.get(
        "/repos/R-W-LAB/wily-roadmap",
        cookies={"wily_board_sid": sid},
        follow_redirects=False,
    )

    assert response.status_code == 404
```

In `tests/test_action_routes.py`, keep only:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_status_action_route_is_not_mounted_after_read_only_cutover(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "board.sqlite"))
    client = TestClient(create_app())

    response = client.post(
        "/actions/phase/status",
        data={
            "repo": "R-W-LAB/wily-roadmap",
            "base_branch": "main",
            "file_path": ".wily/stages/s28/stage.yaml",
            "phase_id": "28-1",
            "new_status": "done",
        },
        headers={"hx-request": "true"},
    )

    assert response.status_code == 404
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
uv run pytest tests/test_readonly_invariants.py tests/test_action_routes.py tests/test_web_routes.py -q
```

Expected now: FAIL on legacy route/template behavior until Tasks 3-5 remove it.

---

## Task 3: Remove Legacy Jinja Templates (`28-1`)

**Files:**
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/*.html`
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/static/app.css`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
- Modify tests that directly assert template/static packaging.

- [ ] **Step 1: Delete template/static assets**

Remove:

```text
app/web/templates/board.html
app/web/templates/repo_detail.html
app/web/templates/_phase_row.html
app/web/templates/base.html
app/web/templates/_toast.html
app/web/static/app.css
```

- [ ] **Step 2: Remove obsolete package data**

In `pyproject.toml`, change:

```toml
[tool.setuptools.package-data]
app = [
  "db/*.sql",
  "web/static/*",
  "web/templates/*.html",
]
```

to:

```toml
[tool.setuptools.package-data]
app = [
  "db/*.sql",
]
```

Keep `jinja2` in dependencies until Task 5 confirms no imports remain; remove it there.

- [ ] **Step 3: Run focused verification**

Run:

```bash
rg -n "web/templates|web/static|board.html|repo_detail.html|_phase_row.html|_toast.html|base.html|app.css" app tests pyproject.toml
uv run pytest tests/test_packaging.py tests/test_readonly_invariants.py -q
```

Expected: no runtime references to deleted template/static files; packaging tests pass or identify exact assertions to update.

- [ ] **Step 4: Complete Wily Phase 28-1 after verification**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` only after the focused verification passes:

```bash
python3 plugins/wily-roadmap/scripts/wily.py complete s28/28-1
```

Expected: `28-1` becomes `done`; `28-2` becomes the next executable phase.

---

## Task 4: Remove Write Actions and PR Mutator (`28-2`)

**Files:**
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/actions/routes.py`
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/actions/toggle_status.py`
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/actions/pr_writer.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
- Modify/Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_pr_writer.py`
- Modify/Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_toggle_status.py`

- [ ] **Step 1: Start Phase 28-2**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py start s28/28-2
```

Expected: session path for `28-2`, and `28-2` marked `in_progress`.

- [ ] **Step 2: Remove PR writer setup from `app/main.py`**

Delete these imports:

```python
from app.actions.pr_writer import GitHubAppPrApi, PullRequestWriter
from app.web.routes import router as web_router
```

Delete this initialization block:

```python
    github_app_api = GitHubAppPrApi(settings)
    app.state.github_client = GitHubClient(
        token_provider=github_app_api.installation_token_for_repo
    )
    app.state.pr_writer = PullRequestWriter(github_app_api)
```

Replace it with:

```python
    app.state.github_client = GitHubClient()
```

Delete static asset setup:

```python
    static_dir = Path(__file__).parent / "web" / "static"
    app.state.asset_version = str((static_dir / "app.css").stat().st_mtime_ns)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

Delete router include:

```python
    app.include_router(web_router())
```

Remove unused imports:

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
```

- [ ] **Step 3: Delete action implementation files**

Remove:

```text
app/actions/routes.py
app/actions/toggle_status.py
app/actions/pr_writer.py
```

Leave `app/actions/__init__.py` only if packaging needs the package; otherwise delete the empty package after confirming no imports remain.

- [ ] **Step 4: Delete action-unit tests**

Delete:

```text
tests/test_pr_writer.py
tests/test_toggle_status.py
```

Keep `tests/test_action_routes.py` as the route absence regression from Task 2.

- [ ] **Step 5: Run focused verification**

Run:

```bash
rg -n "toggle_status|pr_writer|PullRequestWriter|GitHubAppPrApi|/actions/phase/status|new_status|Open PR" app tests frontend
uv run pytest tests/test_action_routes.py tests/test_readonly_invariants.py tests/test_config.py tests/test_webhook.py -q
```

Expected: no legacy action or PR mutator references; focused tests pass.

- [ ] **Step 6: Complete Wily Phase 28-2**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py complete s28/28-2
```

Expected: `28-2` becomes `done`; `28-3` becomes next.

---

## Task 5: Cut FastAPI Web Routes Over to Next.js (`28-3`)

**Files:**
- Delete: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/__init__.py` or delete `app/web/` if empty.
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
- Review: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/next.config.ts`
- Review: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/deploy/Caddyfile`

- [ ] **Step 1: Start Phase 28-3**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py start s28/28-3
```

Expected: session path for `28-3`, and `28-3` marked `in_progress`.

- [ ] **Step 2: Delete FastAPI web route module**

Remove:

```text
app/web/routes.py
```

If `app/web/` is empty except `__init__.py`, delete `app/web/__init__.py` and the directory.

- [ ] **Step 3: Remove Jinja dependency after imports are gone**

In `pyproject.toml`, remove:

```toml
  "jinja2>=3.1.0",
```

Keep `python-multipart` only if another route still uses `Form`; after action routes are gone, run:

```bash
rg -n "Form\\(|python-multipart|Jinja2Templates|TemplateResponse|fastapi.templating" app tests pyproject.toml
```

If `Form(` has no remaining application import, remove:

```toml
  "python-multipart>=0.0.20",
```

- [ ] **Step 4: Confirm route ownership**

Expected `frontend/next.config.ts` keeps:

```ts
{
  source: "/api/:path*",
  destination: `${apiUrl}/api/:path*`,
},
{
  source: "/auth/:path*",
  destination: `${apiUrl}/auth/:path*`,
},
{
  source: "/webhooks/:path*",
  destination: `${apiUrl}/webhooks/:path*`,
},
```

Expected `deploy/Caddyfile` keeps backend paths constrained to:

```caddy
@backend {
	path /api/* /auth/* /webhooks/* /admin/* /healthz /static/*
}
reverse_proxy @backend 127.0.0.1:8000

reverse_proxy 127.0.0.1:3000
```

If `/static/*` is no longer needed by FastAPI, remove it from the backend matcher only after confirming Next.js static asset paths are not affected.

- [ ] **Step 5: Run focused verification**

Run:

```bash
rg -n "Jinja2Templates|TemplateResponse|app.web.routes|web_router|status_actions|/static/app.css" app tests frontend pyproject.toml
uv run pytest tests/test_web_routes.py tests/test_readonly_invariants.py tests/test_api_routes.py tests/test_live_events.py -q
```

Expected: no Jinja/template route references; API/live tests still pass.

- [ ] **Step 6: Complete Wily Phase 28-3**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py complete s28/28-3
```

Expected: `28-3` becomes `done`; `28-4` becomes next.

---

## Task 6: Final Read-Only Regression and Frontend Smoke (`28-4`)

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_readonly_invariants.py`
- Review/modify if needed: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- Review/modify if needed: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/page.tsx`

- [ ] **Step 1: Start Phase 28-4**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py start s28/28-4
```

Expected: session path for `28-4`, and `28-4` marked `in_progress`.

- [ ] **Step 2: Extend invariant tests to source text**

Append to `tests/test_readonly_invariants.py`:

```python
from pathlib import Path


FORBIDDEN_SOURCE_TOKENS = (
    "Open PR",
    'name="new_status"',
    "hx-post=\"/actions/phase/status\"",
    'action="/actions/phase/status"',
    "replace_phase_status",
    "create_status_pr",
)


def test_source_contains_no_legacy_mutation_ui_or_helpers():
    root = Path(__file__).resolve().parents[1]
    searchable = [
        *(root / "app").rglob("*.py"),
        *(root / "frontend").rglob("*.tsx"),
        *(root / "frontend").rglob("*.ts"),
    ]

    offenders = []
    for path in searchable:
        if ".next" in path.parts or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_SOURCE_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(root)}: {token}")

    assert offenders == []
```

- [ ] **Step 3: Run backend full suite**

Run:

```bash
uv run pytest -q
```

Expected: all backend tests pass.

- [ ] **Step 4: Run frontend checks**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend`:

```bash
npm run lint
npm run build
```

Expected: lint and production build pass.

- [ ] **Step 5: Optional local smoke when servers are available**

Run backend and frontend locally, then check:

```bash
curl -I http://127.0.0.1:3000/
curl -I http://127.0.0.1:3000/repos/R-W-LAB/wily-roadmap
curl -I http://127.0.0.1:8000/
```

Expected:

- Next.js serves `/` and `/repos/R-W-LAB/wily-roadmap`.
- FastAPI `/` returns `404` or is not exposed directly through production routing.
- `/api/*`, `/auth/*`, `/webhooks/*`, `/admin/*`, `/healthz` remain backend-owned.

- [ ] **Step 6: Complete Wily Phase 28-4 and Stage 28**

Run from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py complete s28/28-4
```

Expected: `28-4` becomes `done`; Stage `s28` shows `4/4 phases`.

---

## Final Verification Matrix

Run in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

```bash
rg -n "Jinja2Templates|TemplateResponse|toggle_status|pr_writer|PullRequestWriter|GitHubAppPrApi|/actions/phase/status|new_status|Open PR|web/templates|web/static" app tests frontend pyproject.toml
uv run pytest -q
```

Expected:

- `rg` returns no legacy mutation/Jinja references outside this plan-independent documentation, if any docs are intentionally left.
- `uv run pytest -q` passes.

Run in `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend`:

```bash
npm run lint
npm run build
```

Expected: both pass.

Run in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Expected: Stage 28 shows done after all four phases complete.

## Commit Policy

Do not commit automatically. After verification, summarize diffs across both repos and wait for explicit commit/push approval.

Recommended commit grouping after approval:

1. Wily Board code/test cutover commit in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
2. Wily Roadmap durable state commit in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`.

## Self-Review

- Spec coverage: covers template deletion, action/PR mutator deletion, route ownership cutover, backend invariant tests, frontend smoke, and deployment proxy review.
- Red-flag scan: no deferred implementation slots or unspecified tests remain.
- Type/path consistency: Phase IDs match Stage 28 (`28-1` through `28-4`); target code paths are under `/Users/wilycastle/Code/projects/wily-plugin/wily-board`; Wily state paths are under `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`.
