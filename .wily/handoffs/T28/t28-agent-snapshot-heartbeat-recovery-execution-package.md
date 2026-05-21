# Execution Package: T28 Agent Snapshot, Heartbeat, And Status Recovery

## Native Goal Command

```text
/goal Complete T28 by implementing the wily-agent Board v3 snapshot, heartbeat, status-board recovery, and local sync-health behavior according to agent-handoffs/t28-agent-snapshot-heartbeat-recovery-execution-package.md.

First read the execution package. Maintain agent-handoffs/t28-agent-snapshot-heartbeat-recovery-progress.md.

Keep agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. run or import the matching Wily checkpoint event with `python3 plugins/wily-roadmap/scripts/wily.py cp T28 ...`,
5. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Do not stop merely because an action is externally visible if it is goal-scoped. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -q && python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q && python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json && python3 plugins/wily-roadmap/scripts/wily.py doctor.
```

## Source Request / Handoff

- Source request: `custom-workflow-skillset T28 Deep interview로 실행 계획 세우고 실행패키지 만들어줘.`
- Requirements handoff: `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-requirements.md`
- Wily task: `.wily/tasks.yaml` `T28`, `in_progress`.
- Contract source: `agent-handoffs/wily-board-agent-visibility-requirements.md`, especially T26 Agent Payload Contract and Status Board Import And Recovery.

## Inline Requirements

Separate requirements handoff exists. Summary:

- Implement only the `wily-roadmap` bundled `wily-agent` side of Board v3 reflection.
- Snapshot is the recovery source for task/checkpoint data.
- Heartbeat is compact live presence.
- `progress.jsonl` remains durable source of truth.
- Status board import is idempotent recovery/hint data.
- Board unavailable or unconfigured states are best-effort and locally visible through sync health.

## Acceptance Criteria

1. `.wily` change detection still triggers debounced snapshot publication and periodic fallback snapshots.
2. Snapshot payload contains:
   - normalized remote, display repo slug, branch, local path, project id, mode hint, workspace metadata when available
   - actor id/display, optional GitHub login/theme hint, machine hostname
   - full task list including dependencies, assignee/actor, status, claim/done/blocker fields, parallel metadata
   - current task and current checkpoint
   - ordered checkpoint timeline with normalized status, current action, last update, verification text, status board import summary, note, and result/handoff summary
   - recovery metadata and sync health fields
3. Heartbeat payload matches the T26 shape: `project_id`, `repo_slug`, `actor`, `machine`, `current_task_id`, `current_cp`, `status`, `captured_at`.
4. Status board recovery discovers task-related Custom Workflow status boards, imports only missing ledger events, counts imported/skipped/warnings, and never downgrades ledger state.
5. Publish failures persist last failure reason locally; publish success persists last success timestamp; reconnect sends the latest snapshot.
6. Existing Wily commands stay non-blocking without Board config or during Board downtime.
7. Focused unit tests, surface docs tests, foreground agent smoke, and `wily doctor` pass.

## Snapshot Payload Required Schema

The implementation must preserve the current additive raw fields (`repo`, `project_id`, `remote_url`, `title`, `mode_hint`, `local_path`, `tasks`, `actors`, `task_progress`, `cp_events`, `task_results`, `observed_commits`, `project_md`, `client_version`, `captured_at`, `snapshot_sha`) and add explicit Board v3 fields:

- `payload_version`: `"board_v3_snapshot_v1"`.
- `remote`: object with `raw_url`, `normalized_url`, `owner`, `name`, and `slug` such as `R-W-LAB/wily-roadmap`.
- `repo_slug`: display slug from normalized remote or registry fallback.
- `branch`: current branch name, or a deterministic detached-head fallback.
- `workspace`: object with manifest path/title/repo metadata when a workspace manifest is present; otherwise empty values.
- `machine`: object with hostname and configured machine id when present.
- `actor`: object with id/display plus optional GitHub login/theme hint when actor metadata supports it.
- `presence`: object with `project_id`, `repo_slug`, `actor`, `machine`, `current_task_id`, `current_cp`, `status`, and `captured_at`.
- `checkpoint_timeline`: task-keyed object containing ordered CP rows with `id`, `name`, `status`, `current_action`, `last_update`, `verification`, `status_board`, `note`, and `result_summary`.
- `recovery`: object with status board source paths, imported count, skipped duplicate count, ambiguous match warnings, and per-task import summaries.
- `sync_health`: object with last successful push, last failed push, last failure reason, pending snapshot marker, and client version.

`current_cp` means the checkpoint display name used in `progress.jsonl`; it may be null when no checkpoint is active.

## File / Ownership Boundaries

Expected touchpoints:

- `plugins/wily-roadmap/scripts/wily/agent/snapshot.py`
- `plugins/wily-roadmap/scripts/wily/agent/client.py`
- `plugins/wily-roadmap/scripts/wily/agent/config.py`
- `plugins/wily-roadmap/scripts/wily/agent/daemon.py`
- `plugins/wily-roadmap/scripts/wily/agent/recovery.py`
- `plugins/wily-roadmap/scripts/wily/agent/sync_health.py`
- `plugins/wily-roadmap/scripts/wily/progress.py`
- `plugins/wily-roadmap/scripts/wily/cli/cp.py`
- `plugins/wily-roadmap/scripts/wily/cli/agent.py`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `plugins/wily-roadmap/skills/wily-agent/SKILL.md`
- `plugins/wily-roadmap/commands/agent.md`

Must not edit:

- `wily-board/` or any future Board repo.
- Remote/deploy/production files.
- Plugin hooks, MCP servers, or app integrations.
- Unrelated docs/specs already dirty in the worktree unless needed only to preserve context.

User-owned or pre-existing changes to preserve:

- Existing modified docs and handoff files shown by `git status --short` before this package.
- Existing modified `README.md`, `plugins/wily-roadmap/commands/agent.md`, `plugins/wily-roadmap/commands/init.md`, `plugins/wily-roadmap/skills/wily-agent/SKILL.md`, and `plugins/wily-roadmap/skills/wily-init/SKILL.md`.
- Existing untracked `docs/design/shots/`.
- T28 claim/progress edits in `.wily/tasks.yaml` and `.wily/tasks/T28/progress.jsonl` are goal-related.

## Execution Plan

CP01 - Baseline and contract tests:

- Add failing tests in `test_v3_core.py` for normalized remote/project id convergence, branch/repo slug fields, T26 heartbeat shape, checkpoint timeline fields, status recovery metadata, and sync-health persistence.
- Add failing tests for daemon debounce/fallback behavior by patching monotonic time, sleep, and publish calls; do not rely only on `agent run --once`.
- Add a fail-update-reconnect-success test proving failed snapshot sends update sync health, later success updates last success, and the newest snapshot is sent after reconnect.
- Extend the existing snapshot test instead of duplicating broad setup when possible.
- Add or adjust surface tests only for public command/skill documentation text.
- Run targeted tests and confirm RED failures are behavior gaps, not test setup errors.

CP02 - Snapshot identity and timeline:

- Implement remote normalization and stable `project_id` from normalized owner/repo identity.
- Add branch detection with a detached-head safe fallback.
- Build a `presence` block with current task/current checkpoint.
- Build normalized checkpoint timeline from `progress.jsonl` events.
- Preserve raw `task_progress` and `cp_events` as additive backward-compatible fields.
- Add task result/handoff summaries without embedding large raw files in primary timeline fields.

CP03 - Status-board recovery:

- Add `wily.agent.recovery` to discover status boards using deterministic rules:
  - `.wily/handoffs/<task-id>/status.md`
  - `agent-handoffs/*<task-id>*-status.md`
  - sibling `agent-handoffs/<slug>-status.md` where `<slug>-execution-package.md` or requirements handoff references the task id
- Import using `parse_status_board()` and `append_event_once()`.
- Count imported, skipped duplicates, source path, and warnings.
- Preserve ledger precedence with a recovery-layer guard:
  - if a CP already has a terminal ledger event (`done` or `cancel`), skip all status-board events for that CP
  - if a CP has only `start`, allow a missing `done` or `cancel` only when the board marks that same CP `DONE` or `BLOCKED`
  - never append status-board events that contradict task status in `tasks.yaml`
  - ambiguous matches import nothing and produce sync-health warnings
- Preserve status-board metadata in snapshot timeline fields: current action, verification state, note, and handoff/result summary.
- Wire recovery before snapshot construction in `publish_repo_heartbeat()` so the latest payload reflects recovered CPs.
- Keep module boundaries strict: `recovery.py` may write missing ledger events; `snapshot.py` must stay read-only and accept recovery/sync-health reports as inputs or read immutable result files only; `daemon.py` orchestrates ordering.

CP04 - Heartbeat and sync health:

- Replace token-mode heartbeat body with the T26 contract while keeping legacy live-event fallback for legacy secret config.
- Require token-mode `/agent/heartbeat` to post the full T26 body; legacy `/api/live/events` remains unchanged only for secret-based config.
- Add `wily.agent.sync_health` with local JSON state under the agent config directory.
- Extend `AgentPaths` with a sync-health path, defaulting to `~/.config/wily/agent/sync-health.json` and overridable with `WILY_AGENT_SYNC_HEALTH`.
- Write sync-health JSON atomically with temp-file plus replace.
- Record last successful snapshot/heartbeat publish, last failed publish, last failure reason, client version, and captured timestamp.
- Record pending snapshot identity after failed sends so reconnect behavior can be verified.
- Include sync health in snapshot payload and daemon result.
- Ensure Board failures stay best-effort and normal commands exit successfully when offline mode allows it.

