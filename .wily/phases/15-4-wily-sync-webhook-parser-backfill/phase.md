# Phase 15-4: Wily sync webhook, parser, and backfill

## Purpose

Ingest `.wily/` state from GitHub into Wily Board's SQLite cache through signed webhooks and manual backfill.

## Dependencies

- 15-3 FastAPI auth and SQLite skeleton

## Expected Output

- `/webhooks/github` verifies HMAC signatures and accepted repositories.
- GitHub contents or archive fetch retrieves `.wily/roadmap.yaml` and `.wily/stages/**/stage.yaml`.
- Parser maps Stage and Phase state into SQLite upserts.
- `/admin/repos/{owner}/{name}/resync` can rebuild cache from default branch.
- Events record sync and backfill actions.

## Likely Files

- `app/sync/webhook.py`
- `app/sync/pull.py`
- `app/sync/parser.py`
- `app/db/repo.py`
- `app/web/routes.py`
- `.github/workflows/wily-board-sync.yml`
- `tests/test_parser.py`
- `tests/test_webhook_signature.py`

## Known Risks

- Importing parser code directly from `wily-roadmap` may create packaging friction across repositories.
- YAML parsing must preserve the current Stage/Phase schema but can stay read-only in this phase.
- Webhook replay and unknown repo handling need explicit behavior.

