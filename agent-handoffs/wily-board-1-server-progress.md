# Wily Board Plan 1 Server Foundation — Progress

## 2026-05-19 — Planning

- Checkpoint: execution package
- Files changed:
  - `agent-handoffs/wily-board-1-server-execution-package.md`
  - `agent-handoffs/wily-board-1-server-status.md`
  - `agent-handoffs/wily-board-1-server-progress.md`
  - `agent-handoffs/wily-board-1-server-verification.md`
- Commands run:
  - `git status --short` in `wily-roadmap`
  - `git status --short` in `wily-board`
  - plan/spec inspection commands
- Result: execution package initialized. Existing `wily-board` repo is clean and appears to be legacy v2 implementation.
- Next step: validate execution package, then prepare rewrite branch/scaffold.
- Blockers / risks: existing v2 repo requires careful branch/history preservation.

Auto-resolved under active /goal: Superpowers approval/review/continue gates -> continue with recorded evidence checkpoints unless a narrow hard-stop condition is reached.

## 2026-05-19 — Execution package validation and repo exploration

- Checkpoint: execution package / repo facts
- Files changed:
  - `agent-handoffs/wily-board-1-server-execution-package.md`
  - `agent-handoffs/wily-board-1-server-status.md`
  - `agent-handoffs/wily-board-1-server-progress.md`
- Commands run:
  - `python3 .../validate_execution_package.py agent-handoffs/wily-board-1-server-execution-package.md`
  - `git branch --show-current` in `wily-board`
  - `git branch --list --all` in `wily-board`
  - `git status --short` in `wily-board`
- Result:
  - Validator output: `PASS: execution package contract is complete.`
  - Current `wily-board` branch: `main`
  - Existing `wily-board` worktree: clean
  - Read-only explorer confirmed the existing repo is v2/stage-phase product and orphan rewrite fits Plan 1.
- Next step: create/switch to `feat/v3-rewrite` orphan branch and scaffold v3 files.
- Blockers / risks: avoid adding ignored generated dirs such as `.venv`, `frontend/node_modules`, `.next`, caches.

## 2026-05-19 — Implementation and review

- Checkpoint: server foundation/API implementation
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/.gitignore`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/uv.lock`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/deploy/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/deploy.md`
- Commands run:
  - `git checkout --orphan feat/v3-rewrite && git rm -rf .`
  - `uv sync --extra dev`
  - `uv run pytest -q`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run ruff check . && uv run ruff format --check . && uv run pytest -v`
  - `git commit --amend --no-edit`
- Result:
  - Created orphan branch `feat/v3-rewrite`.
  - Implemented FastAPI app, SQLite schema/migrator/repo, parser, merge policy, session/OAuth/org allowlist, machine mint, agent register/snapshot/heartbeat, web login/add-machine shell, deploy artifacts, README/deploy runbook.
  - Reviewer found OAuth allowlist/user upsert gap and Add machine shell gap; both fixed.
  - Commit: `cbe7e59 feat: scaffold wily-board v3 server foundation`.
- Final verification:
  - `uv run ruff check .`: pass.
  - `uv run ruff format --check .`: pass.
  - `uv run pytest -v`: 40 passed, 2 warnings.
- Blockers / risks:
  - Warnings are Starlette TestClient cookie deprecation warnings in session tests; not behavior failures.
  - No remote SSH/deploy performed.
