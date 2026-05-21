# Execution Package: Board Live Local State And Checkpoint Visibility

## Native Goal Command

```text
/goal Complete Wily Board live local state and checkpoint visibility according to agent-handoffs/board-live-local-state-execution-package.md.

First read the execution package. Maintain agent-handoffs/board-live-local-state-progress.md.

Keep agent-handoffs/board-live-local-state-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped local engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, production live event emission, production deploy/restart, GitHub push/PR/merge, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build; python3 plugins/wily-roadmap/scripts/wily.py status; python3 plugins/wily-roadmap/scripts/wily.py board check --probe.
```

## Source Request / Handoff

Primary requirements handoff:

- `agent-handoffs/board-live-local-state-requirements.md`

User request summary:

- Fix Wily Board not showing Custom Workflow checkpoint/phase-decomposition state.
- Fix Wily Board not reflecting realtime work data.
- Concrete regression: this repo is locally at Stage `s25`, but Board still shows only through `s24`.
- Create a handoff first, then run a goal from that handoff.

## Inline Requirements

Outcome: Wily Board's Next/API surface must display local Wily Stage/Phase topology and checkpoint overlays before durable GitHub sync catches up, while marking that data as provisional local live/draft state.

In scope:

- Wily CLI local draft replay for current decomposed Stage topology.
- Board API projection of `live_drafts` into repo detail, repo progress, desk/follow-up, and SSE refresh behavior.
- Next.js UI type/rendering support for draft Stages/Phases and checkpoint overlays.
- Focused tests and a local-only smoke path.

Non-goals:

- No Board mutation workflow.
- No new hooks, MCP servers, app integrations, schema-heavy activity model, production deploy/restart, GitHub push, or production live event emission.
- Do not execute the broader Stage `s25` UI polish roadmap.

Assumptions:

- Existing `live_drafts` storage is enough; schema changes should be avoided unless tests prove otherwise.
- `wily board sync-local [stage-id]` is an acceptable local-first CLI shape for replaying local topology.
- Durable GitHub sync remains authoritative and continues to clear matching drafts after durable phases arrive.

## Acceptance Criteria

- Wily CLI exposes a local board draft replay command or equivalent path that emits the current local decomposed Stage topology as a signed `stage_decomposed_local` event.
- Replay can target `s25` and includes Stage metadata plus normalized child Phases.
- Missing Board config still produces a visible warning and no command failure.
- Board API `/api/repos/{owner}/{name}` includes draft-only Stages when durable Board DB state does not yet include them.
- Board API repo progress can represent local draft Stages, so a repo with durable `s01..s24` plus local draft `s25` appears as `24/25`, not complete `24/24`.
- Draft child Phase rows can display checkpoint overlays from live item/session payloads.
- Hub/MY DESK API includes a visible draft follow-up or active item for local topology awaiting push.
- SSE refresh includes new draft/live events so the Next app refreshes after draft topology and checkpoint updates.
- Durable sync reconciliation still hides/clears draft rows when matching durable child Phases arrive.
- Regression tests cover durable state through `s24` plus live draft `s25` with checkpoint overlay on `25-1`.

## File / Ownership Boundaries

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `agent-handoffs/board-live-local-state-*.md`

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- `app/api/routes.py`
- `app/db/repo.py`
- `frontend/lib/types.ts`
- `frontend/components/phase-list.tsx`
- `frontend/components/desk.tsx`
- `frontend/components/repo-list.tsx`
- `frontend/components/live-refresh.tsx`
- `tests/test_api_routes.py`
- `tests/test_live_events.py`
- `tests/test_web_routes.py`

Must not edit:

- `.playwright-mcp/`
- secret-bearing local Board config files
- production deploy/service files
- `.agents/plugins/marketplace.json`
- `plugins/wily-roadmap/.codex-plugin/plugin.json`
- unrelated generated screenshots or build output

User-owned or pre-existing changes to preserve:

- All dirty `.wily` roadmap state in `wily-roadmap`, especially `s25`.
- Existing Board changes in `app/live/events.py` and `tests/test_live_events.py`.
- Existing untracked handoff directories in both repos.

## Execution Plan

CP01: Baseline and regression tests.

- Record dirty status for both repos.
- Add failing Wily CLI test for `wily board sync-local s25` or the chosen equivalent replay command.
- Add failing Board API tests for durable `s24` plus live draft `s25` repo detail/progress/desk/SSE behavior.
- Add or extend Next-facing tests only where the existing test harness can cover payload and rendering without broad browser work.

CP02: Wily CLI local draft replay.

- Implement local topology replay under `wily board sync-local [stage-id]`.
- Reuse existing `live_draft_stage_decomposition_payload` and `emit_stage_decomposition_live_draft`.
- Include Stage metadata: title, status, owner, depends_on, execution mode, raw path, and position.
- Keep warnings local-first and non-fatal when config or endpoint is missing.
- Verify targeted Wily CLI tests.

CP03: Board API draft projection.

- Add helper logic to project `live_drafts` into API repo detail, including draft-only Stages and draft Phases.
- Attach live item/session checkpoint overlays to draft Phase payloads by phase id.
- Overlay repo progress totals with active draft-only Stages.
- Add draft followups to desk payload without renaming the existing UI sections unless required.
- Ensure durable phases still win when durable sync catches up.
- Verify targeted Board API/live/web route tests.

CP04: Next.js rendering and live refresh.

