# Verification

Use child Phase verification guidance.

Stage-level acceptance:

- `wily-board` exists as a separate deployable web app or implementation branch.
- The app can ingest `.wily/` state from at least `wily-roadmap`.
- The app can render board/list views on mobile.
- The first write action creates a GitHub PR rather than directly pushing.
- Deployment artifacts fit the Azure 1 GiB RAM constraint.

Current evidence:

- `R-W-LAB/wily-board` commit `458036d` fixes Python package discovery and includes runtime SQL/template/static assets in the deployable wheel.
- `uv run pytest -q` in `wily-board` passes: 20 tests.
- Azure VM deployment on `airman@20.17.177.129:5679` completed with systemd `wily-board` active and Caddy active.
- `curl -fsS https://rnwlab.duckdns.org/healthz` returns `{"ok":true}`.
- `deploy/preflight.sh` still fails on missing `GITHUB_OAUTH_CLIENT_ID`; GitHub OAuth App and GitHub App credentials are required before final live onboarding verification.
