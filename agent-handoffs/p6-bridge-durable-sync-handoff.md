# P6 Handoff — wily-board durable sync auth + Post-P5 secret rotation

Date created: 2026-05-17. Carried over from a Claude Code session that
hit usage limits. The receiving agent should be able to act on this
file with no other context.

## TL;DR for the receiving agent

- wily-roadmap CLI side is **done** (P1-P5, commits already on
  `R-W-LAB/wily-roadmap` `main` at `b95d2f6`). Realtime bridge works.
- wily-board service durable sync is **broken**: GitHub Actions
  webhook `POST /webhooks/github` returns 500 because GitHub App auth
  on the board service is 401. This is the remaining work in P6.
- Production secrets and the SSH password were exposed in the previous
  chat log. Rotate after P6 (procedure at the bottom).

## Background — why this work exists

The Wily-lab user (kokyuhyun@goedu.kr, GitHub `airmang`) reported that
`wily-watch` (local) and `wily-board` (https://rnwlab.duckdns.org) do
not show the same state. Root-cause analysis traced this to two
independent failures:

1. Realtime bridge was silently failing in the CLI (no
   `~/.wily/board.json`, no Codex hook, and every emit call site
   swallowed errors).
2. Durable sync (GitHub push → Actions webhook → board fetches
   `.wily/`) is broken because the wily-board GitHub App credentials
   return 401 from `api.github.com`.

(1) was fully resolved in P1–P5. (2) is what P6 must fix.

## State on hand-off

### Repository: `R-W-LAB/wily-roadmap`

`main` HEAD = `b95d2f6d20d6818660ca79a07268f5ddeb481a59` (pushed).

Three commits added in this session:

| SHA       | Title                                                                |
|-----------|----------------------------------------------------------------------|
| `327145d` | feat(wily): surface board bridge failures at every emit site         |
| `82b7609` | feat(wily): add 'board check --probe' to verify endpoint reachability|
| `b95d2f6` | feat(wily): cache last bridge emit and surface it in watch + board check |

These add:

- `_surface_emit_failure(event, result)` helper in
  `plugins/wily-roadmap/scripts/wily.py`. Every emit call site
  (`command_start`, `close_live_sessions` for complete/block/release,
  `command_live_worked`, `command_live_heartbeat`) now routes its
  result through this helper. On `missing config` the helper prints
  `Board bridge: not configured for <event> (run 'wily board check')`.
  On HTTP/URL errors it prints
  `Board bridge: <event> failed: <reason> (run 'wily board check')`.
- `probe_board_endpoint(values)` helper + `--probe` flag on
  `wily board check`. Probe is a signed GET to
  `/api/live/claims?phase_id=__probe__`, which is read-only on the
  board and exercises URL, TLS, HMAC signature, and repo registration.
  Output: `ok (HTTP 200)` / `rejected (HTTP 4xx)` /
  `server error (HTTP 5xx)` / `unreachable (...)` /
  `skipped (missing config)`.
- `.wily/local/board-last-emit.json` cache (gitignored). Helpers
  `_record_board_emit_result(root, event, ok, reason)` and
  `read_board_last_emit(root)`. `emit_board_live_event` writes the
  cache on every network attempt (not on the `missing config` branch).
- `wily_watch_ui.py`:
  - `_active_live_bridge_warning` (existing, label normalised to
    `Board bridge not connected - run 'wily board check'`).
  - New `_board_bridge_last_emit_line` reads the cache and renders one
    line in `render_watch` (most recent of last_success vs
    last_failure wins; failures in yellow with the reason).
- `wily board check` prints `last bridge success: …` and/or
  `last bridge failure: …` when the cache has entries.

Tests: 231 pass (`python3 -m unittest discover -s plugins/wily-roadmap/tests`).

### Local developer machine state (`kokyuhyun`)

- `~/.wily/board.json` exists with real production URL/secret/repo/actor.
- `~/.codex/hooks.json` exists; PostToolUse hook points to
  `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
  (main repo path, stable).
- `git remote origin` for `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
  has been corrected from `airmang/wily-roadmap` to
  `R-W-LAB/wily-roadmap` so future pushes do not rely on the GitHub
  redirect.

### Main worktree dirty state — preserve, do not touch

The user has unstaged in-progress work for stage `s25` that must
remain untouched:

- `M .wily/roadmap.yaml` (roadmap_version 27, s25 entry added)
- `M .wily/status.md`
- `?? .wily/revisions/2026-05-17-132403-replan-26.md`
- `?? .wily/stages/s25-wily-board-ui-polish-usability/`

### Worktree to clean up

Path: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/amazing-goodall-94b7f6`
Branch: `claude/amazing-goodall-94b7f6` (same commit as `main`).

Safe to remove with `git worktree remove .claude/worktrees/amazing-goodall-94b7f6`
once P6 work has its own workspace. Do this only after confirming
nothing extra is in the worktree (git status clean expected).

## P6 — Restore durable sync

Repository: `R-W-LAB/wily-board` at `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.

### Symptoms (confirmed in production journal)

Triggering Actions workflow `Notify Wily Board` on `R-W-LAB/wily-roadmap`
fires `POST https://rnwlab.duckdns.org/webhooks/github` with a valid
signature. The service then 500s. From `journalctl -u wily-board`:

```
POST /webhooks/github HTTP/1.1" 500 Internal Server Error
File "/opt/wily-board/app/sync/webhook.py", line 65, in sync_repo
    files = github_client.fetch_wily_files(repo_full_name, ref)
File "/opt/wily-board/app/sync/github_client.py", line 54, in _get_json
    response.raise_for_status()
httpx.HTTPStatusError: Client error '401 Unauthorized' for url
'https://api.github.com/repos/R-W-LAB/wily-roadmap/git/trees/b95d2f6...?recursive=1'
```

Realtime bridge endpoints on the same service work (`/api/live/events`,
`/api/live/claims`, `/api/desk`, `/api/sse/live` all return 200). Only
the GitHub App fetch path is broken.

### P6.1 — Defensive error handling (code-side)

Goal: a future credential outage should produce a clear log line and a
non-500 response, not an unhandled exception.

In `app/sync/webhook.py:sync_repo`, wrap the `fetch_wily_files` call so
`httpx.HTTPStatusError` (and `httpx.RequestError` / `OSError`) are
caught. Return a JSONResponse with status 502 and body
`{"error": "github fetch failed", "status": <exc.response.status_code>}`.
Log at ERROR level with the URL and status.

TDD: add a test in `tests/test_web_routes.py` (or
`tests/test_operations_doc.py`, whichever currently covers the webhook
route) that mocks the injected `GitHubClient` to raise
`httpx.HTTPStatusError`. Assert the route returns 502 and the response
body contains the upstream status.

Verification:

```
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_web_routes.py tests/test_operations_doc.py -q
```

Then run the full suite:

```
uv run pytest -q
```

Existing baseline before this work: 82 passed.

### P6.2 — Restore GitHub App credentials (ops-side)

Server: `ssh airman@20.17.177.129 -p 5679`. Sudo password equals SSH
password (already used during the previous session). Hostname is
`n8n-machine`.

Relevant env at `/etc/wily-board/wily-board.env` (mode 0640
root:wily-board, needs sudo to read):

```
GITHUB_APP_ID=3722777
GITHUB_APP_PRIVATE_KEY=/etc/wily-board/app.pem
GITHUB_APP_INSTALLATION_ID=132602517
```

Diagnostic checklist:

1. `sudo ls -la /etc/wily-board/app.pem` — does the file exist and is
   it readable by the `wily-board` service user?
2. `sudo head -c 30 /etc/wily-board/app.pem` — first bytes should be
   `-----BEGIN RSA PRIVATE KEY-----` or `-----BEGIN PRIVATE KEY-----`.
3. In the GitHub UI for `R-W-LAB`: Organization settings →
   GitHub Apps → confirm the App with ID `3722777` is still installed,
   confirm installation ID `132602517` matches, and confirm the
   installation has `Contents: Read` for `wily-roadmap` and any other
   repos in `SYNC_REPOS`.
4. If the App was removed, reinstall on the org and update
   `GITHUB_APP_INSTALLATION_ID` to the new ID.
5. If the private key was rotated, replace `/etc/wily-board/app.pem`
   with the new PEM, preserving mode `0640 root:wily-board`.
6. `sudo systemctl restart wily-board`.

Verification after the fix:

```
gh workflow run wily-board-sync.yml --ref main -R R-W-LAB/wily-roadmap
gh run list --workflow=wily-board-sync.yml -R R-W-LAB/wily-roadmap --limit 1
gh run watch <run-id> -R R-W-LAB/wily-roadmap --exit-status
```

Should exit 0. `journalctl -u wily-board --since '2 min ago'` should
show `POST /webhooks/github` returning 200.

Then from `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

```
python3 plugins/wily-roadmap/scripts/wily.py board check --probe
```

Should still print `endpoint: ok (HTTP 200)`. The board UI should now
reflect the latest `.wily/` content from `R-W-LAB/wily-roadmap` `main`.

## Post-P5 — Secret rotation (do AFTER P6)

The previous session exposed the following in chat. Treat all as
compromised:

- SSH password `dpdj5705@dpdj5705@` for `airman@20.17.177.129:5679`.
- `WILY_BOARD_SECRET=38b2324bee8decc914d702d4cef238c0d083063013c86cdf768a2a3d40e0eeb9`
- `SESSION_SECRET=1d3f4087e240f908d895fff14bfdf3b23e7762bad519016c979f07927747338fa41f37d94eb7f0c3361b023b4dca9f2fbf2495032a4dba26471160951b3405de`
- `GITHUB_OAUTH_CLIENT_SECRET=e635107d74f956fb1c0978cf410e68e68a116d5e`
  (OAuth App `GITHUB_OAUTH_CLIENT_ID=Ov23liePBsZB86sbuF5c`).

Rotation order:

1. **SSH password** — `passwd` on the server, or move to ssh-key-only
   auth and remove password auth from `sshd_config`.
2. **`WILY_BOARD_SECRET`** — new value: `openssl rand -hex 32`.
   Update in three places **atomically**:
   - `/etc/wily-board/wily-board.env` on the server.
   - `R-W-LAB/wily-roadmap` repo → Settings → Secrets → Actions →
     `WILY_BOARD_SECRET`.
   - `~/.wily/board.json` on every developer machine using the bridge.
   Then `sudo systemctl restart wily-board`. Confirm with
   `wily board check --probe` (should still be `ok (HTTP 200)`).
3. **`SESSION_SECRET`** — new value: `openssl rand -hex 64`. Update in
   `/etc/wily-board/wily-board.env`, restart `wily-board`. All current
   board UI sessions will be invalidated; users must sign in again.
4. **`GITHUB_OAUTH_CLIENT_SECRET`** — regenerate in GitHub UI for the
   OAuth App owning `GITHUB_OAUTH_CLIENT_ID=Ov23liePBsZB86sbuF5c`,
   update `wily-board.env`, restart `wily-board`.

After all four rotations, retest:

- `wily board check --probe` from a dev machine → `endpoint: ok`.
- Trigger `Notify Wily Board` workflow → run succeeds, board journal
  shows 200 on `/webhooks/github`.
- Sign in to the board UI fresh → OAuth round trip works.

## Useful absolute paths and commands

Repos:

- wily-roadmap (this CLI plugin): `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
- wily-board (FastAPI service): `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
- temporary worktree to clean up: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/amazing-goodall-94b7f6`

Developer config (already filled, gitignored):

- `~/.wily/board.json` (URL / secret / repo=R-W-LAB/wily-roadmap / actor=airmang / agent=codex)
- `~/.codex/hooks.json` (PostToolUse → wily.py live-worked --from-hook)
- per-repo cache: `.wily/local/board-last-emit.json`

Production:

- Server: `airman@20.17.177.129:5679` (`n8n-machine`)
- Service: `wily-board.service` (systemd, EnvironmentFile=/etc/wily-board/wily-board.env)
- Logs: `sudo journalctl -u wily-board --since '5 min ago' --no-pager`
- URL: `https://rnwlab.duckdns.org`

Probe / verification:

```
python3 plugins/wily-roadmap/scripts/wily.py board check --probe
gh workflow run wily-board-sync.yml --ref main -R R-W-LAB/wily-roadmap
gh run watch <id> -R R-W-LAB/wily-roadmap --exit-status
```

## Done condition for this handoff

- P6.1 merged on `R-W-LAB/wily-board` with passing tests.
- P6.2 confirmed: `Notify Wily Board` workflow run succeeds after a
  triggering push or manual dispatch, journal shows 200, board UI
  reflects latest committed `.wily/` from `R-W-LAB/wily-roadmap`.
- Secret rotation completed and verified by `wily board check --probe`.
- Temporary worktree `amazing-goodall-94b7f6` removed.
- `~/.wily/board.json` updated with the rotated secret.
