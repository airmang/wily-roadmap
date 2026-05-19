# Requirements Handoff: S21 Realtime Board Bridge

## Source Request

User asked to re-plan how to make S21 work show on Wily Board in realtime after discovering that prior "success" covered code/test pieces but not an actual end-to-end bridge from active Codex/CustomWorkflow work to Board UI.

The user selected:

- Hybrid staged rollout: local end-to-end first, production smoke after explicit approval.
- Hybrid event source: canonical `wily start` live session plus CustomWorkflow status file updates and Codex hook `live-worked` signals attached to that session.
- Hook installation included in scope.
- Repo-local untracked `.wily/board.json` configuration.
- Tiered warnings: short warning in active Wily surfaces, detailed diagnostics in `wily board check`.
- Success requires Board Hub, repo detail, and `wily watch/status` to show the same checkpoint/live state.
- Production work is approval-gated only.

## Desired Outcome

When a Codex or CustomWorkflow run is actively working on a Wily Stage or Phase, Wily Roadmap and Wily Board show that work in realtime before `.wily` changes are pushed.

The system must prove the full route:

1. A Wily live session exists for the active Stage/Phase.
2. CustomWorkflow checkpoint status and Codex tool activity attach to that session.
3. Wily emits signed live checkpoint/work events.
4. Board stores those events without mutating durable roadmap state.
5. Board SSE/API and UI surfaces show the current checkpoint, action, blocker, verification, evidence, and freshness.
6. `wily status` and `wily watch` show equivalent live state and warn when the bridge is expected but disconnected.

Local end-to-end must pass before any production smoke. Production smoke may be run only after explicit approval for each remote/secret/deploy/restart/push action.

## In Scope

- Add a repo-local, untracked Board live config path, expected as `.wily/board.json`, with fields equivalent to `WILY_BOARD_URL`, `WILY_BOARD_SECRET`, `WILY_BOARD_REPO`, `WILY_BOARD_ACTOR`, and optional agent/heartbeat settings.
- Add or refine `wily board configure/check` diagnostics so a missing or broken live bridge is obvious before a run is marked successful.
- Treat `wily start` as the canonical live session creation point for active Stage/Phase work.
- Attach CustomWorkflow status boards, especially `agent-handoffs/*-status.md`, to the active Wily session as live runner overlay.
- Attach Codex hook `live-worked` signals to the same active session.
- Include `wily hooks install --target codex` installation and verification in the implementation plan.
- Parse checkpoint fields from CustomWorkflow status boards:
  - checkpoint id
  - checkpoint status
  - current action
  - next checkpoint
  - blocker
  - verification status/evidence
  - recent events
- Emit signed live events for checkpoint started, updated, completed, blocked, and verification updates.
- Store checkpoint overlay state in Board separately from durable roadmap tables.
- Expose checkpoint overlay state through Board read-only JSON and SSE APIs.
- Render checkpoint overlay in Board Hub, repo detail, and `wily watch/status`.
- Keep live overlay visually and semantically distinct from durable Git-synced `.wily` state.
- Add local end-to-end verification covering Wily CLI, Board API/SSE, and Board UI.
- Add production smoke checklist and approval gates for live Board verification.

## Non-Goals

- Do not make Board the source of truth for roadmap progress.
- Do not auto-complete durable Wily Phases from checkpoint completion alone.
- Do not directly write remote repositories from Board.
- Do not push, deploy, restart production services, or write production secrets without explicit user approval.
- Do not add MCP servers or app integrations.
- Do not treat "unit tests passed" as enough for realtime success.
- Do not silently ignore missing live config or missing hook/bridge setup during active work.

## Decision Boundaries

- Agent may implement local code, tests, local fixture config, and local smoke checks.
- Agent may install or update Codex hook configuration because the user explicitly selected hook installation in scope.
- Agent must keep secrets out of git. `.wily/board.json` must be untracked/ignored or otherwise protected from accidental commit.
- Agent must ask before using real production secrets.
- Agent must ask before pushing to GitHub.
- Agent must ask before triggering production deploy or service restart.
- Agent must ask before running a production smoke that sends real live events to `https://rnwlab.duckdns.org`.
- Agent should prefer local end-to-end proof using a local Board server and fixture/temporary secret before production smoke.

## Acceptance Criteria

- `wily board check` reports all required live bridge inputs and fails clearly when URL, secret, repo, actor, hook, or reachable Board endpoint is missing.
- With no live bridge configured, an active Stage/Phase causes `wily status` or `wily watch` to show a short "Board live not connected" style warning and points to `wily board check`.
- With local Board configured, `wily start 21-2` creates a live session registry and opens the heartbeat/work signal path.
- Updating a CustomWorkflow status board such as `agent-handoffs/s21-board-ui-redesign-status.md` updates the attached live checkpoint overlay without changing durable Phase status.
- A Codex hook/tool activity event sends or records a `live-worked` signal attached to the current Wily session.
- Local Board accepts signed checkpoint/work events and rejects malformed or unsigned events.
- Local Board API and SSE include the current checkpoint overlay for the active Stage/Phase.
- Board Hub and repo detail UI show the same active checkpoint/current action/verification state that `wily watch/status` shows.
- Durable Git sync continues to control Stage/Phase done/pending/progress counts.
- The old failure mode is covered by a test or smoke: if code exists but `.wily/board.json` and hooks are missing, completion cannot be reported as realtime success.
- Production smoke checklist exists and is approval-gated. A final "realtime success" claim requires evidence from either local E2E only or explicitly approved production smoke, named clearly.

## Constraints

