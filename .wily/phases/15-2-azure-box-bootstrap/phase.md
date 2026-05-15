# Phase 15-2: Azure box bootstrap artifacts

## Purpose

Prepare deployment artifacts for a lightweight Ubuntu 24.04 Azure VM running Caddy, FastAPI, SQLite, and systemd without Docker.

## Dependencies

- 15-1 Wily Board repository and contract baseline

## Expected Output

- `deploy/install.sh` provisions non-root execution, SSH hardening assumptions, ufw, fail2ban, swap, Python 3.12, uv, Caddy, and app directories.
- `deploy/Caddyfile` exposes HTTPS for the chosen host and supports rate limits where available.
- `deploy/wily-board.service` runs uvicorn with one worker.
- The deployment path avoids Docker and stays within the 1 GiB memory budget.

## Likely Files

- `deploy/install.sh`
- `deploy/Caddyfile`
- `deploy/wily-board.service`

## Known Risks

- Caddy `rate_limit` requires a build/module decision; if unavailable, keep rate limiting in the app or document the operational gap.
- Hostname, SSH, and secret values are user-owned and must not be guessed.