- Update TypeScript types for draft metadata.
- Render draft Stage/Phase rows with clear `local draft` / `awaiting push` markers and checkpoint rows.
- Ensure repo list/progress and desk chips show draft/live context.
- Extend live refresh to react to draft/live event refresh signals.
- Verify frontend lint/build.

CP05: Local smoke, evidence, and final verification.

- Run local-only smoke using temporary Board DB/events where possible; do not emit production live events.
- Optionally replay to a local Board endpoint only if the endpoint is local/test-owned.
- Run final verification commands.
- Update status/progress/verification files and final state.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Local test servers, temporary SQLite DBs, and generated temporary fixtures are allowed.
- Do not use production secrets, send production live events, deploy, restart services, push to GitHub, create PRs, merge, or mutate remote state without explicit user approval.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, required edits outside this package, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/board-live-local-state-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, Superpowers auto-resolution, or final state changes
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
  - `Superpowers:test-driven-development`: active for CLI/API/UI behavior changes.
  - `Superpowers:systematic-debugging`: active for failing tests or unexpected runtime behavior.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans`: this execution package is the task-level plan.
  - `Superpowers:using-git-worktrees`: skipped because the user did not request a separate worktree and current dirty state must be preserved in place.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: skipped because subagents require explicit user authorization in this environment; root goal owns sequential integration.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch`: not required unless the user asks for review/PR/merge.

## Superpowers Autonomy Override

- Active when native `/goal` is active or the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

Auto-resolved under active /goal: `Superpowers:brainstorming` design approval gate -> the user explicitly requested a Custom Workflow handoff and goal; this execution package records the design and boundaries before implementation.

## Goal Runtime Contract

Progress log:

- `agent-handoffs/board-live-local-state-progress.md`

Live status board:

- `agent-handoffs/board-live-local-state-status.md`

Verification evidence:

- `agent-handoffs/board-live-local-state-verification.md`

Baseline:

- Current `wily-roadmap` status: dirty; local roadmap version 27; `s25` is current/next; Board config probe passes.
- Current `wily-board` status: dirty; existing modified files are `app/live/events.py` and `tests/test_live_events.py`.
- Known issue: Board API/Next path does not project `live_drafts`, so local draft topology can be invisible even when stored.

User / pre-existing changes:

- Preserve all pre-existing changes and untracked files.
- If target files contain user work, inspect diffs before editing and make additive scoped changes.
- Stop only if safe editing is impossible.

Pre-existing modified files:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/roadmap.yaml`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/status.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`

Pre-existing untracked files:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.playwright-mcp/`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/revisions/2026-05-17-132403-replan-26.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/stages/s25-wily-board-ui-polish-usability/`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/p6-bridge-durable-sync-handoff.md`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/agent-handoffs/`

Checkpoint loop:

1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log:
   - checkpoint name
   - files changed
   - commands run
   - result
   - evidence file updates, if any
   - status board update
   - next step
   - blockers / risks
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:

- At the end of each execution package step.
- Before changing component boundaries.
- After any failed verification retry.

Narrow hard-stop conditions:

- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside the execution package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Payment/purchase action is needed.
- Credential or secret exfiltration risk is discovered.
- Production live event, production deploy, production restart, GitHub push/PR/merge, or secret-bearing command is required.
- Explicit user-forbidden action is needed.
- Tests fail in a way that cannot be attributed to the current change.

Finalization:

1. Run final verification commands.
2. Apply `completion_verifier` discipline locally by checking acceptance criteria against evidence.
3. Apply `integration_reviewer` discipline locally because this is multi-component Wily CLI + Board API + Next UI work.
4. Update `agent-handoffs/board-live-local-state-status.md` to DONE, PARTIAL, or BLOCKED.
5. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED
Reason: The change crosses two repos and shared data contracts. Subagent implementation is not authorized in this turn, and the safest path is one root integration loop with focused checkpoints.

## Lane Handoffs

### Lane A — Root Sequential Integration

Agent: root
Mode: sequential_required
Timebox: current goal
Allowed files: listed in File / Ownership Boundaries
Must not edit: listed in File / Ownership Boundaries
Task: implement the CLI replay, Board API projection, Next UI rendering, and verification.
Completion evidence: tests, lint/build, local smoke, status/progress/verification logs.
Dependencies: none.

## Sequential Gates

- Gate 1: failing regression tests exist before implementation.
- Gate 2: Wily CLI targeted tests pass after replay command.
- Gate 3: Board API tests pass after draft projection.
- Gate 4: frontend lint/build pass after UI updates.
- Gate 5: final verification commands pass.

## Verification Plan

- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py`
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build`
- `python3 plugins/wily-roadmap/scripts/wily.py status`
- `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`

## Rollback / Stop Conditions

- Prefer additive code changes and test fixtures that can be individually reverted if needed.
- Do not remove existing live draft, checkpoint, or durable sync behavior.
- If a Board API projection creates duplicate durable/draft rows after sync, stop and fix before proceeding.
- If final verification repeatedly fails without a new hypothesis, mark BLOCKED with evidence rather than broadening scope.

## Reviewer Notes

- Architect: local draft topology already exists in storage and Jinja routes; the missing piece is Next/API projection plus a replay path for non-`decompose-stage` local authoring.
- Critic: biggest regression risk is duplicate rows after durable sync or stale draft data changing progress totals after a sync. Tests must cover durable-wins behavior.
