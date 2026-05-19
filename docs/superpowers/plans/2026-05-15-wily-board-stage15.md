# Wily Board Stage 15 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy the separate `R-W-LAB/wily-board` dashboard for viewing multiple Wily repositories and creating safe PR-based status changes.

**Architecture:** `wily-board` is a separate FastAPI application. Each Wily repository remains the source of truth through `.wily/roadmap.yaml` and `.wily/stages/**/stage.yaml`; the board stores a SQLite cache and creates GitHub PRs for write actions. The app runs on the Azure VM behind Caddy with GitHub OAuth and a two-person whitelist.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, htmx, Pico.css, SQLite, pytest, uvicorn, systemd, Caddy, GitHub REST API.

---

## Fixed Inputs

- GitHub org: `R-W-LAB`
- Dashboard repo: `R-W-LAB/wily-board`
- Visibility: `private`
- URL: `https://rnwlab.duckdns.org`
- Azure SSH: `airman@20.17.177.129`
- Allowed GitHub logins: `airmang`, `Julirsia`
- Sync repositories:
  - `R-W-LAB/wily-roadmap`
  - `R-W-LAB/Digit`
  - `R-W-LAB/mac2win`
  - `R-W-LAB/BounceBall`

## File Structure

Create `/Users/wilycastle/Code/projects/wily-plugin/wily-board` as the separate application workspace.

- `pyproject.toml`: package metadata, dependencies, pytest config.
- `README.md`: architecture, setup, env vars, deployment, safety constraints.
- `.env.example`: non-secret configuration keys.
- `app/main.py`: FastAPI app factory and route registration.
- `app/config.py`: typed environment configuration and defaults.
- `app/auth/github.py`: OAuth URL/callback exchange, whitelist check, session helpers.
- `app/db/schema.sql`: SQLite schema for repos, stages, phases, events, oauth_sessions.
- `app/db/repo.py`: SQLite repository functions.
- `app/sync/signature.py`: HMAC signature generation/verification.
- `app/sync/parser.py`: parse Wily roadmap and stage YAML into DTOs.
- `app/sync/github_client.py`: GitHub REST file fetch helpers.
- `app/sync/webhook.py`: webhook and admin resync handlers.
- `app/actions/pr_writer.py`: GitHub App auth and PR creation.
- `app/actions/toggle_status.py`: targeted phase status replacement and action handler.
- `app/web/routes.py`: server-rendered HTML routes.
- `app/web/templates/*.html`: base, board, repo, stage, phase card.
- `app/web/static/app.css`: compact board styling and mobile rules.
- `deploy/install.sh`: Ubuntu bootstrap.
- `deploy/Caddyfile`: HTTPS reverse proxy.
- `deploy/wily-board.service`: systemd unit.
- `.github/workflows/wily-board-sync.yml`: reusable sync workflow template.
- `tests/`: focused unit and route tests.

## Execution Tasks

### Task 1: Repository Baseline

**Files:**
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/README.md`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/.env.example`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/__init__.py`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`

- [ ] **Step 1: Create failing config tests**

```python
from app.config import Settings


def test_settings_defaults_for_fixed_stage15_inputs(monkeypatch):
    monkeypatch.setenv("WILY_BOARD_HOST", "rnwlab.duckdns.org")
    monkeypatch.setenv("ALLOWED_GITHUB_LOGINS", "airmang,Julirsia")
    settings = Settings.from_env()
    assert settings.host == "rnwlab.duckdns.org"
    assert settings.url == "https://rnwlab.duckdns.org"
    assert settings.allowed_github_logins == ("airmang", "Julirsia")
```

- [ ] **Step 2: Run red test**

Run: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && python3 -m pytest tests/test_config.py -q`
Expected: FAIL because `app.config` does not exist.

- [ ] **Step 3: Implement baseline files and config**

Create `pyproject.toml`, `README.md`, `.env.example`, `app/config.py`, package init files, and test config parsing.

- [ ] **Step 4: Run green test**

Run: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && python3 -m pytest tests/test_config.py -q`
Expected: PASS.

### Task 2: Database Schema and Repository Layer

**Files:**
- Create: `app/db/schema.sql`
- Create: `app/db/repo.py`
- Test: `tests/test_db.py`

