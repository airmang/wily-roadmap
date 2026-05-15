# Notes

This is the first phase that should touch multiple existing repositories, so approval boundaries matter.

2026-05-15 live deploy update:

- Wily Board is deployed on the Azure VM reachable via `ssh -p 5679 airman@20.17.177.129`.
- `https://rnwlab.duckdns.org/healthz` returns `{"ok":true}`.
- `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are configured on the server.
- Final preflight remains blocked on missing GitHub App values: `GITHUB_APP_ID`, `/etc/wily-board/app.pem`, and `GITHUB_APP_INSTALLATION_ID`.