CP05 - CLI/docs and smoke:

- Update `wily agent` skill/command docs for Board v3 snapshot, heartbeat, recovery, and sync-health behavior.
- Keep no-secret response guidance.
- Run focused core tests, surface tests, foreground smoke, and doctor.
- Update progress, verification, status board, and Wily CP ledger.

## Autonomous Action Policy

- Goal-scoped local edits, dependency installation required for local verification, tests, and Wily checkpoint updates may proceed.
- Do not push, deploy, SSH, mutate production services, expose secrets, or create remote resources.
- Record any externally visible or environment-changing action in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, impossible file-safety conflicts, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, subagent lane, Superpowers auto-resolution, or final state changes
- Required visible fields:
  - State: PLANNING | RUNNING | VERIFYING | DONE | PARTIAL | BLOCKED
  - Objective
  - Progress count and percentage
  - Current checkpoint/action
  - Next checkpoint
  - Checkpoint table
  - Verification table
  - Recent events

## Superpowers Skill Routing

- Available: yes.
- Required before implementation:
  - `Superpowers:test-driven-development`: required for all behavior changes; write failing tests before production code.
  - `Superpowers:systematic-debugging`: required for failing tests, foreground smoke failures, publish/recovery surprises, or inconsistent payloads.
- Required before done:
  - `Superpowers:verification-before-completion`: required before claiming T28 complete or running `wily done T28`.
- Conditional:
  - `Superpowers:writing-plans`: routed into this execution package's checkpoint plan.
  - `Superpowers:using-git-worktrees`: use only if dirty target files make safe edits impossible; default is preserve user changes in place.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: use for bounded read-only evidence/review. Parallel implementation is not recommended because the core files overlap.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch`: use before major finalization, PR, or merge work if that becomes goal-scoped.

## Superpowers Autonomy Override

- Active when native `/goal` is active or the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:

- `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-progress.md`

Live status board:

- `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md`

Verification evidence:

- `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-verification.md`

Baseline:

- Current git status: dirty before package creation; preserve unrelated modifications.
- Initial failed verification: `python3 -m pytest ...` failed because `pytest` was not installed.
- Dependency action: user approved installing pytest; `python3 -m pip install --user --break-system-packages pytest` succeeded.
- Initial passing verification: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_builds_board_v3_snapshot_payload_from_local_wily_state or cp_import_status_converts_custom_workflow_board_idempotently or agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent" -q` -> `3 passed, 91 deselected`.
- Known broken tests unrelated to this task: none identified yet.

User / pre-existing changes:

- Pre-existing modified files include root README, Board handoff/status docs, multiple Board design docs, `plugins/wily-roadmap/commands/agent.md`, `plugins/wily-roadmap/commands/init.md`, `plugins/wily-roadmap/skills/wily-agent/SKILL.md`, and `plugins/wily-roadmap/skills/wily-init/SKILL.md`.
- Pre-existing untracked files include `docs/design/shots/`.
- Must not overwrite user changes.
- If a target file has user changes unrelated to T28, preserve them and continue only when safe; stop if safe editing is impossible.

Checkpoint loop:

1. Choose the next smallest checkpoint from this package.
2. Run `python3 plugins/wily-roadmap/scripts/wily.py cp T28 start <cp-name>` before implementation work for that checkpoint.
3. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
4. Write one focused failing test set.
5. Run targeted verification and confirm RED failure.
6. Implement the smallest passing change.
7. Run targeted verification and any relevant surface/smoke checks.
8. Update the status board: mark verification state and checkpoint state.
9. Append progress log:
   - checkpoint name
   - files changed
   - commands run
   - result
   - evidence file updates, if any
   - status board update
   - next step
   - blockers / risks
10. Run `python3 plugins/wily-roadmap/scripts/wily.py cp T28 done <cp-name>` after checkpoint verification passes.
11. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:

- At the end of each execution package checkpoint.
- Before changing component boundaries between snapshot, recovery, client, daemon, or CLI.
- Before any new local state file schema.
- After any failed verification retry.

Narrow hard-stop conditions:

- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside the execution package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Payment/purchase action is needed.
- Credential or secret exfiltration risk is discovered.
- Explicit user-forbidden action is needed.
- Existing behavior risk is discovered that is not covered by the plan and cannot be mitigated within scope.
- Tests fail in a way that cannot be attributed to the current change.