- [ ] **Step 1: Test schema creation and seed repos**

```python
from app.db.repo import connect, initialize, upsert_repo, list_repos


def test_schema_stores_initial_repositories(tmp_path):
    db = connect(tmp_path / "board.sqlite")
    initialize(db)
    upsert_repo(db, "R-W-LAB", "wily-roadmap", "main", "secret")
    rows = list_repos(db)
    assert rows[0]["owner"] == "R-W-LAB"
    assert rows[0]["name"] == "wily-roadmap"
```

- [ ] **Step 2: Run red test**

Run: `python3 -m pytest tests/test_db.py -q`
Expected: FAIL because db layer does not exist.

- [ ] **Step 3: Implement schema and repository helpers**

Use the schema from `docs/wily-board-plan.md` with indexes and cascade deletes.

- [ ] **Step 4: Run green test**

Run: `python3 -m pytest tests/test_db.py -q`
Expected: PASS.

### Task 3: Wily Parser and Sync Signature

**Files:**
- Create: `app/sync/parser.py`
- Create: `app/sync/signature.py`
- Test: `tests/test_parser.py`
- Test: `tests/test_signature.py`

- [ ] **Step 1: Test parsing current Wily stage schema**

Use fixtures copied from this repository's `.wily/roadmap.yaml` and `.wily/stages/s15-wily-board-external-dashboard/stage.yaml`. Assert stage `s15` and phase `15-1` parse correctly.

- [ ] **Step 2: Test webhook HMAC verification**

Assert `sign_payload(secret, body)` verifies with the same body and fails with a tampered body.

- [ ] **Step 3: Run red tests**

Run: `python3 -m pytest tests/test_parser.py tests/test_signature.py -q`
Expected: FAIL because parser/signature modules do not exist.

- [ ] **Step 4: Implement parser and signature helpers**

Use PyYAML for read-only parsing. Normalize `depends_on` to tuples and preserve raw paths.

- [ ] **Step 5: Run green tests**

Run: `python3 -m pytest tests/test_parser.py tests/test_signature.py -q`
Expected: PASS.

### Task 4: FastAPI App, Auth, and Web Routes

