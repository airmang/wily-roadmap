# Wily Board Reflection Fixes Progress

## 2026-05-19 - Planning

State: PLANNING

Created execution package and live status board for fixing Wily Board reflection issues.

Validation:

- `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-board-reflection-fixes-execution-package.md`
- Result: PASS.

Known starting facts:

- Current Codex `PostToolUse` hook calls an old moved-away Wily script path and causes `can't open file` errors after commands.
- Wily agent launchd plist and registry point at moved `/Users/wilycastle/Code/projects/wily-plugin/...` paths.
- `publish_snapshot()` and `publish_heartbeat()` currently force `sent: true` over failed `post_json()` results.
- Wily v3 source treats `live-* --from-hook` as a migration no-op, while some docs still describe it as a live reflection mechanism.
- Board route tests need environment repair or a working `uv run` path after relocation.

## 2026-05-19 - Execution Complete

State: DONE

Checkpoint summary:

- CP1 Baseline: recorded dirty state. Roadmap had many pre-existing modified handoffs/docs and untracked relocation handoffs. Board had pre-existing modified `tests/test_agent_routes.py`. Launchd plist and agent registry already used moved `wily-plugin` paths. `~/.codex/hooks.json` contained the stale old path.
- CP2 Agent send results: added `test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent`, verified it failed red, then changed `publish_snapshot()` and `publish_heartbeat()` to preserve failed `sent: false` results.
- CP3 Hook cleanup: backed up `/Users/wilycastle/.codex/hooks.json` to `/Users/wilycastle/.codex/hooks.json.bak-wily-board-reflection-20260519` and replaced the active hook file with `{ "hooks": {} }`.
- CP4 Docs contract: updated Wily Board operations docs, root Wily roadmap README, and plugin README to say Board v3 reflection uses `wily-agent` snapshots/heartbeats; stale `live-* --from-hook` hooks are no-op cleanup targets; checkpoints flow through `wily cp`.
- CP5 Board test environment: moved broken relocated `.venv` to `.venv.bak-wily-board-reflection-20260519`, ran `uv sync`, and verified the new `.venv/bin/pytest` shebang points at the moved `wily-plugin/wily-board` path.
- CP6 Smoke: `wily agent status --json` showed configured/running daemon and moved registry paths. `wily agent run --once --offline-ok --json` reached Board and got 401 invalid bearer token, correctly reported as `sent: false`.

Verification:

- Roadmap focused tests: PASS, 5 unittest targets.
- Board route tests: PASS, 3 tests.
- Roadmap v3 full isolated unittest: PASS, 104 tests.
- `git diff --check` for touched roadmap and board files: PASS.
- Active runtime old-path scan over `~/.codex/hooks.json`, launchd plist, and agent registry: PASS, no matches.

Residual note:

- The current Codex process continues to print the stale old hook error after tool calls, apparently from a cached hook loaded before `~/.codex/hooks.json` was edited. The persisted hook file is clean, so a new/reloaded Codex session should stop invoking it.
