# Execution Package: Stage 31 Heartbeat Tail SSE Polish

## Native Goal Command

```text
/goal Complete Stage 31 heartbeat tail and SSE polish across wily-roadmap and wily-board according to agent-handoffs/stage-31-heartbeat-tail-sse-polish-execution-package.md.

First read the execution package. Maintain agent-handoffs/stage-31-heartbeat-tail-sse-polish-progress.md.

Keep agent-handoffs/stage-31-heartbeat-tail-sse-polish-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py plugins/wily-roadmap/tests/test_wily_watch_ui.py -q; uv run pytest tests/test_live_events.py tests/test_config.py tests/test_signature.py tests/test_api_routes.py tests/test_db.py tests/test_operations_doc.py -q; uv run pytest tests/test_webhook.py -q; npm run lint; npm run build.
```

## Source Request / Handoff

User request: `$custom-workflow-skillset:plan-goal-runner Stage 31 구현해줘. 구현 계획 파일docs/superpowers/plans/2026-05-18-stage-31-heartbeat-tail-sse-polish.md 여기에 있어 참고해.`

Source plan: `docs/superpowers/plans/2026-05-18-stage-31-heartbeat-tail-sse-polish.md`.

## Inline Requirements

Outcome: finish Stage 31 by stabilizing Wily live-event identity, Board live-event ingestion, HMAC rotation, heartbeat TTL expiry, and frontend SSE reconnect behavior.

In scope:
- Wily CLI live-event client in this repo.
- Wily Board backend event ingestion, config, signature verification, webhook verification, and operations docs.
- Wily Board frontend SSE repo scoping, reconnect backoff, and tab visibility handling.
- Focused tests and final verification commands from the source plan.

Non-goals:
- Do not add hooks, MCP servers, or app integrations.
- Do not commit, push, or land unless the user explicitly asks later.
- Do not broaden Board behavior beyond Stage 31 acceptance criteria.

