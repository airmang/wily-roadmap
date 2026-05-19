# Execution Package: Wily Board Plan 2 Agent

## Native Goal Command

```text
/goal Implement Wily Board v3 Plan 2 wily-agent daemon according to agent-handoffs/wily-board-2-agent-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-board-2-agent-progress.md.

Keep agent-handoffs/wily-board-2-agent-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not broaden scope beyond Plan 2. Work only toward the wily-agent package, the local_path server contract amendment, docs, and listed verification.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Done only when all Plan 2 acceptance criteria are satisfied and final verification passes: cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run pytest -v; uv run ruff check .; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .
```

## Source Request / Handoff

User requested Custom Workflow goal execution for:

`/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/wily-board-plans-2-3/docs/superpowers/plans/2026-05-19-wily-board-2-agent.md`

The plan title is "Wily Board v3 - Plan 2: wily-agent Daemon".

## Inline Requirements

Outcome: ship `wily-agent`, a separate Python package under `/Users/wilycastle/Code/projects/wily-plugin/wily-board/agent`, with CLI login/register/unregister/status/run, token and registry persistence, `.wily` snapshot building, HTTP client, daemon push loop, heartbeat, E2E server round trip, systemd template, and docs.

In scope:
- Create the `agent/` package and tests.
- Use the existing server contract in `app/parsers/wily_state.py` and `tests/contracts/agent_v1.json`.
- Amend the server once to accept `local_path` and populate `project_machines`.
- Keep browser UI out of scope.

Non-goals:
- No Plan 3 UI.
- No remote deployment unless local verification proves impossible.
- No hooks, MCP servers, or app integrations.

Assumptions:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board` is the Plan 1 server repo.
- The Plan 2 file in `.claude/worktrees/wily-board-plans-2-3` is authoritative even though it is not present in the main plans directory.
- Existing dirty files in `wily-roadmap` are user-owned and must be preserved.

## Acceptance Criteria

- `wily-agent` is separately installable from `wily-board/agent`.
- `wily-agent login`, `register`, `unregister`, `status`, and `run` exist.
- Watchdog daemon debounces `.wily/` changes, pushes snapshots, includes a 60-second fallback push, and sends 5-second heartbeats.
- Snapshot payloads match the server contract and include `local_path`.
- Server persists `project_machines.local_path` during snapshot ingest.
- In-process E2E proves agent login/register/push writes task, checkpoint, and project machine rows.
- Final verification commands pass or failures are documented with evidence.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/agent/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/parsers/wily_state.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/agent.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/contracts/agent_v1.json`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_parsers_wily_state.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_agent_snapshot.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-board-2-agent-*.md`
- Must not edit:
  - `plugins/wily-roadmap/**`
  - unrelated `wily-roadmap` dirty files
  - remote servers unless local-only verification is blocked
- User-owned or pre-existing changes to preserve:
  - `wily-roadmap/AGENTS.md`, `.claude/`, `CLAUDE.md`, existing handoffs/docs.

## Execution Plan

1. Create agent scaffold and path/token/registry primitives with tests.
2. Implement `.wily` reader, git collector, snapshot builder, and HTTP client with tests.
3. Implement CLI commands and status coverage.
4. Amend server contract for `local_path` and verify server suite.
5. Implement daemon push loop and heartbeat with tests.
6. Add in-process E2E against the server.
7. Add systemd template and README docs.
8. Run final server and agent verification.

## Autonomous Action Policy

- Goal-scoped local edits, dependency installation via `uv`, and test execution may proceed.
- Do not perform remote SSH/deploy/push unless a local verification blocker makes it necessary and it is recorded.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/wily-board-2-agent-status.md`

## Superpowers Skill Routing

- Available: yes.
- `custom-workflow-skillset:plan-goal-runner`: outer runtime.
- `superpowers:executing-plans`: active for written plan execution.
- `superpowers:test-driven-development`: active; use red/green checkpoints for Plan 2 behavior.
- `superpowers:verification-before-completion`: required before final done.
- `superpowers:subagent-driven-development`: plan recommends it, but implementation remains local because the user asked for Custom Workflow goal execution rather than explicit subagent delegation.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-board-2-agent-progress.md`

Live status board:
- `agent-handoffs/wily-board-2-agent-status.md`

Verification evidence:
- `agent-handoffs/wily-board-2-agent-verification.md`

Baseline:
- `wily-roadmap`: dirty before this goal; preserve unrelated changes.
- `wily-board`: branch `feat/v3-rewrite`; initial server suite `uv run pytest -q` passed with 40 tests and 2 warnings before Plan 2 edits.

Checkpoint loop:
1. Mark next checkpoint RUNNING in status.
2. Make a focused change.
3. Run relevant verification.
4. Append progress and evidence.
5. Continue until DONE, PARTIAL, or BLOCKED.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED
Reason: Plan tasks are ordered and many later tasks depend on earlier modules. Use no parallel implementation unless explicitly delegated.

## Verification Plan

- Server baseline and contract: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v`
- Agent package: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run pytest -v`
- Agent lint: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .`
- Server lint: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .`

## Rollback / Stop Conditions

- Repeated failing verification with no new evidence.
- Need to touch files outside the boundaries.
- SSH/deploy becomes necessary without local evidence.
- Secret exposure risk.

## Reviewer Notes

- Architect: Plan fits the existing Plan 1 server contract and keeps agent package separate.
- Critic: E2E ASGI transport compatibility may need adjustment for installed httpx version; verify rather than assuming.
