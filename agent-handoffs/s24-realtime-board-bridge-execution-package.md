# Execution Package: S24 Realtime Board Bridge End-to-End Hardening

## Native Goal Command

```text
/goal Complete Wily roadmap Stage s24 end to end according to agent-handoffs/s24-realtime-board-bridge-execution-package.md.

First read the execution package. Maintain agent-handoffs/s24-realtime-board-bridge-progress.md.

Keep agent-handoffs/s24-realtime-board-bridge-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped local engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, production secret use, production live event emission, production deploy/restart, push to GitHub, or if the same verification failure repeats twice without new evidence.

Done only when all local acceptance criteria are satisfied and final verification passes: python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest; python3 plugins/wily-roadmap/scripts/wily.py status; python3 plugins/wily-roadmap/scripts/wily.py next.
```

## Source Request / Handoff

User requested: complete all S24 work using `custom-workflow-skillset:plan-goal-runner`.

Primary requirement source:

- `agent-handoffs/s21-realtime-board-bridge-requirements.md`

Roadmap source:

- `.wily/stages/s24-s21-realtime-board-bridge-e2e/stage.md`
- `.wily/stages/s24-s21-realtime-board-bridge-e2e/stage.yaml`
- `.wily/stages/s24-s21-realtime-board-bridge-e2e/verification.md`

## Inline Requirements

Outcome: prove and harden the realtime bridge so active Wily/Codex/CustomWorkflow work reaches Wily status/watch and Wily Board before durable `.wily` push.

In scope:

- Repo-local `.wily/board.json` config and `wily board check` diagnostics.
- Codex hook installation and verification for `live-worked`.
- CustomWorkflow status-board checkpoint parsing and live session attachment.
- Wily status/watch checkpoint overlay rendering and bridge warnings.
- Board live checkpoint event storage, validation, JSON/SSE output, and Hub/repo detail UI parity.
- Local end-to-end proof with temporary local Board configuration.
- Roadmap S24 completion only after local verification evidence is fresh.

Non-goals:

- Do not make Board the durable roadmap source of truth.
- Do not auto-complete durable Wily Phases from checkpoint progress.
- Do not run production smoke, use production secrets, push, deploy, or restart services without explicit user approval.
- Do not add MCP servers or app integrations.

Assumptions:

- Current dirty S21/S24 roadmap and Wily CLI changes are user/pre-existing work and must be preserved.
- Wily Board edits are required for full acceptance. The workspace sandbox may require explicit approval for editing `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- Local E2E can use temporary secrets and local SQLite paths.

## Acceptance Criteria

- `wily board check` reports required config, hook, and endpoint/signature readiness while redacting secrets.
- Missing live bridge config or hook is visible in active Wily status/watch when realtime Board visibility is expected.
- `wily start` remains the canonical live session source for active Stage/Phase work.
- CustomWorkflow status boards attach checkpoint state to that live session without mutating durable Phase status.
- Codex `live-worked` hook activity attaches to the same live session.
- Wily emits signed checkpoint/work events with current checkpoint, current action, blocker, verification, evidence, actor, agent, session, and freshness data.
- Board accepts signed checkpoint/work events and rejects malformed or unsigned checkpoint events.
- Board stores checkpoint overlay separately from durable roadmap tables.
- Board JSON/SSE responses expose checkpoint overlay fields.
- Board Hub and repo detail UI render the same checkpoint/live state shown by Wily status/watch.
- Local E2E proves Wily session, status-board update, worked signal, Board API/SSE, Board UI, and Wily status/watch agree.
- Old false-success mode is covered: if config/hook is missing, realtime success cannot be claimed.
- Production smoke remains a documented, approval-gated checklist.

## File / Ownership Boundaries

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `.wily/stages/s24-s21-realtime-board-bridge-e2e/**`
- `.wily/roadmap.yaml`
- `agent-handoffs/s24-realtime-board-bridge-*.md`

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- `app/live/events.py`
- `app/db/schema.sql`
- `app/db/repo.py`
- `app/api/routes.py`
- `app/web/routes.py`
- `app/web/templates/board.html`
- `app/web/templates/repo_detail.html`
- `frontend/**` if the active Board surface has moved to Next.js for the same data
- `tests/test_live_events.py`
- `tests/test_db.py`
- `tests/test_api_routes.py`
- `tests/test_web_routes.py`
- `tests/test_operations_doc.py`

Must not edit:

- `.playwright-mcp/`
- committed or untracked secret files
- `.wily/board.json` with real production secrets
- production service files unless a checkpoint explicitly proves local work requires documentation updates only

User-owned or pre-existing changes to preserve:

- Existing dirty S21 files and current Wily CLI/watch/test modifications.
- Existing dirty `wily-board` work from S21 unless the change is directly required by S24 and reviewed before editing.

## Execution Plan

Checkpoint 1: Board live config, diagnostics, and hook contract.

- Inspect current Wily config/hook functions and tests.
- Add failing Wily CLI tests for `wily board check` missing-config, redaction, hook diagnostics, and protected repo-local config behavior.
- Implement minimal CLI/config diagnostics.
- Verify targeted Wily CLI tests.

Checkpoint 2: Wily checkpoint session bridge.

- Add failing tests for status-board parsing edge cases, active session reuse, no durable Phase mutation, `live-worked` attachment, and status/watch missing-bridge warnings.
- Implement or harden checkpoint sync/session attachment.
- Verify targeted Wily CLI/watch tests.

Checkpoint 3: Board checkpoint overlay API, SSE, and UI parity.

- Request approval before editing `/Users/wilycastle/Code/projects/wily-plugin/wily-board` if sandbox blocks writes.
- Add failing Board tests for signed checkpoint overlay acceptance, malformed rejection, storage separation, API/SSE fields, Hub rendering, and repo detail rendering.
- Implement schema/repo/live/API/UI changes.
- Verify targeted Board tests.

Checkpoint 4: Local E2E proof, roadmap completion, and production smoke gate.

- Run local Board with temporary SQLite and temporary secret.
- Configure temporary repo-local live config without committing secrets.
- Start a Wily live session, sync checkpoint status, trigger worked signal, and verify Wily status/watch plus Board API/SSE/UI agree.
- Document production smoke gate without running production actions.
- Mark S24 phases done only after local evidence passes.
- Run final verification commands.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Hook installation may be implemented and tested because the user explicitly included hooks in scope.
- Stop for:
  - hard destructive shell commands
  - payment/purchase actions
  - credential or secret exfiltration risk
  - production secret use
  - production live event emission
  - production deploy/restart
  - push to GitHub
  - edits outside the execution package
  - explicit user-forbidden actions
  - repeated verification failure without new evidence

## Live Status Board

- File: `agent-handoffs/s24-realtime-board-bridge-status.md`
- Intended use: keep this Markdown file open in Codex while the goal runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, subagent lane, Superpowers auto-resolution, or final state changes

## Superpowers Skill Routing

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development`: active for CLI/watch/Board behavior changes.
  - `Superpowers:systematic-debugging`: active for failing tests or unexpected runtime behavior.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans`: folded into this execution package.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: read-only explorer lanes only unless disjoint implementation becomes safe.
  - `Superpowers:requesting-code-review`: use integration review before final completion if multi-component changes land.

## Superpowers Autonomy Override

Active. Superpowers approval/review/continue prompts are converted into progress/evidence checkpoints because the user explicitly requested autonomous S24 completion.

Auto-resolution log:

- Auto-resolved under active /goal: writing-plans execution choice prompt -> root goal runner owns sequential implementation with read-only evidence lanes.
- Auto-resolved under active /goal: Superpowers design/review gates -> execution package and local verification evidence replace user gates unless a narrow hard-stop condition occurs.

## Goal Runtime Contract

Progress log:

- `agent-handoffs/s24-realtime-board-bridge-progress.md`

Live status board:

- `agent-handoffs/s24-realtime-board-bridge-status.md`

Verification evidence:

- `agent-handoffs/s24-realtime-board-bridge-verification.md`

Baseline:

- Current git status is dirty and must be preserved.
- Current Wily status reports s24 pending and 24-1 next.
- Known production bridge state: no production secrets should be used; production smoke is approval-gated.

User / pre-existing changes:

- Pre-existing modified Wily files include `.wily/**`, `plugins/wily-roadmap/scripts/wily.py`, `plugins/wily-roadmap/scripts/wily_watch_ui.py`, `plugins/wily-roadmap/tests/test_wily_cli.py`, `plugins/wily-roadmap/tests/test_wily_watch_ui.py`, and `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`.
- Pre-existing untracked handoffs and S21/S24 phase files must not be removed.
- If a target file has unrelated user changes, preserve them and continue when possible; stop only if safe editing is impossible.

Pre-existing modified files:

- `.wily/roadmap.yaml`
- `.wily/stages/s21-wily-board-ui-redesign/handoff.md`
- `.wily/stages/s21-wily-board-ui-redesign/prompt.md`
- `.wily/stages/s21-wily-board-ui-redesign/stage.md`
- `.wily/stages/s21-wily-board-ui-redesign/stage.yaml`
- `.wily/stages/s21-wily-board-ui-redesign/verification.md`
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`

Pre-existing untracked files:

- `.playwright-mcp/`
- `.wily/revisions/2026-05-17-015345-replan-24.md`
- `.wily/revisions/2026-05-17-092156-replan-25.md`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-2-customworkflow-checkpoint-phase-contract/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-3-wily-live-checkpoint-adapter/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-4-board-checkpoint-storage-api/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-5-nextjs-scaffold-auth/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-6-hub-my-desk-checkpoints/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-7-repo-workspace-checkpoints/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-8-preferences-polish-checkpoints/`
- `.wily/stages/s21-wily-board-ui-redesign/phases/21-9-readonly-cutover-ops/`
- `.wily/stages/s24-s21-realtime-board-bridge-e2e/`
- `agent-handoffs/s21-board-ui-redesign-execution-package.md`
- `agent-handoffs/s21-board-ui-redesign-progress.md`
- `agent-handoffs/s21-board-ui-redesign-status.md`
- `agent-handoffs/s21-board-ui-redesign-verification.md`
- `agent-handoffs/s21-realtime-board-bridge-requirements.md`
- `agent-handoffs/s24-realtime-board-bridge-execution-package.md`
- `agent-handoffs/s24-realtime-board-bridge-progress.md`
- `agent-handoffs/s24-realtime-board-bridge-status.md`
- `agent-handoffs/s24-realtime-board-bridge-verification.md`

Checkpoint loop:

1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused test-first change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log with files changed, commands run, results, evidence, next step, and blockers.
7. Continue until DONE, PARTIAL, or BLOCKED unless a narrow hard-stop condition is triggered.

Finalization:

1. Run final verification commands.
2. Review acceptance criteria line by line.
3. Update roadmap Stage s24 phase status.
4. Update status board to DONE, PARTIAL, or BLOCKED.
5. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: Wily CLI/watch and Board app facts can be explored independently, but implementation should be integrated sequentially because payload, schema, and rendering contracts must stay aligned.

## Lane Handoffs

### Lane A - Wily CLI/Watch Explorer

Agent: explorer
Mode: read_only_evidence
Timebox: 15 minutes
Allowed files: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
Must not edit: all files
Task: map current Wily config, checkpoint sync, live-worked, hooks, and watch/status rendering code and tests.
Completion evidence: concise function/test map and gap list.
Dependencies: none.

### Lane B - Board Explorer

Agent: explorer
Mode: read_only_evidence
Timebox: 15 minutes
Allowed files: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
Must not edit: all files
Task: map current Board live event, DB, API/SSE, and UI rendering support for checkpoint overlay.
Completion evidence: concise file/test map and gap list.
Dependencies: none.

## Sequential Gates

- Gate 1: Do not edit production secrets or production config.
- Gate 2: Do not edit `/Users/wilycastle/Code/projects/wily-plugin/wily-board` unless sandbox permits it or the user approves an escalated edit path.
- Gate 3: Do not mark S24 done until local E2E evidence exists or the status is explicitly PARTIAL with missing evidence named.

## Reviewer Gates

- Architect review: root runner reviews explorer evidence before Board schema/API implementation.
- Critic review: root runner validates the execution package with the validator before implementation.
- integration_reviewer: root runner performs an integration review of Wily CLI/watch and Board API/UI contracts together before final completion.
- completion_verifier: root runner runs final verification and acceptance checklist before marking DONE/PARTIAL/BLOCKED.

## Verification Plan

Targeted Wily verification:

```bash
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_checkpoint_sync_reads_custom_workflow_status_board_without_completing_phase
python3 -m unittest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest.test_render_shows_checkpoint_overlay_from_local_live_registry
```

Expanded Wily verification:

```bash
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest plugins.wily-roadmap.tests.test_wily_watch_ui.RenderWatchTest
```

Board targeted verification:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_live_events.py tests/test_db.py tests/test_api_routes.py tests/test_web_routes.py -q
```

Board full verification:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
```

Wily roadmap verification:

```bash
python3 plugins/wily-roadmap/scripts/wily.py status
python3 plugins/wily-roadmap/scripts/wily.py next
```

Local E2E smoke:

- Start local Board with temporary SQLite and secret.
- Configure temporary `.wily/board.json` or equivalent isolated test config.
- Start Wily phase 24-1 or fixture phase.
- Sync a CustomWorkflow status board.
- Trigger `live-worked`.
- Confirm Wily status/watch and Board API/SSE/UI agree.

## Rollback / Stop Conditions

- Revert only changes made by this goal if rollback is needed.
- Never revert pre-existing user changes without explicit instruction.
- Stop if production secret use is required.
- Stop if editing `wily-board` is impossible under the sandbox and approval is denied.
- Stop if the same verification failure repeats twice without new evidence.
- Stop if local E2E cannot be made observable without production dependencies.

## Reviewer Notes

- Architect: pending root review after explorer evidence.
- Critic: pending root review after validator.
