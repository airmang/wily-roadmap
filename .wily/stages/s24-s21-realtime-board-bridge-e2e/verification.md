# Verification

Verify Stage s24 with:

- Wily CLI tests for `.wily/board.json` loading, secret redaction, and `wily board check` missing-config/hook diagnostics.
- Wily CLI tests that `wily start` creates the canonical live session and that Codex `live-worked` attaches to it.
- Wily adapter tests that parse `agent-handoffs/*-status.md` checkpoint state and attach it as live overlay without marking durable Phases done.
- Wily status/watch tests that render current checkpoint, current action, blocker, verification, evidence, and live-bridge warnings.
- Board API tests for signed checkpoint events, malformed/unsigned rejection, and storage separate from durable roadmap tables.
- Board JSON/SSE tests proving checkpoint overlay appears in repo detail, desk data, and live event streams.
- Board UI or browser checks proving Hub and repo detail match Wily status/watch for the same active checkpoint.
- A local E2E smoke with temporary local Board secret and no production dependency.

Production smoke is approval-gated:

1. Confirm production Board health.
2. Provide production live config without committing secrets.
3. Send one approved test checkpoint/worked event.
4. Confirm production Board Hub and repo detail update.
5. Confirm durable `.wily` state does not change until push/sync.

## Local Verification Result

Completed on 2026-05-17T01:52:09Z:

- Wily CLI/watch tests: 121 passed, 1 skipped.
- Board API/web tests: 80 passed, 31 warnings.
- Board frontend lint/build: PASS.
- Local E2E smoke: PASS, with checkpoint `CP02` visible in Board desk and repo detail.
- Wily status/next: `24/24 - 100%`, `Next phase: none`.

No production smoke was run without explicit approval.

## Server Reflection

Pushed to `main` for GitHub Actions Wily Board notification after local verification passed. The workflow remains the approval boundary for server-side reflection; no production secret, manual deploy, service restart, or direct server mutation was performed locally.
