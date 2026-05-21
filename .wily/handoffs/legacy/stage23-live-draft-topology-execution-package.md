# Execution Package: Stage 23 Live Draft Topology Overlay

## Native Goal Command

```text
/goal Complete Stage 23 live draft topology overlay according to agent-handoffs/stage23-live-draft-topology-execution-package.md.

First read the execution package. Maintain agent-handoffs/stage23-live-draft-topology-progress.md.

Keep agent-handoffs/stage23-live-draft-topology-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest; python3 plugins/wily-roadmap/scripts/wily.py status; python3 plugins/wily-roadmap/scripts/wily.py next.
```

## Source Request / Handoff

User requested: "Stage 23 작업 전부 완벽하게 끝내줘" using `custom-workflow-skillset:plan-goal-runner`.

Primary design and plan:

- `docs/superpowers/specs/2026-05-17-wily-board-live-draft-topology-design.md`
- `docs/superpowers/plans/2026-05-17-wily-board-live-draft-topology.md`

## Inline Requirements

Outcome: locally decomposed Wily Stages must appear on Wily Board before commit/push as provisional topology, then disappear when durable GitHub sync catches up.

In scope:

- Wily Roadmap CLI emits `stage_decomposed_local` draft events from `decompose-stage`.
- Wily Board validates, stores, renders, and reconciles draft topology.
- Stage 23 roadmap phases are completed after implementation and verification.

Non-goals:

- Board must not directly write to repositories.
- No MCP server, app integration, or workspace permission layer.
- No polling developer machines from Board.

Assumptions:

- Existing Board HMAC secret flow remains authoritative for local live events.
- Existing `.wily` GitHub sync remains the durable source of truth.
- Pre-existing S-21 decomposition files in the roadmap repo are user work and must be preserved.

## Acceptance Criteria

- `decompose-stage --from-json` sends a signed `stage_decomposed_local` event when Board config exists.
- Missing Board config produces a visible CLI warning while local decomposition still succeeds.
- Board accepts valid `stage_decomposition` draft payloads and rejects malformed ones.
- Board stores topology drafts in `live_drafts`, separate from `live_items` and `live_sessions`.
- Repo detail renders provisional child phases with `local draft` and `awaiting push` markers before durable phases exist.
- Dashboard shows a follow-up item for draft topology awaiting push.
- Durable sync clears matching drafts when durable child phases for the same repo/stage arrive.
- Full Wily Roadmap CLI test suite passes.
- Full Wily Board pytest suite passes.
- `wily status` shows Stage 23 complete and Stage 21 next.

## File / Ownership Boundaries

Expected touchpoints:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/docs/superpowers/plans/2026-05-17-wily-board-live-draft-topology.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/repo_detail.html`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

Must not edit:

- `.playwright-mcp/`
- secrets or local Board config files
- unrelated generated screenshots

User-owned or pre-existing changes to preserve:

- Existing S-21 decomposition files and UI redesign spec in `wily-roadmap`
- Any dirty work already present before this goal began

User / pre-existing changes: preserve all files listed below and do not revert user-owned roadmap edits.

## Dirty Working Tree Guard

- Do not revert or overwrite pre-existing roadmap changes.
- Before editing a dirty file, inspect the relevant diff and make additive scoped changes.
- Generated `.playwright-mcp/` remains untracked and out of scope.

Pre-existing modified files:

- `.wily/roadmap.yaml`
- `.wily/status.md`
- `.wily/stages/s21-wily-board-ui-redesign/handoff.md`
- `.wily/stages/s21-wily-board-ui-redesign/prompt.md`
- `.wily/stages/s21-wily-board-ui-redesign/stage.md`
- `.wily/stages/s21-wily-board-ui-redesign/verification.md`
- `.wily/revisions/2026-05-17-003112-replan-22.md`
- `.wily/revisions/2026-05-17-004453-replan-23.md`
- `.wily/stages/s21-wily-board-ui-redesign/phases/`
- `.wily/stages/s21-wily-board-ui-redesign/stage.yaml`
- `.wily/stages/s23-wily-board-live-draft-topology-overlay/`
- `docs/superpowers/plans/2026-05-17-wily-board-live-draft-topology.md`
- `docs/superpowers/specs/2026-05-16-wily-board-ui-redesign-design.md`

## Execution Plan

Checkpoint 1: Wily CLI event emission.

- Add failing tests in `test_wily_cli.py`.
- Implement draft payload normalization.
- Emit event from successful `decompose-stage` apply paths.
- Print missing-config warning when event cannot be sent.
- Verify targeted Wily CLI tests.

Checkpoint 2: Board draft storage/API.

- Add `live_drafts` schema and migration guard.
- Add normalization, upsert, list, and clear helpers.
- Extend `/api/live/events` validation/storage.
- Verify DB and live event API tests.

Checkpoint 3: Board rendering.

- Add draft listing to repo detail/dashboard context.
- Render draft phase rows with clear provisional badges.
- Add dashboard follow-up item.
- Verify web route tests.

Checkpoint 4: Durable sync reconciliation.

- Clear matching drafts during `replace_repo_state` when durable stage phases exist.
- Verify clearing tests and no regressions in existing live overlay behavior.

Checkpoint 5: Roadmap completion and final verification.

- Update Stage 23 phase status to done through Wily workflow or direct roadmap state edits when CLI lifecycle cannot apply cleanly.
- Run full verification commands.
- Update status/progress/verification logs.
- Mark native goal complete only after evidence is fresh.

## Autonomous Action Policy

- Goal-scoped engineering actions may proceed without user approval.
- This includes local commits only if needed to preserve checkpoints; no push is required unless explicitly requested.
- Stop for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/stage23-live-draft-topology-status.md`
- Intended use: keep this Markdown file open in Codex while the goal runs.
- Update cadence: before and after every checkpoint, after verification, and on blocker/final state changes.

