# Requirements Handoff: T28 Agent Snapshot, Heartbeat, And Status Recovery

## Source Request

User requested:

- `$wily-claim T28`
- `custom-workflow-skillset T28 Deep interview로 실행 계획 세우고 실행패키지 만들어줘.`

Authoritative task source:

- `.wily/tasks.yaml` task `T28`, now `in_progress`.
- `agent-handoffs/wily-board-agent-visibility-requirements.md`, especially the T26 Agent Payload Contract and Status Board Import And Recovery sections.

## Desired Outcome

Implement the `wily-roadmap` bundled `wily-agent` side of the Wily Board v3 reflection contract. The agent must build a durable snapshot from repo-local `.wily` state, publish a compact heartbeat for presence, recover missing checkpoint events from Custom Workflow status boards idempotently, and persist local sync health so Board downtime is visible and reconnect converges to the newest snapshot.

## In Scope

- Build a Board v3 snapshot payload from registered repo `.wily` state.
- Include normalized project identity, repo slug, branch, local path, actors, tasks, dependencies, current task, current checkpoint, checkpoint timelines, task results, status board import summaries, recovery metadata, observed commits, and sync health.
- Replace the legacy heartbeat shape used by Board v3 token mode with the T26 heartbeat contract: `project_id`, `repo_slug`, `actor`, `machine`, `current_task_id`, `current_cp`, `status`, `captured_at`.
- Discover and import Custom Workflow status boards as recovery hints without letting status board text override durable `progress.jsonl`.
- Persist local sync health for last success, last failure, failure reason, and client version.
- Keep legacy `/api/live/events` compatibility path best-effort and non-blocking where existing config uses it.
- Update focused tests and agent docs.

## Non-Goals

- Do not implement the sibling `wily-board` server, API, DB, SSE, or UI.
- Do not recreate or edit the deleted `wily-board` repo.
- Do not make Board or status boards the source of truth for `.wily` state.
- Do not add hooks, MCP servers, app integrations, production deployment, or remote mutations.
- Do not expose secrets or run production Board calls.

## Decision Boundaries

- Goal-scoped local code, tests, docs, and Wily checkpoint updates may proceed autonomously.
- Installing local developer dependencies is allowed when needed for verification; `pytest` was installed into the user Python 3.14 environment after user approval.
- Remote, destructive, deploy, production-affecting, payment, and credential/secret actions remain hard stops.
- If a required implementation edit falls outside the T28 scope, stop and report the path before editing.
- If multiple status boards ambiguously match one task, do not import; record a sync-health warning.

## Acceptance Criteria

1. Registered repo `.wily` changes are detected and debounced by the agent foreground/daemon path.
2. Snapshot payload includes current task, current checkpoint, checkpoint timeline, task list, dependencies, actor data, normalized repo/project identity, and R-W-LAB remote-derived project id.
3. Heartbeat payload is sufficient to show who is working on which task and checkpoint.
4. Status board recovery imports missing checkpoint state idempotently and never downgrades ledger-backed state.
5. Board unavailability records local last failure reason and preserves last success timestamp; reconnect converges by sending the latest snapshot.
6. Focused unit tests pass for snapshot shape, heartbeat shape, recovery import, sync health, and foreground smoke.
7. Agent skill/command docs describe the local-first, best-effort Board v3 behavior.

## Constraints

- Preserve compatibility with existing Wily v3 tests and command surfaces.
- Use repo-local `.wily/tasks.yaml` and `.wily/tasks/<id>/progress.jsonl` as the source of truth.
- Keep status board import as a recovery mechanism only.
- Keep normal Wily CLI commands non-blocking when Board is missing or unreachable.
- Use TDD for behavior changes.
- Respect the existing dirty worktree and do not overwrite unrelated modified files.

## Repo Facts

