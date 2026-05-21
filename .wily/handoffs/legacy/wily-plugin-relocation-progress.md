# Wily Plugin Relocation Progress

## 2026-05-19T06:00:11Z - CP01 Baseline and Planning

- Checkpoint: Freeze baseline and plan.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-execution-package.md`
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
  - `agent-handoffs/wily-plugin-relocation-verification.md`
- Commands run:
  - `git status --short --branch` in `/Users/wilycastle/Code/projects/wily-roadmap`
  - `git -C /Users/wilycastle/Code/projects/wily-board status --short --branch`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent status`
  - launchd plist and registry read-only inspections
  - subagent read-only inspections for repo paths, daemon/registry, parallelization, and plan critique
- Result:
  - Roadmap repo is on `main` with pre-existing untracked `.claude/`.
  - Board repo is clean on `main`.
  - Wily daemon is running and plist points to old roadmap path.
  - Registry contains old roadmap root plus two old nested roadmap worktree paths.
  - Plan critic found extra required repairs: git worktree metadata and `core.hooksPath`.
- Evidence:
  - `agent-handoffs/wily-plugin-relocation-execution-package.md`
  - `agent-handoffs/wily-plugin-relocation-status.md`
- Next step:
  - Validate execution package, then stop daemon from old path.
- Blockers / risks:
  - Do not move while launchd daemon is running.
  - Do not print Wily agent config token/secret or board private key.

## 2026-05-19T06:01:00Z - CP01 Execution Package Validation Fix

- Checkpoint: Freeze baseline and plan.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-execution-package.md`
- Commands run:
  - `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/wily-plugin-relocation-execution-package.md`
- Result:
  - Validator found the rollback section content but required it under a `## Rollback / Stop Conditions` heading.
  - Heading corrected; re-run pending.
- Next step:
  - Re-run execution package validator.

## 2026-05-19T06:01:30Z - CP01 Complete

- Checkpoint: Freeze baseline and plan.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-execution-package.md`
  - `agent-handoffs/wily-plugin-relocation-status.md`
- Commands run:
  - `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/wily-plugin-relocation-execution-package.md`
- Result:
  - PASS: execution package contract is complete.
- Next step:
  - Stop Wily launchd daemon from the old plugin path.

## 2026-05-19T06:02:20Z - CP02 Complete

- Checkpoint: Stop Wily launchd daemon.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
- Commands run:
  - `python3 plugins/wily-roadmap/scripts/wily.py agent stop`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
  - `launchctl print gui/$(id -u)/com.wily.roadmap.agent`
- Result:
  - `wily-agent launchd bootout ok`.
  - `agent status --json` reported `daemon.running=false`.
  - `launchctl print` returned non-zero, confirming the service is not loaded.
- Next step:
  - Move `wily-roadmap` and `wily-board` under `/Users/wilycastle/Code/projects/wily-plugin`.

## 2026-05-19T06:08:00Z - CP03 and CP04 Complete

- Checkpoints:
  - Move repositories.
  - Repair git metadata.
- Files changed:
  - Filesystem paths moved from `/Users/wilycastle/Code/projects/{wily-roadmap,wily-board}` to `/Users/wilycastle/Code/projects/wily-plugin/{wily-roadmap,wily-board}`.
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.git/config`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.git/worktrees/*/gitdir`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/*/.git`
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
- Commands run:
  - `mkdir -p /Users/wilycastle/Code/projects/wily-plugin`
  - `mv /Users/wilycastle/Code/projects/wily-roadmap /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
  - `mv /Users/wilycastle/Code/projects/wily-board /Users/wilycastle/Code/projects/wily-plugin/wily-board`
  - `git -C /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap worktree repair ...`
  - `git -C /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap config core.hooksPath /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.git/hooks`
  - `kill 73930 77844 77991`
  - `rm -rf /Users/wilycastle/Code/projects/wily-board`