Assumptions:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board` is the intended sibling repo.
- Process-local dedup is acceptable and does not need multi-worker persistence.
- Frontend manual SSE behavior is verified through lint/build plus backend API route tests unless a browser smoke is practical.

## Acceptance Criteria

- Wily CLI emits stable `event_id` values, preserving supplied event ids and generating unique ids for new live payloads.
- Wily CLI emits `renamed` live events for active local sessions whose item id changes, and updates the active registry.
- Wily CLI heartbeat uses `WILY_BOARD_HEARTBEAT_TTL_SECONDS` as the default TTL and explicit `--ttl` overrides it, including `--ttl 0` disabling expiry.
- Board accepts HMAC signatures signed by any current or previous secret from `WILY_BOARD_SECRETS`, preserving `WILY_BOARD_SECRET` compatibility.
- Board deduplicates duplicate `(session_id, event_id)` live events for five minutes before DB writes.
- Board handles valid `renamed` events and rejects malformed ones.
- Board operations docs describe HMAC rotation and heartbeat TTL.
- Board frontend scopes repo workspaces to `/api/sse/live?repo=owner%2Fname`.
- Board frontend owns reconnect backoff, shows the required toast after repeated failures, and reconnects on tab visibility changes.
- Final verification commands pass or any residual failures are documented with evidence.

## File / Ownership Boundaries

- Expected touchpoints:
  - `plugins/wily-roadmap/scripts/wily.py`
  - `plugins/wily-roadmap/tests/test_wily_cli.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/signature.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/webhook.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_signature.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_webhook.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/api/sse/live/route.ts`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- Must not edit:
  - `.agents/plugins/marketplace.json` except if needed to preserve existing marketplace metadata.
  - `plugins/wily-roadmap/.codex-plugin/plugin.json` except if explicitly required; not expected.
  - Hooks, MCP servers, or app integrations.
- User-owned or pre-existing changes to preserve:
  - `agent-handoffs/p6-bridge-durable-sync-handoff.md` is pre-existing untracked.
  - `docs/superpowers/plans/2026-05-18-stage-31-heartbeat-tail-sse-polish.md` is pre-existing untracked source plan.

## Execution Plan

1. Create and validate handoff artifacts: execution package, status board, progress log, and verification log.
2. Lane A, Wily CLI:
   - Add failing tests for event id generation/preservation/uniqueness, renamed events, and heartbeat TTL env/default/expiry.
   - Implement `new_live_event_id`, include `event_id` in Board live payloads, implement `emit_renamed_live_events`, wire it into the id-change path if present, and add heartbeat TTL env parsing.
   - Run targeted Wily CLI tests after each behavior group.
3. Lane B, Board backend:
   - Add failing tests for secret rotation, previous-secret signature acceptance, live-event dedup, renamed handling, operations docs, and heartbeat TTL config.
   - Implement rotated secrets in Settings, `verify_signature_any`, route verification updates, live-event dedup before DB writes, renamed normalization/validation, and docs.
   - Run targeted backend tests after each behavior group.
4. Lane C, Board frontend:
   - Confirm or add repo filter regression coverage.
   - Update `LiveRefresh` to derive repo filter from pathname, build scoped EventSource URLs, own manual backoff, handle visibility changes, invalidate relevant queries, and clean up timers/EventSource.
   - Run backend SSE tests and frontend lint/build.
5. Integration:
   - Run all final verification commands from the source plan.
   - Update verification log and status board to DONE, PARTIAL, or BLOCKED.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Do not perform branch push, PR open/update, GitHub comments, issue duplicate/close actions, or PR merge in this task because the source plan says to commit Wily roadmap state only after explicit user request.
- Record externally visible actions if any are later requested.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, repeated verification failure, or unsafe file ownership conflicts.

## Live Status Board

- File: `agent-handoffs/stage-31-heartbeat-tail-sse-polish-status.md`
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
  - `Superpowers:test-driven-development` for behavior changes: loaded; red-green checkpoints will be recorded.
  - `Superpowers:systematic-debugging` for failures: load before fixing unexpected or repeated test/build failures.
- Required before done:
  - `Superpowers:verification-before-completion`: loaded; final claims require fresh command evidence.
- Conditional:
  - `Superpowers:writing-plans` for detailed task decomposition: skipped because the user supplied a detailed implementation plan.
  - `Superpowers:using-git-worktrees` if isolation is needed: skipped unless file conflicts appear.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` if lanes are independent: `subagent-driven-development` loaded because the source plan explicitly requires it.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch` for review, PR, merge, or cleanup: defer unless user asks for review or landing.

## Superpowers Autonomy Override

- Active because native `/goal` is active and the user requested implementation.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/stage-31-heartbeat-tail-sse-polish-progress.md`

Live status board:
- `agent-handoffs/stage-31-heartbeat-tail-sse-polish-status.md`

Verification evidence:
- `agent-handoffs/stage-31-heartbeat-tail-sse-polish-verification.md`

Baseline:
- Current git status:
  - wily-roadmap: untracked `agent-handoffs/p6-bridge-durable-sync-handoff.md`, untracked source plan, plus this task's handoff files.
  - wily-board: clean at initial inspection.
- Initial failing/passing verification:
  - Run targeted RED checks before each implementation group.
- Known broken tests unrelated to this task:
  - Unknown at package creation.

User / pre-existing changes:
- Pre-existing modified files: none reported.
- Pre-existing untracked files: `agent-handoffs/p6-bridge-durable-sync-handoff.md`, `docs/superpowers/plans/2026-05-18-stage-31-heartbeat-tail-sse-polish.md`.
- Must not overwrite user changes.
- If a target file has user changes unrelated to this task, preserve them and continue when possible; stop only if safe editing is impossible.

Checkpoint loop:
1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log with checkpoint, files changed, commands run, result, evidence updates, status board update, next step, blockers, and risks.
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing component boundaries.
- Before public API/schema/migration changes.
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
2. Use command output as verification evidence.
3. Run completion_verifier by mapping each acceptance criterion to evidence.
4. Run integration_reviewer for multi-component changes.
5. Update status board to DONE, PARTIAL, or BLOCKED.
6. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: Lane A writes only the Wily plugin repo. Lane B writes Board backend/config/docs/tests. Lane C writes Board frontend and a focused route test. Lane B and C must avoid concurrent edits to the same backend route file; integration remains sequential.

