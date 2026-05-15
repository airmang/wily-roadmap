# Execution Prompt

Implement Azure VM bootstrap artifacts for Wily Board.

Scope:

- Add deploy scripts and service files for Ubuntu 24.04, Caddy, Python 3.12, uv, systemd, SQLite storage, ufw, fail2ban, and 1 GiB swap.
- Keep values configurable via environment files.
- Do not use Docker.
- Do not connect to Azure, alter the real server, or register DNS without explicit approval.

