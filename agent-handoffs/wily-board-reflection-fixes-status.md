# Wily Board Reflection Fixes Status

State: DONE

Objective: Fix the discovered Wily Board reflection issues so Wily v3 task state is honestly reflected through `wily-agent`, stale Codex hooks stop failing, and docs/tests match the supported contract.

Progress: 6/6 checkpoints (100%)

Current checkpoint/action: Final verification completed.

Next checkpoint: None.

## Checkpoints

| # | Checkpoint | Status | Notes |
|---|------------|--------|-------|
| 1 | Baseline And Safety | DONE | Dirty state recorded; launchd/registry already pointed at moved plugin path; hook file contained old path. |
| 2 | Truthful Agent Send Results | DONE | Added regression test and fixed snapshot/heartbeat failure reporting. |
| 3 | Remove Stale Codex Hook Failure | DONE | Backed up `~/.codex/hooks.json` and removed old-path PostToolUse hook. |
| 4 | Align Documentation And CLI Contract | DONE | Documented v3 agent snapshots/heartbeats, stale `live-*` no-op cleanup, and `wily cp` checkpoint bridge. |
| 5 | Repair Board Test Execution Environment | DONE | Recreated relocated `wily-board/.venv`; board route tests now run. |
| 6 | Integration Smoke | DONE | Agent status/run and active runtime old-path scan completed. |

## Verification

| Command | Status | Result |
|---------|--------|--------|
| Roadmap focused agent/surface tests | PASS | 5 unittest targets passed. |
| Roadmap v3 full isolated unittest | PASS | 104 tests passed with isolated Wily agent config paths. |
| Board agent route tests | PASS | `uv run pytest tests/test_agent_routes.py -q`: 3 passed. |
| `wily agent status --json` | PASS | Configured, daemon running, registry uses moved `wily-plugin` paths. |
| `wily agent run --once --offline-ok --json` | PASS | Ran one tick; Board rejected current token with 401, now reported as `sent: false`. |
| Active runtime old-path scan | PASS | No matches in `~/.codex/hooks.json`, launchd plist, or agent registry. |
| Execution package validator | PASS | `validate_execution_package.py` passed. |

## Recent Events

- 2026-05-19: Planning started from review findings.
- 2026-05-19: Execution package created.
- 2026-05-19: Execution package validator passed.
- 2026-05-19: Backed up and cleared stale `~/.codex/hooks.json` PostToolUse hook.
- 2026-05-19: Added failing regression test for failed snapshot/heartbeat `sent` reporting; implemented fix and verified green.
- 2026-05-19: Updated Wily Board v3 docs and plugin/root README contract wording.
- 2026-05-19: Recreated relocated `wily-board/.venv` and passed board agent route tests.
- 2026-05-19: Final verification completed. Current Codex process still emits the cached old hook error after tool calls, but persisted hook config is fixed for new/reloaded sessions.
