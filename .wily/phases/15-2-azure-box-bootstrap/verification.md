# Verification

Expected checks:

```bash
sh -n deploy/install.sh
systemd-analyze verify deploy/wily-board.service
caddy validate --config deploy/Caddyfile
```

Run available checks locally and document any host-only checks that cannot run.