- Repository rule: keep plugin behavior local-first and approval-first for remote actions.
- Repository rule: hooks, MCP servers, or app integrations must not be added until explicitly requested. The user has now explicitly requested hooks for this bridge; MCP/app integrations remain out of scope.
- `plugins/wily-roadmap/` remains the plugin implementation location.
- `.agents/plugins/marketplace.json` and `plugins/wily-roadmap/.codex-plugin/plugin.json` must remain present.
- Board secrets must never be printed in logs or committed.
- Live events should be best-effort for normal work, but diagnostics and verification must fail loudly when the bridge is expected to prove realtime behavior.
- Heartbeat/worked event cadence should stay lightweight and should not spam Board or slow Codex work.
- Local and production behavior should use the same payload shape where possible.

## Repo Facts

- Current Wily local state shows `s21` as in progress with `21-2` ready:
  - `.wily/roadmap.yaml`
  - `.wily/stages/s21-wily-board-ui-redesign/stage.yaml`
- Current `s21` roadmap already names checkpoint bridge phases:
  - `21-2 CustomWorkflow checkpoint-to-Phase contract`
  - `21-3 Wily live checkpoint adapter`
  - `21-4 Board checkpoint storage and SSE API`
- Current `agent-handoffs/s21-board-ui-redesign-status.md` has checkpoint progress through CP04 while durable Wily Phase state only shows `21-1` done and `21-2` pending.
- Current Wily CLI code already has pieces for:
  - Board live config environment keys
  - `live-heartbeat`
  - `live-worked`
  - `hooks install --target codex|claude`
  - `codex-bridge`
  - local `.wily/local/live/active/*.json` registries
- Current repo has no `.wily/board.json` and no `~/.wily/board.json`.
- Running a live heartbeat currently fails because required Board live config is missing.
- `wily status` reads local Wily files and shows `s21` in progress, but production Board reads synced/cache state and live events, not this dirty local worktree directly.
- Wily Board already has `live_items` and `live_drafts` storage concepts and `/api/live/events`.
- Board currently validates `stage_decomposition` drafts specially; checkpoint overlay payload validation/storage still needs explicit design and implementation.

## Assumptions

- CustomWorkflow status boards will continue to use markdown files under `agent-handoffs/` with stable headings/tables similar to `agent-handoffs/s21-board-ui-redesign-status.md`.
- A single active Wily session per actor/agent/item is sufficient for this bridge.
- Local Board can be run in development for E2E verification before production.
- Production Board secret can be supplied by the user through an untracked config or environment when production smoke is approved.
- Hook installation can be made reversible and inspectable.
- The initial bridge can poll or explicitly read status files; filesystem watching can be added only if needed for acceptable latency.

## Decision Log

- Q1: selected C, hybrid staged local E2E then production smoke.
- Q2: selected C, hybrid event source combining Wily session, CustomWorkflow status files, and Codex hooks.
- Q3: selected A, hook installation and verification are in scope.
- Q4: selected A, repo-local untracked `.wily/board.json` config.
- Q5: selected C, tiered warnings in active Wily surfaces plus detailed `wily board check`.
- Q6: selected A, Board Hub, repo detail, and `wily watch/status` must agree.
- Q7: selected A, production work is approval-gated only.

## Superpowers Routing

- Used `custom-workflow-skillset:deep-interview` because the request was high-risk and likely to cause rework without requirements clarification.
- Used `superpowers:brainstorming` as a companion method because the work changes product behavior and realtime UX semantics.
- Did not spawn a repo explorer because current Codex tool policy only allows subagents when the user explicitly requests delegation or parallel agent work. Repo facts were gathered locally instead.
- No implementation skill was used; this handoff is requirements-only.

## Open Questions

- Exact checkpoint live payload schema should be finalized in implementation planning, using local Board and Wily tests as the contract.
- Whether status file updates are detected by polling, explicit `wily checkpoint sync`, or a watcher should be decided in planning. Default assumption: start with explicit sync/polling for simpler verification, add watch mode only if latency is poor.
- Exact production smoke target and secret delivery method require user approval before execution.

## Likely Touchpoints

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/stages/s21-wily-board-ui-redesign/*`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/*-status.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/*`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/*`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/*`

## Verification Ideas

- Wily CLI unit tests:
  - board config loads `.wily/board.json` and redacts secrets in diagnostics
  - `wily board check` fails on missing config, bad URL, missing hook, and signature failure
  - `wily start 21-2` creates active live session and optional heartbeat
  - CustomWorkflow status board parser extracts CP04/RUNNING/current action/evidence
  - checkpoint overlay attaches to `21-2` without marking durable Phase done
  - hook-generated `live-worked` attaches to the active session
- Wily Watch/status tests:
  - shows current checkpoint/action/evidence under active Phase
  - warns when active work expects Board live bridge but config/hook is absent
- Board tests:
  - accepts signed checkpoint live event
  - rejects malformed/unsigned checkpoint event
  - stores checkpoint overlay separate from durable stages/phases
  - API repo detail and desk responses include checkpoint overlay
  - SSE emits checkpoint update events
  - durable sync does not erase live overlay incorrectly, and completed/blocked durable states reconcile safely
- Local E2E smoke:
  - run local Board with temporary secret
  - configure `.wily/board.json`
  - install Codex hook in an inspectable temporary or real approved path
  - start Wily Phase `21-2`
  - update a status board checkpoint
  - trigger a worked event
  - verify `wily status/watch`, Board API/SSE, Board Hub, and repo detail agree
- Production smoke, approval-gated:
  - verify production Board health
  - write/provide production live config without committing secrets
  - send one test checkpoint/worked event for `R-W-LAB/wily-roadmap`
  - confirm Board Hub/repo detail updates
  - confirm no durable `.wily` state changed until push/sync