- Agent modules live under `plugins/wily-roadmap/scripts/wily/agent/`.
- `build_snapshot_payload()` already emits raw tasks, actors, task progress, CP events, task results, commits, project markdown, and `snapshot_sha`.
- `heartbeat_payload()` still emits legacy live-event fields and does not match the T26 heartbeat contract.
- `publish_heartbeat()` currently posts only `project_id`, `current_task_id`, and `actor`.
- `run_loop()` already reloads registry and watches `.wily` mtimes, with snapshot debounce and fallback intervals.
- `parse_status_board()` and `append_event_once()` already support idempotent checkpoint event import.
- `wily cp import-status` is explicit only; the agent does not yet discover/import status boards before snapshot.
- `project_id()` hashes the raw remote URL, so SSH/HTTPS aliases may diverge.
- No local sync health state file/schema exists yet.
- Baseline focused pytest after installing pytest: `3 passed, 91 deselected`.

## Assumptions

- Sync health should be stored as local JSON under the agent config directory, next to config/registry, not inside committed `.wily` ledger files.
- Sync health should default to `~/.config/wily/agent/sync-health.json`, support `WILY_AGENT_SYNC_HEALTH`, and use atomic writes.
- Normalized repo identity should derive `R-W-LAB/wily-roadmap` from common Git remote forms such as `git@github.com:R-W-LAB/wily-roadmap.git` and `https://github.com/R-W-LAB/wily-roadmap.git`.
- Status board discovery should prefer `.wily/handoffs/<task-id>/status.md`, then deterministic `agent-handoffs/*-status.md` matches tied to the task id or sibling execution package metadata.
- Ambiguous status board discovery is a warning, not a blocker.
- Machine identity can use hostname until Board provides richer machine metadata.
- Actor GitHub login and theme hint are optional fields when not configured.

## Decision Log

- Deep Interview did not ask a user question because T26 explicitly says there are no implementation-blocking open questions and T28 acceptance is concrete.
- Selected local JSON sync health state under the agent config directory as the default storage design.
- Selected deterministic status-board discovery with no import on ambiguous matches.
- Selected `SEQUENTIAL_RECOMMENDED` implementation because snapshot, recovery, daemon, and tests touch shared files; subagents should be used for read-only review and verification, not overlapping code edits.
- `Superpowers:writing-plans` is routed into the Custom Workflow execution package rather than a separate user-facing plan file because the requested artifact is an execution package.
- `Superpowers:test-driven-development`, `systematic-debugging`, and `verification-before-completion` are required during implementation.

## Superpowers Routing

- Used `Superpowers:using-superpowers` as process discovery.
- Used `Custom Workflow Skillset:deep-interview` for requirements clarification.
- Used `Custom Workflow Skillset:plan-goal-runner` for execution package structure.
- Routed `Superpowers:writing-plans` into the execution package task breakdown.
- Required for implementation: `Superpowers:test-driven-development`.
- Required for failures: `Superpowers:systematic-debugging`.
- Required before done: `Superpowers:verification-before-completion`.

## Open Questions

No implementation-blocking open questions.

Accepted implementation assumptions:

- Local sync health path/schema can be defined by T28.
- Exact stale thresholds can remain conservative and tune later.
- Theme hints and GitHub login may be absent until actor metadata grows.

## Likely Touchpoints

- `plugins/wily-roadmap/scripts/wily/agent/snapshot.py`
- `plugins/wily-roadmap/scripts/wily/agent/client.py`
- `plugins/wily-roadmap/scripts/wily/agent/config.py`
- `plugins/wily-roadmap/scripts/wily/agent/daemon.py`
- `plugins/wily-roadmap/scripts/wily/agent/recovery.py` (new)
- `plugins/wily-roadmap/scripts/wily/agent/sync_health.py` (new)
- `plugins/wily-roadmap/scripts/wily/progress.py`
- `plugins/wily-roadmap/scripts/wily/cli/cp.py`
- `plugins/wily-roadmap/scripts/wily/cli/agent.py`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `plugins/wily-roadmap/skills/wily-agent/SKILL.md`
- `plugins/wily-roadmap/commands/agent.md`

## Verification Ideas

- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent" -q`
- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "cp_import_status or status_board or cp_summary" -q`
- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q`
- `python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json`
- `python3 plugins/wily-roadmap/scripts/wily.py doctor`