## Lane Handoffs

### Lane A - Wily CLI Live-Event Client

Agent: root or implementation worker.
Mode: implementation_disjoint.
Timebox: 30 minutes.
Allowed files:
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
Must not edit:
- Board repo files.
Task:
- Implement event ids, renamed live events, and heartbeat TTL env/default behavior with tests.
Completion evidence:
- `python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "live_heartbeat or board_live_event or renamed_live" -q`
Dependencies:
- None.

### Lane B - Board Live-Event Backend

Agent: implementation worker.
Mode: implementation_disjoint.
Timebox: 45 minutes.
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/signature.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/webhook.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_signature.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_webhook.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
Must not edit:
- Board frontend files.
Task:
- Implement secret rotation verification, live-event dedup, renamed event handling, heartbeat TTL setting, and operations docs.
Completion evidence:
- `uv run pytest tests/test_config.py tests/test_signature.py tests/test_live_events.py tests/test_webhook.py tests/test_operations_doc.py -q`
Dependencies:
- None.

### Lane C - Board Frontend SSE

Agent: implementation worker.
Mode: implementation_disjoint.
Timebox: 30 minutes.
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/api/sse/live/route.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
Must not edit:
- Board backend live ingestion, config, signature, or webhook files.
Task:
- Implement repo-scoped EventSource URL, reconnect backoff, visibility reconnect, and SSE regression test.
Completion evidence:
- `uv run pytest tests/test_api_routes.py -k "sse_live" -q`
- `npm run lint`
- `npm run build`
Dependencies:
- None, except avoid conflicting backend route edits.

### Lane D - Integration

Agent: root.
Mode: sequential_required.
Timebox: 30 minutes.
Allowed files:
- Both repos for integration fixes within accepted touchpoints.
Must not edit:
- Out-of-scope plugin layers, hooks, MCP servers, app integrations.
Task:
- Run final verification and apply focused fixes.
Completion evidence:
- Final verification plan passes or residual failures are documented.
Dependencies:
- Lanes A, B, and C complete.

## Sequential Gates

- Gate 1: execution package validates.
- Gate 2: RED tests observed for each behavior group before production implementation.
- Gate 3: lane targeted verification passes before integration.
- Gate 4: final verification passes before DONE.

## Verification Plan

- Wily CLI targeted:
  - `python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "event_id" -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "renamed_live or replan" -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "live_heartbeat or board_live_event or renamed_live" -q`
- Wily CLI final:
  - `python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py plugins/wily-roadmap/tests/test_wily_watch_ui.py -q`
- Board backend targeted:
  - `uv run pytest tests/test_config.py tests/test_signature.py tests/test_live_events.py -k "secret or signature" -q`
  - `uv run pytest tests/test_live_events.py -k "dedup" -q`
  - `uv run pytest tests/test_live_events.py tests/test_db.py -k "renamed or live_item" -q`
  - `uv run pytest tests/test_operations_doc.py -q`
  - `uv run pytest tests/test_config.py tests/test_operations_doc.py -q`
- Board frontend targeted:
  - `uv run pytest tests/test_api_routes.py -k "sse_live" -q`
  - `npm run lint`
  - `npm run build`
- Board final:
  - `uv run pytest tests/test_live_events.py tests/test_config.py tests/test_signature.py tests/test_api_routes.py tests/test_db.py tests/test_operations_doc.py -q`
  - `uv run pytest tests/test_webhook.py -q`
  - `npm run lint`
  - `npm run build`

## Rollback / Stop Conditions

- Revert only this task's edits if an attempted change proves unsafe; do not revert unrelated user changes.
- Stop if target file ownership becomes ambiguous due to concurrent user edits that cannot be merged safely.
- Stop if final verification exposes unrelated broken infrastructure that prevents acceptance criteria from being verified.

## Reviewer Notes

- Architect: Plan follows source lane boundaries; integration remains sequential to avoid backend/frontend route conflicts.
- Critic: Test-first behavior is required. Main risks are matching existing helper names and avoiding brittle tests around EventSource behavior.