Finalization:

1. Run full verification commands.
2. Use command evidence in `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-verification.md`.
3. Run completion verifier.
4. Run integration reviewer because snapshot, recovery, daemon, CLI, and docs interact.
5. Update `agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md` to DONE, PARTIAL, or BLOCKED.
6. Run `python3 plugins/wily-roadmap/scripts/wily.py cp T28 import-status agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md`.
7. Use `wily done T28` only after all acceptance criteria and final verification pass.
8. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED

Reason:

- Snapshot identity, status-board recovery, sync health, daemon publishing, and tests share the same small set of files.
- Parallel implementation would likely conflict in `snapshot.py`, `daemon.py`, `progress.py`, and `test_v3_core.py`.
- Use subagents for read-only architecture review, plan critique, completion verification, and integration review. If implementation is parallelized despite this, split only along strict file ownership boundaries and keep root agent responsible for integration.

## Lane Handoffs

### Lane A - Read-Only Architecture Review

Agent: plan_architect or reviewer.
Mode: read_only_evidence.
Timebox: 10-20 minutes.
Allowed files: read any file in `plugins/wily-roadmap/scripts/wily/agent`, `progress.py`, `cli/cp.py`, `cli/agent.py`, tests, and T26 handoff docs.
Must not edit: all files.
Task: verify the chosen module boundaries for snapshot/recovery/sync health and flag data-integrity risks.
Completion evidence: concise findings in progress log.
Dependencies: package draft exists.

### Lane B - Read-Only Executability Critique

Agent: plan_critic.
Mode: read_only_evidence.
Timebox: 10-20 minutes.
Allowed files: this execution package and likely touchpoints.
Must not edit: all files.
Task: find missing acceptance coverage, unsafe assumptions, or vague verification.
Completion evidence: accepted/rejected verdict and required revisions.
Dependencies: package draft exists.

### Lane C - Final Integration Review

Agent: integration_reviewer.
Mode: review_verification.
Timebox: 10-20 minutes.
Allowed files: changed files and verification logs.
Must not edit: all files unless explicitly reassigned.
Task: before final `wily done T28`, verify snapshot/recovery/heartbeat/sync-health changes align and no status-board text can override ledger truth.
Completion evidence: final review notes in verification log.
Dependencies: implementation and focused verification complete.

## Sequential Gates

- Gate 1: RED tests for snapshot/heartbeat/recovery/sync health are observed before implementation.
- Gate 2: Snapshot payload includes normalized identity, presence, timeline, recovery, and sync-health fields.
- Gate 3: Agent recovery imports idempotently and ambiguous status boards become warnings.
- Gate 4: Heartbeat and sync health survive Board unavailable and reconnect cases.
- Gate 5: Docs, foreground smoke, and final verification pass.

## Verification Plan

Baseline:

- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_builds_board_v3_snapshot_payload_from_local_wily_state or cp_import_status_converts_custom_workflow_board_idempotently or agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent" -q`

Checkpoint verification:

- CP01: targeted RED tests in `test_v3_core.py`.
- CP02: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "snapshot or project_id or branch or heartbeat or checkpoint_timeline" -q`
- CP03: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "import_status or status_board or recovery or cp_summary or ledger_precedence or ambiguous" -q`
- CP04: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent or heartbeat or sync_health or debounce or fallback or reconnect" -q`
- CP05: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q`

Final verification:

- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -q`
- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q`
- `python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json`
- `python3 plugins/wily-roadmap/scripts/wily.py doctor`

## Rollback / Stop Conditions

- Do not run destructive git operations.
- Revert only this task's own changes if a checkpoint must be abandoned; never revert user-owned dirty files.
- If sync health schema choice starts requiring migration of committed `.wily` state, stop and redesign.
- If status-board discovery cannot be made deterministic, keep explicit `wily cp import-status` behavior and mark the agent auto-recovery criterion blocked.
- If Board API expectations conflict with T26, T26 wins unless the user changes the contract.

## Reviewer Notes

- Architect: REVISE. Required revisions incorporated: explicit snapshot schema, stricter recovery-layer ledger guard, sharper module boundaries, status-board metadata preservation, explicit sync-health path/atomic writes/pending retry, token-mode heartbeat shape, expanded full-core final verification.
- Parallel planner: timed out and closed. Root retained `SEQUENTIAL_RECOMMENDED` because implementation write paths overlap; use subagents for read-only review/verification.
- Critic: REVISE. Required revisions incorporated: daemon debounce/fallback unit coverage, fail-update-reconnect-success test, ambiguous status-board warning coverage, ledger downgrade regression test, full-core final verification.