**Files:**
- Create: `app/main.py`
- Create: `app/auth/github.py`
- Create: `app/web/routes.py`
- Create: `app/web/templates/base.html`
- Create: `app/web/templates/board.html`
- Create: `app/web/templates/repo_detail.html`
- Create: `app/web/templates/stage_detail.html`
- Create: `app/web/templates/phase_card.html`
- Create: `app/web/static/app.css`
- Test: `tests/test_web_routes.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Test health and protected routes**

Assert `/healthz` returns `{"ok": true}`. Assert `/` redirects to GitHub auth without a session.

- [ ] **Step 2: Test whitelist auth logic**

Assert `airmang` and `Julirsia` are allowed and any other login is rejected.

- [ ] **Step 3: Run red tests**

Run: `python3 -m pytest tests/test_web_routes.py tests/test_auth.py -q`
Expected: FAIL because app/auth/web modules do not exist.

- [ ] **Step 4: Implement app, auth helpers, templates, and static CSS**

Implement server-rendered board, repo, and stage pages. Keep write controls disabled until PR writer config exists.

- [ ] **Step 5: Run green tests**

Run: `python3 -m pytest tests/test_web_routes.py tests/test_auth.py -q`
Expected: PASS.

### Task 5: Webhook, Backfill, and GitHub Fetch

**Files:**
- Create: `app/sync/github_client.py`
- Create: `app/sync/webhook.py`
- Modify: `app/main.py`
- Test: `tests/test_webhook.py`
- Test: `tests/test_resync.py`

- [ ] **Step 1: Test webhook verifies signature and upserts parsed data**

Use a fake GitHub client returning fixture files. Assert repos, stages, phases, and events are written.

- [ ] **Step 2: Test admin resync requires an authenticated admin session**

Assert unauthenticated resync returns redirect or 401, and admin session can run fake backfill.

- [ ] **Step 3: Run red tests**

Run: `python3 -m pytest tests/test_webhook.py tests/test_resync.py -q`
Expected: FAIL because webhook/backfill handlers do not exist.

- [ ] **Step 4: Implement webhook and resync**

Implement HMAC validation, repo allowlist, GitHub fetch abstraction, parser integration, DB upsert, and event logging.

- [ ] **Step 5: Run green tests**

Run: `python3 -m pytest tests/test_webhook.py tests/test_resync.py -q`
Expected: PASS.

### Task 6: PR Writer and Status Toggle

**Files:**
- Create: `app/actions/pr_writer.py`
- Create: `app/actions/toggle_status.py`
- Modify: `app/web/routes.py`
- Test: `tests/test_pr_writer.py`
- Test: `tests/test_toggle_status.py`

- [ ] **Step 1: Test targeted YAML replacement**

Assert changing phase `15-1` only changes that phase's `status:` line in `stage.yaml`.

- [ ] **Step 2: Test PR writer request construction**

Use a fake GitHub API client. Assert branch prefix, commit message, PR title, and PR body match the plan.

- [ ] **Step 3: Run red tests**

Run: `python3 -m pytest tests/test_pr_writer.py tests/test_toggle_status.py -q`
Expected: FAIL because actions modules do not exist.

- [ ] **Step 4: Implement status toggle and PR writer**

Implement GitHub App JWT, installation token exchange, branch creation, file update, and PR creation. Keep direct push to default branch impossible.

- [ ] **Step 5: Run green tests**

Run: `python3 -m pytest tests/test_pr_writer.py tests/test_toggle_status.py -q`
Expected: PASS.

### Task 7: Deployment and Sync Workflow

**Files:**
- Create: `deploy/install.sh`
- Create: `deploy/Caddyfile`
- Create: `deploy/wily-board.service`
- Create: `.github/workflows/wily-board-sync.yml`
- Test: `tests/test_deploy_files.py`

- [ ] **Step 1: Test generated deploy files contain fixed host and safe defaults**

Assert Caddyfile references `rnwlab.duckdns.org`, service runs one uvicorn worker, and install script creates `/var/lib/wily-board`.

- [ ] **Step 2: Run red test**

Run: `python3 -m pytest tests/test_deploy_files.py -q`
Expected: FAIL because deploy files do not exist.

- [ ] **Step 3: Implement deploy and workflow files**

Do not embed real secrets. Use environment files and GitHub Secrets references.

- [ ] **Step 4: Run green tests and static checks**

Run:

```bash
python3 -m pytest tests/test_deploy_files.py -q
sh -n deploy/install.sh
```

Expected: PASS.

### Task 8: Local Verification, Remote Setup, and Deployment

**Files:**
- Modify Wily state in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/**`
- Possibly create remote `R-W-LAB/wily-board`
- Possibly push branch and configure deployment.

- [ ] **Step 1: Run full local checks**

Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
python3 -m pytest -q
python3 -m py_compile $(find app -name '*.py' -print)
```

Expected: all tests pass.

- [ ] **Step 2: Create private GitHub repo**

Run: `gh repo create R-W-LAB/wily-board --private --source /Users/wilycastle/Code/projects/wily-plugin/wily-board --remote origin --push`
Expected: repo created or existing repo detected and remote configured.

- [ ] **Step 3: Stop if OAuth or GitHub App credentials are missing**

Ask the user for OAuth/App creation if CLI/API cannot create the needed credentials. Do not guess secrets.

- [ ] **Step 4: Deploy only after credentials and SSH succeed**

Run SSH bootstrap only after confirming credentials are available in server environment or a secure manual path exists.

- [ ] **Step 5: Verify live app**

Run:

```bash
curl -fsS https://rnwlab.duckdns.org/healthz
```

Expected: `{"ok":true}`.

## Self-Review

- Spec coverage: covers separate repo, FastAPI/SQLite/auth, sync/webhook/parser, PR writer, UI, deploy, and onboarding workflow.
- Remote/destructive guard: repo creation, server bootstrap, workflow/secret writes, OAuth/App credentials are approval-gated; approval has been granted, but missing credentials still require a stop.
- Known likely blocker: GitHub OAuth App and GitHub App creation may require browser/owner-level setup; stop and ask if `gh` cannot provision these values.