- Result:
  - Both repo roots are under `/Users/wilycastle/Code/projects/wily-plugin`.
  - `git status` works in both moved repo roots.
  - `git worktree list --porcelain` lists the nested worktrees under the new roadmap path.
  - `core.hooksPath` now points to the moved roadmap `.git/hooks`.
  - Three stale old-path dev processes were terminated with SIGTERM because they recreated generated `.next` cache under the old board path.
  - The leftover old board path contained only generated `.next` cache and was removed.
- Next step:
  - Update active old absolute path references in repo files.

## 2026-05-19T06:15:00Z - CP05 Complete

- Checkpoint: Update path references.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_agent_routes.py`
  - top-level `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/**`
  - top-level `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/docs/superpowers/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/docs/**`
- Commands run:
  - `rg -0 -l ... | xargs -0 perl -0pi -e ...`
  - active old-path text audit with `rg -n`, excluding `.git`, dependency folders, `.wily/archive`, `.claude/worktrees`, and this relocation evidence package.
- Result:
  - Active old-path audit returned no matches.
  - Board test fixture now expects `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`.
  - Historical `.wily/archive`, nested worktree historical docs, and relocation evidence were intentionally excluded from the bulk rewrite.
- Next step:
  - Update Wily agent registry with exact unregister/register commands.

## 2026-05-19T06:18:00Z - CP06 Complete

- Checkpoint: Update Wily registry.
- Files changed:
  - `/Users/wilycastle/.config/wily/agent/registry.json`
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
- Commands run:
  - `python3 plugins/wily-roadmap/scripts/wily.py agent unregister --path /Users/wilycastle/Code/projects/wily-roadmap`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent unregister --path /Users/wilycastle/Code/projects/wily-roadmap/.claude/worktrees/v3-design-review`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent unregister --path /Users/wilycastle/Code/projects/wily-roadmap/.claude/worktrees/wily-board-plans-2-3`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent register --path /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap --repo R-W-LAB/wily-roadmap`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent register --path /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/v3-design-review --repo R-W-LAB/wily-roadmap`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent register --path /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/wily-board-plans-2-3 --repo R-W-LAB/wily-roadmap`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
  - `rg -n` old/new path audits on `/Users/wilycastle/.config/wily/agent/registry.json`
- Result:
  - Old roadmap paths were removed.
  - New roadmap root and two nested worktree paths were registered.
  - Board was not registered because it was not in the baseline registry.
  - Registry old-path audit returned no matches.
- Next step:
  - Reinstall launchd plist from the moved plugin and start the daemon.

## 2026-05-19T06:22:00Z - CP07 Complete

- Checkpoint: Reinstall and start launchd.
- Files changed:
  - `/Users/wilycastle/Library/LaunchAgents/com.wily.roadmap.agent.plist`
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
- Commands run:
  - `python3 plugins/wily-roadmap/scripts/wily.py agent install`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent start`
  - `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
  - `plutil -p /Users/wilycastle/Library/LaunchAgents/com.wily.roadmap.agent.plist`
  - `rg -n` old/new path audits on the launchd plist
  - `launchctl print gui/$(id -u)/com.wily.roadmap.agent`
- Result:
  - Plist was regenerated.
  - Daemon started successfully.
  - `agent status --json` reported `daemon.running=true`.
  - Plist points to `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`.
  - Plist old-path audit returned no matches.
- Next step:
  - Run final verification.

## 2026-05-19T06:35:00Z - CP08 Verification Commands

- Checkpoint: Final verification.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
  - `agent-handoffs/wily-plugin-relocation-verification.md`
- Commands run:
  - `git status --short --branch` in moved roadmap and board.
  - `git status --short --branch` in both nested roadmap worktrees.
  - `git worktree list --porcelain`.
  - marketplace metadata read and `test -d plugins/wily-roadmap`.
  - config/git metadata old-path audit across launchd plist, Wily registry, roadmap `.git/config`, roadmap `.git/worktrees`, and nested worktree `.git` files.
  - active text old-path audit excluding `.git`, dependency folders, `.wily/archive`, `.claude/worktrees`, and relocation evidence.
  - `uv run --with pytest python -m pytest tests/test_agent_routes.py -q` in moved board.
  - isolated plugin test: `WILY_AGENT_CONFIG=<tmp>/config.json WILY_AGENT_REGISTRY=<tmp>/registry.json WILY_AGENT_PLIST=<tmp>/com.wily.roadmap.agent.plist WILY_AGENT_LOG_DIR=<tmp>/logs uv run --with pytest pytest tests/v3 -q`.
  - `git diff --check` in moved roadmap and moved board.
  - `python3 plugins/wily-roadmap/scripts/wily.py agent check --offline --json`.
  - `python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json`.
- Result:
  - Git and marketplace checks passed.
  - Launchd/registry/git metadata old-path audits passed.
  - Active text old-path audit passed.
  - Board targeted test passed: 3 passed.
  - Plugin isolated tests passed: 102 passed, 37 subtests passed.
  - `git diff --check` passed in both repos.
  - `wily agent check --offline --json` passed with `ok=true`.
  - `wily agent run --once --offline-ok --json` exited 0 and reached all registered repos, but the configured Board returned HTTP 401 invalid bearer token for snapshot/heartbeat sends. This confirms relocated local paths are readable; token validity is a pre-existing Board auth issue outside the filesystem relocation.
- Next step:
  - Wait for integration reviewer and completion verifier, then finalize.

## 2026-05-19T06:48:00Z - Nested Handoff Cleanup

- Checkpoint: Final verification.
- Files changed:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/v3-design-review/agent-handoffs/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/wily-board-plans-2-3/agent-handoffs/**`
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
  - `agent-handoffs/wily-plugin-relocation-verification.md`
- Commands run:
  - bulk path rewrite over nested worktree `agent-handoffs`, excluding `.git`, dependency/cache folders, and `.wily/archive`.
  - old-path audit over top-level and nested worktree `agent-handoffs`.
  - old-path audit over local script file types.
  - `git diff --check` in both nested worktrees.
- Result:
  - Nested worktree `agent-handoffs` no longer contain old roadmap/board absolute paths outside archives.
  - Local script audit returned no old path matches.
  - `git diff --check` passed in both nested worktrees.
  - All subagents used for this task were closed.
- Next step:
  - Run final verification re-check after this status update.

## 2026-05-19T06:55:00Z - CP08 Complete

- Checkpoint: Final verification.
- Files changed:
  - `agent-handoffs/wily-plugin-relocation-status.md`
  - `agent-handoffs/wily-plugin-relocation-progress.md`
- Commands run:
  - old roots absence check
  - final plist/registry/git metadata old-path audit
  - final top-level and nested worktree handoff old-path audit
  - final local script old-path audit
  - `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
  - `git worktree list --porcelain`
  - `uv run --with pytest python -m pytest tests/test_agent_routes.py -q`
  - isolated plugin test with temp Wily agent paths: `uv run --with pytest pytest tests/v3 -q`
  - `git diff --check` in roadmap, board, and both nested worktrees
  - `python3 plugins/wily-roadmap/scripts/wily.py agent check --offline --json`
- Result:
  - Old roots are absent.
  - Launchd plist, active registry, roadmap git metadata, active handoff docs, and local scripts have no old roadmap/board absolute paths.
  - Wily agent status reports `daemon.running=true`.
  - Roadmap worktree metadata lists only moved paths.
  - Board targeted test passed: 3 passed.
  - Plugin isolated tests passed: 102 passed, 37 subtests passed.
  - Diff whitespace checks passed.
  - `wily agent check --offline --json` passed with `ok=true`.
- Remaining issue:
  - Foreground `agent run --once --offline-ok --json` reached the moved repos but Board sends returned 401 invalid bearer token. This is outside the relocation path work and the daemon is installed/running.
