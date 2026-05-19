# Execution Package: Wily Agent Board V3 Realignment

## Native Goal Command

```text
/goal Complete the Wily Agent Board v3 realignment according to agent-handoffs/wily-agent-board-v3-realignment-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-agent-board-v3-realignment-progress.md.

Keep agent-handoffs/wily-agent-board-v3-realignment-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not broaden scope beyond the execution package. Work only toward the approved architecture: wily-roadmap owns the bundled wily-agent client/snapshot behavior, and wily-board owns only the ingest/cache/rendering server contract.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Done only when docs are aligned, roadmap agent snapshot behavior is implemented, Board ingest API persists the snapshot contract, and final verification passes.
```

## Source Request / Handoff

User approved changing the Board v3 direction so `wily-roadmap` bundles and operates the official `wily-agent`, instead of putting an installable agent package under `wily-board/agent`. The user asked to fix the design docs first and then complete the implementation.

## Inline Requirements

Outcome:
- Update design docs so Board v3 treats `wily-roadmap` as the owner of the bundled `wily-agent`.
- Extend the bundled `wily agent` from heartbeat-only behavior to Board v3 snapshot sync behavior.
- Add Board server ingest support for the snapshot/heartbeat contract consumed by the bundled agent.

In scope:
- `plugins/wily-roadmap/**` agent docs, tests, CLI, config, snapshot, client, daemon behavior.
- `docs/superpowers/specs/2026-05-19-wily-board-v3-design.md` and related handoff text where it contradicts the new ownership model.
- Minimal `wily-board` server additions for `/agent/register`, `/agent/snapshot`, and `/agent/heartbeat`.

Non-goals:
- Do not add hooks, MCP servers, app integrations, or remote deployment.
- Do not make Board write `.wily` state.
- Do not replace existing `/api/live/events` compatibility in this task.
- Do not refactor unrelated Board frontend or GitHub sync behavior.

Assumptions:
- Existing dirty changes in `/Users/wilycastle/Code/projects/wily-plugin/wily-board` are user-owned and must be preserved.
- The current Board repo may not yet match the full v3 design, so the ingest implementation should be additive and compatible with the existing tables/rendering.
- macOS launchd remains the plugin-friendly daemon install path for the bundled agent; systemd packaging belongs only in Board deployment docs if later requested.

## Acceptance Criteria

- Design docs say the official agent source lives in `wily-roadmap`, not `wily-board/agent`.
- `wily agent login`, `register`, `unregister`, `status`, and `run` exist, while existing `install/start/stop/check/dev` compatibility remains.
- The bundled agent can build a Board v3 snapshot payload with tasks, actors, task progress, checkpoint events, task results, project markdown, observed commits, `local_path`, `remote_url`, `project_id`, `snapshot_sha`, and `mode_hint`.
- The daemon publishes snapshots and heartbeats; snapshot failures stay best-effort and do not break normal Wily commands.
- Board accepts `/agent/register`, `/agent/snapshot`, and `/agent/heartbeat` with bearer machine tokens and stores enough state to render current v3 tasks via existing Board models.
- Focused roadmap and board tests pass.

## File / Ownership Boundaries

- Expected touchpoints:
  - `plugins/wily-roadmap/scripts/wily/agent/**`
  - `plugins/wily-roadmap/scripts/wily/cli/agent.py`
  - `plugins/wily-roadmap/skills/wily-agent/SKILL.md`
  - `plugins/wily-roadmap/commands/agent.md`
  - `plugins/wily-roadmap/README.md`
  - `plugins/wily-roadmap/tests/v3/**`
  - `docs/superpowers/specs/2026-05-19-wily-board-v3-design.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/agent.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_agent_*.py`
- Must not edit:
  - Remote deploy files unless required for local tests.
  - Board frontend unless ingestion tests require a typed API update.
- User-owned or pre-existing changes to preserve:
  - Existing dirty Board files and untracked roadmap worktrees.

## Execution Plan

1. Add failing roadmap tests for snapshot payload construction and agent CLI aliases.
2. Implement roadmap snapshot builder, token config, login/unregister/run CLI aliases, and snapshot publishing.
3. Add failing Board tests for register, snapshot ingest, and heartbeat.
4. Implement Board agent API and additive DB tables/helpers.
5. Update design docs and plugin docs to the approved ownership model.
6. Run focused verification, then broader relevant suites.

## Autonomous Action Policy

- Goal-scoped local edits and tests may proceed.
- Do not push, deploy, SSH, or expose secrets.
- Stop only for hard destructive shell commands, credential exfiltration risk, impossible user-owned file conflicts, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/wily-agent-board-v3-realignment-status.md`

## Superpowers Skill Routing

- Available: yes.
- `superpowers:brainstorming`: direction already approved in conversation; record the design as docs and proceed.
- `superpowers:test-driven-development`: required for behavior-changing roadmap and board work.
- `superpowers:systematic-debugging`: use for test/build failures.
- `superpowers:verification-before-completion`: required before final done.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-agent-board-v3-realignment-progress.md`

Live status board:
- `agent-handoffs/wily-agent-board-v3-realignment-status.md`

Verification evidence:
- `agent-handoffs/wily-agent-board-v3-realignment-verification.md`

Checkpoint loop:
1. Mark next checkpoint RUNNING in status.
2. Write the failing test first where behavior changes.
3. Implement the smallest passing change.
4. Run focused verification.
5. Append progress and evidence.
6. Continue until DONE, PARTIAL, or BLOCKED.