## Superpowers Skill Routing

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development`: active for CLI/API/DB/UI behavior changes.
  - `Superpowers:systematic-debugging`: active if tests or runtime checks fail.
- Required before done:
  - `Superpowers:verification-before-completion`
- Conditional:
  - `Superpowers:writing-plans`: already used to produce the implementation plan.
  - `Superpowers:subagent-driven-development`: read-only explorer/review lanes are active; root goal owns integration.

## Superpowers Autonomy Override

Active. Superpowers approval/review/continue prompts are converted into progress checkpoints because the user explicitly requested autonomous completion.

Active goal auto-resolution log:

- Auto-resolved under active /goal: Superpowers design/plan approval gates -> user explicitly requested Stage 23 autonomous completion after reviewing the plan.
- Auto-resolved under active /goal: Superpowers execution choice prompt -> root goal runner owns sequential integration with read-only explorer lanes.
- Auto-resolved under active /goal: commit/review prompts -> local verification checkpoints replace user gates unless a narrow hard-stop condition occurs.

## Goal Runtime Contract

Progress log:

- `agent-handoffs/stage23-live-draft-topology-progress.md`

Live status board:

- `agent-handoffs/stage23-live-draft-topology-status.md`

Verification evidence:

- `agent-handoffs/stage23-live-draft-topology-verification.md`

Baseline:

- Current git status is recorded in the progress log.
- Known pre-existing dirty roadmap files must be preserved.
- Wily Board starts clean on `main`.

Checkpoint loop:

1. Choose the next checkpoint.
2. Update status board.
3. Make focused TDD change.
4. Run checkpoint verification.
5. Append progress/evidence.
6. Continue until DONE, PARTIAL, or BLOCKED.

Narrow hard-stop conditions:

- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches out-of-scope files.
- Hard destructive shell command is needed.
- Credential or secret exfiltration risk is discovered.
- Existing user changes would have to be overwritten.

Finalization:

1. Run final verification commands.
2. Review acceptance criteria line by line.
3. Update roadmap Stage 23 status.
4. Update status board to DONE, PARTIAL, or BLOCKED.
5. Summarize diff, verification, and residual risks.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: Wily CLI and Board code can be inspected independently. Implementation is sequential at integration time because event payload, schema, and rendering contracts must stay aligned.

## Lane Handoffs

### Lane A — Wily CLI Explorer

Agent: explorer
Mode: read_only_evidence
Allowed files: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
Task: identify exact CLI helpers and tests for draft event emission.
Completion evidence: concise function/test map.

### Lane B — Board Explorer

Agent: explorer
Mode: read_only_evidence
Allowed files: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
Task: identify DB/API/sync/render touchpoints.
Completion evidence: concise function/test map.

### Lane C — Plan Critic

Agent: default
Mode: review_verification
Allowed files: read-only across both repos.
Task: identify gaps or sequencing risks in Stage 23 plan.
Completion evidence: review notes.

## Sequential Gates

- Gate 1: CLI targeted tests pass.
- Gate 2: Board DB/API targeted tests pass.
- Gate 3: Board route rendering tests pass.
- Gate 4: full verification passes.
- Gate 5: Wily roadmap shows Stage 23 complete and Stage 21 next.

## Reviewer Gates

- Repo explorer: collect Wily CLI touchpoints before implementation.
- Repo explorer: collect Board DB/API/render touchpoints before implementation.
- Plan critic: review architecture and sequencing risks before implementation.
- completion_verifier: run final acceptance checklist before DONE.
- integration_reviewer: review multi-component contract after implementation.

## Verification Plan

Targeted:

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_live_events.py tests/test_db.py tests/test_web_routes.py
```

Final:

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
python3 plugins/wily-roadmap/scripts/wily.py status
python3 plugins/wily-roadmap/scripts/wily.py next
```

## Rollback / Stop Conditions

Rollback is local git revert or patch reversal of the changed files. Stop if schema migration cannot be made compatible with existing databases, if signed event auth requires secrets not available locally, or if tests repeatedly fail without a new root-cause hypothesis.

## Reviewer Notes

- Architect: pending read-only review.
- Critic: pending read-only review.
