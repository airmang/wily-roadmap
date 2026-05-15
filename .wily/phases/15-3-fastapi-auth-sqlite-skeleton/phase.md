# Phase 15-3: FastAPI auth and SQLite skeleton

## Purpose

Build the backend foundation: FastAPI routes, SQLite schema, GitHub OAuth, whitelist sessions, health checks, and empty HTML pages.

## Dependencies

- 15-1 Wily Board repository and contract baseline

## Expected Output

- FastAPI app starts locally with `/healthz`.
- SQLite schema includes repos, stages, phases, events, and oauth_sessions.
- GitHub OAuth callback can be tested with mocks.
- Unauthorized users are rejected after OAuth if not in the whitelist.
- Initial HTML routes return 200 with empty states.

## Likely Files

- `app/main.py`
- `app/config.py`
- `app/auth/`
- `app/db/schema.sql`
- `app/db/repo.py`
- `app/web/routes.py`
- `tests/test_auth.py`
- `tests/test_schema.py`

## Known Risks

- OAuth implementation needs careful redirect URI and cookie security handling.
- Storing sessions in SQLite is sufficient for two users, but expiry cleanup must exist.

