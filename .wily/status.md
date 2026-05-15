# Wily Status

Roadmap version 16 has Stage s15 in a blocked state.

Current baseline:
- `R-W-LAB/wily-board` exists as a private repository and has the local FastAPI/SQLite/htmx implementation pushed.
- Child Phases 15-1 through 15-6 are implemented. Phase 15-2 is now deployed on the Azure VM via SSH port 5679.
- Live board health is up: `https://rnwlab.duckdns.org/healthz` returns `{"ok":true}` and `/` redirects to `/auth/github/start`.
- `R-W-LAB/wily-board` now includes `docs/OPERATIONS.md` and `deploy/preflight.sh` covering deploy, credentials, service health, logs, and remaining blockers.
- Child Phase 15-7 merged workflow PRs for all four initial repositories and configured `WILY_BOARD_URL` plus `WILY_BOARD_SECRET` secrets.
- Stage s15 remains blocked because live GitHub OAuth App and GitHub App credentials are still missing; server preflight currently stops at `GITHUB_OAUTH_CLIENT_ID`.
- Stage s14 is done; child Phase 14-2 remains superseded by user request.

Next action:
- Provide GitHub OAuth App and GitHub App credentials before live login, manual backfill, and PR-writing verification.
- Workflow PRs are merged on default branches:
  - `R-W-LAB/wily-roadmap#2`
  - `R-W-LAB/Digit#4`
  - `R-W-LAB/mac2win#187`
  - `R-W-LAB/BounceBall#55`
