# Execution Package: S27 Stage/Phase Contract Refactor

## Native Goal Command

```text
/goal Complete S27, the Wily Roadmap Stage/Phase contract refactor, according to agent-handoffs/s27-refactor-execution-package.md.

First read the execution package, agent-handoffs/s27-refactor-contract-requirements.md, and docs/superpowers/specs/2026-05-17-s27-refactor-design.md. Maintain agent-handoffs/s27-refactor-progress.md.

Keep agent-handoffs/s27-refactor-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped local engineering actions. Preserve the repository rule that Wily behavior remains local-first and approval-first for remote actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Do not stop merely because local goal-scoped engineering work is non-trivial. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, production deploy/restart, production secret use, remote push, PR creation/update, merge, GitHub issue mutation, GitHub comments, irreversible migration cleanup, or if the same verification failure repeats twice without new evidence.

Use Superpowers routing during implementation: test-driven-development for behavior changes, systematic-debugging for failures, verification-before-completion before any completion claim, writing-plans as task-granularity guidance, and dispatching/subagent skills only for bounded lanes whose file ownership is disjoint.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py; python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py; python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py; python3 -m pytest plugins/wily-roadmap/tests/test_wily_watch_ui.py; python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py; ./plugins/wily-roadmap/wily status; ./plugins/wily-roadmap/wily next; ./plugins/wily-roadmap/wily watch --once --ui ascii; ./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run; disposable fixture apply/status/next/run dry-run verification; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run.
```

## Source Request / Handoff

User requested: use `custom-workflow-skillset:plan-goal-runner` to create the S27 execution package, without implementing yet.

Primary sources:

- `agent-handoffs/s27-refactor-contract-requirements.md`
- `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`

Roadmap source:

- `.wily/stages/s27-wily-roadmap-large-refactor/stage.md`
- `.wily/stages/s27-wily-roadmap-large-refactor/stage.yaml`
- `.wily/stages/s27-wily-roadmap-large-refactor/handoff.md`
- `.wily/stages/s27-wily-roadmap-large-refactor/prompt.md`
- `.wily/stages/s27-wily-roadmap-large-refactor/verification.md`

The current user request is package-only. This file is the implementation handoff for a later `/goal`; it does not mark S27 started or implemented.

## Inline Requirements

Outcome: refactor Wily Roadmap from the current `stage-v1`/legacy phase mix into the official `wily-roadmap-v2` durable model where Stage is the aggregation and collaboration boundary, Phase is the only execution unit, Custom Workflow Skillset remains an external black-box runner, and Watch plus Wily Board share projection semantics for Stage/Phase/checkpoint display.

In scope:

- Durable `Stage -> Phase` schema v2 contract and implementation.
- Phase-only command behavior for lifecycle and runner commands.
- Explicit local `wily migrate-state` command with dry-run, apply, backup, report, validation, and approval-gated prune.
- Custom Workflow adapter boundary and status-board checkpoint overlay parsing.
- Shared `RoadmapProjection`/`wily-roadmap-projection-v1` semantics for status, watch, Board emitters, and Board rendering.
- Wily Board read-only alignment, including `/me`, `/collab`, repo detail, checkpoint rows, visibility, and responsive web-native IA.
- Skills, command docs, references, and tests needed to make the contract executable.
- Two-repo final verification across `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` and `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.

Non-goals:

- Do not edit the Custom Workflow Skillset plugin.
- Do not make Wily Board the durable roadmap source of truth.
- Do not add mutation UI to Wily Board for roadmap state in S27.
- Do not add hooks, MCP servers, app integrations, or new plugin layers.
- Do not rewrite completed S01-S24 Git history.
- Do not run production deploys, remote pushes, PR creation/update, merges, GitHub issue/comment mutations, or production live events without explicit user approval.
- Do not delete legacy `.wily/phases/**`, sessions, revisions, handoffs, or backups by default.

Assumptions:

- The current dirty worktree is user/pre-existing work and must be preserved.
- The Wily Board repo currently has its own dirty worktree; the S27 runner must inspect and preserve it before editing.
- Actual migration apply against real working repos remains approval-gated unless the user explicitly authorizes it during S27. Disposable fixture apply is in scope.
- Wily Board visual verification is required only when Board UI surfaces change; production visual verification remains approval-gated.

## Acceptance Criteria

- `roadmap_schema: "wily-roadmap-v2"` is the official durable model, with `.wily/roadmap.yaml` containing Stage list only.
- `.wily/stages/<stage-id>-<slug>/stage.yaml` contains child Phases; `.wily/phases/**` is legacy input/archive after migration.
- Canonical Phase identity is `(stage_id, phase_id)` and user-facing references use `<stage-id>/<phase-id>`.
- Stage is not executable. All lifecycle and execution commands target a Phase identity.
- Passing a Stage id to Phase-only commands fails clearly and suggests the next ready Phase, `wily decompose-stage`, or `wily migrate-state` as applicable.
- Stage status display is derived or normalized from child Phase status and Stage dependencies using documented aggregate rules.
- `wily next` reports both next ready Stage and next executable Phase.
- `wily run <stage-id>/<phase-id>` uses the default `custom-workflow` runner adapter.
- Custom Workflow remains black-box; Wily adapts to its artifacts and never edits its plugin files.
- Custom Workflow status-board checkpoints materialize only as non-durable child rows under the owning Wily Phase in Watch and Board.
- Checkpoint rows never mark a Wily Phase done by themselves.
- Watch and Board consume the same projection semantics.
- Wily Board is read-only for roadmap state and renders Stage/Phase/checkpoint topology, live activity, stale/fresh status, risk/attention, and next work.
- `/me`, `/collab`, and `/repos/[owner]/[name]` surfaces follow the IA in the design spec.
- Migration supports dry-run, apply, backup, human-readable and machine-readable reports, validation, and optional explicit legacy prune.
- Migration preserves completed work evidence, session paths, verification files, handoff references, and id mappings where possible.
- The final verification plan passes in Wily Roadmap and Wily Board, with disposable fixture apply before any real repo apply.

## File / Ownership Boundaries

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

- `agent-handoffs/s27-refactor-*.md`
- `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_runner.py`
- `plugins/wily-roadmap/scripts/wily_state_summary.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- Possible new focused helper modules under `plugins/wily-roadmap/scripts/`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_command_skills.py`
- New migration/projection fixtures under `plugins/wily-roadmap/tests/fixtures/`
- `plugins/wily-roadmap/skills/**`
- `plugins/wily-roadmap/skills/wily-workflow/references/**`
- `plugins/wily-roadmap/README.md`
- `README.md`
- `.wily/stages/s27-wily-roadmap-large-refactor/**`
- `.wily/roadmap.yaml`

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- `app/api/routes.py`
- `app/db/*.sql`
- `app/db/repo.py`
- `app/live/events.py`
- `tests/test_live_events.py`
- `tests/test_api_routes.py`
- Other existing Board backend tests if they cover changed behavior.
- `frontend/app/page.tsx`
- `frontend/app/me/**`
- `frontend/app/collab/**`
- `frontend/app/repos/[owner]/[name]/**`
- `frontend/components/**` for active Phase, repo grid, live strip, risk queue, stage map, phase list, checkpoint rows, and shared chrome.
- `frontend/lib/types.ts`
- `frontend/app/globals.css` and component-level styles only as needed for the IA.

Must not edit:

- Custom Workflow Skillset plugin files under `/Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/**`.
- `.agents/plugins/marketplace.json`, except to preserve its required `./plugins/wily-roadmap` pointer if verification detects drift.
- `plugins/wily-roadmap/.codex-plugin/plugin.json`, except to preserve manifest validity if verification detects drift.
- `.wily/local/**` secrets or machine-local config.
- Legacy `.wily/phases/**` through real destructive cleanup unless the user explicitly approves `--prune-legacy`.
- Completed S01-S24 history except read-only inspection and migration fixture/reference handling.
- Production service files, production secrets, deploy scripts, or remote configuration unless the user explicitly expands scope.

User-owned or pre-existing changes to preserve:

- Current modified Wily files: `.wily/roadmap.yaml`, `.wily/status.md`.
- Current untracked Wily files/directories include `.playwright-mcp/`, new `.wily/revisions/*`, `.wily/stages/s25-*`, `.wily/stages/s26-*`, `.wily/stages/s27-*`, `agent-handoffs/board-live-local-state-*`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`, `agent-handoffs/s27-refactor-contract-requirements.md`, and `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`.
- Current Wily Board modified files include `app/api/routes.py`, `app/live/events.py`, `app/web/routes.py`, `app/web/static/app.css`, `app/web/templates/_phase_row.html`, `app/web/templates/board.html`, `frontend/app/globals.css`, `frontend/components/desk.tsx`, `frontend/components/phase-list.tsx`, `frontend/components/stage-map.tsx`, `frontend/lib/types.ts`, `tests/test_api_routes.py`, `tests/test_live_events.py`, and `tests/test_web_routes.py`, plus untracked `agent-handoffs/`.
- If a target file has unrelated user changes, preserve them and continue when possible; stop only if safe editing is impossible.

## Execution Plan

Checkpoint 1: Contract freeze and fixtures (`s27/p01`).

- Re-read the two S27 source docs and current Wily reference docs.
- Resolve the four open questions from the design spec into concrete defaults:
  - direct Stage migration Phase title policy,
  - `/me` redirect versus remembered surface,
  - Board stale threshold,
  - migration backup retention default.
- Add or update final contract/reference docs and migration/projection fixture examples for v1-only, mixed legacy, and already-v2 state.
- Do not change runtime behavior in this checkpoint except fixture/test scaffolding.
- Verification: markdown self-review, fixture readability checks, no vague markers such as unresolved blanks, and targeted command-skill/reference tests if docs affect tested skill text.

Checkpoint 2: State schema and parser boundary (`s27/p02`).

- Use TDD with v2 fixtures before implementation.
- Introduce or extract focused state helpers for schema detection, Stage-local Phase parsing, canonical `(stage_id, phase_id)` identity, Stage dependency checks, invariant warnings, and aggregate status calculation.
- Remove ongoing execution reliance on top-level `phases:` for v2 repos while retaining legacy detection for migration guidance.
- Verification: `python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py` plus targeted parser fixture tests.

Checkpoint 3: Explicit migration command (`s27/p03`).

- Add `wily migrate-state --to wily-roadmap-v2 --dry-run|--apply|--prune-legacy`.
- Implement preflight, backup, transform, report, validation, and rollback guidance.
- Preserve sessions, handoff references, verification evidence, completed/blocked statuses, and id mappings.
- Require explicit prune flag for irreversible legacy cleanup.
- Verification: CLI migration tests, dry-run no-write tests, apply against disposable fixtures, report content tests, and no default destructive cleanup.

Checkpoint 4: Phase-only lifecycle commands (`s27/p04`).

- Update `start`, `run`, `complete`, `block`, `retry`, `release`, `live-heartbeat`, `live-worked`, and `checkpoint-sync` to resolve `<stage-id>/<phase-id>`.
- Reject Stage ids for Phase-only commands with actionable suggestions.
- Recompute or normalize Stage aggregate status after Phase mutations.
- Verification: CLI tests for Stage rejection, Stage-local Phase lifecycle, aggregate recomputation, and status/watch behavior after transitions.

Checkpoint 5: Runner adapter registry and Custom Workflow default (`s27/p05`).

- Replace legacy `find_phase(phase_id)` assumptions in `wily_runner.py` with a Stage-local runner context.
- Add or clarify adapter registry behavior for `custom-workflow`.
- Make `wily run <stage-id>/<phase-id> --dry-run` verify request generation without durable mutation/session creation.
- Print or record the exact Custom Workflow route and artifact paths.
- Do not edit Custom Workflow plugin files.
- Verification: runner request generation tests, Stage-local Phase runner tests, dry-run no-mutation tests, and optional `pytest -m integration` only in environments with Custom Workflow installed.

Checkpoint 6: Shared projection core (`s27/p06`).

- Introduce `RoadmapProjection` / `wily-roadmap-projection-v1` as a stable internal schema.
- Feed projection from durable v2 state, sessions, live overlays, Custom Workflow status boards, and Board last emit cache.
- Convert `wily status` and `wily watch` consumers to projection semantics.
- Keep Watch terminal-first and Board-independent.
- Verification: projection fixture tests, watch/status render tests for Stage/Phase/checkpoint rows, and `./plugins/wily-roadmap/wily watch --once --ui ascii`.

Checkpoint 7: Checkpoint overlay and Board event contract (`s27/p07`).

- Update `checkpoint-sync` to accept `<stage-id>/<phase-id>` and attach Custom Workflow checkpoint rows as non-durable child rows under the owning Phase.
- Emit signed Board payloads with `(repo, stage_id, phase_id)` identity when local Board config is available.
- Ensure checkpoint overlays never mutate durable Phase status.
- Update Board reflection references.
- Verification: checkpoint parser tests, local live registry tests, Board emit cache tests, and status/watch projection tests.

Checkpoint 8: Wily Board backend alignment (`s27/p08`).

- In `/Users/wilycastle/Code/projects/wily-plugin/wily-board`, update DB/API/live handling for canonical `(repo, stage_id, phase_id)` identity and checkpoint overlays.
- Keep Board read-only for roadmap state.
- Preserve existing visibility/auth rules.
- Verification: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest` or targeted backend tests first, then full backend tests before leaving the checkpoint.

Checkpoint 9: Wily Board IA chrome (`s27/p09`).

- Add `/me` and `/collab` routes, root redirect behavior, shared header/search/surface toggle, side nav or mobile drawer, and visibility-aware repo detail entry.
- Use web-native responsive design; do not copy Watch ASCII rail/glyph visual language.
- Verification: frontend lint/build and route-level smoke/screenshot checks if UI changes are visible.

Checkpoint 10: Wily Board `/me` and `/collab` surfaces (`s27/p10`).

- Implement Active Phase, Next Ready Phase, personal repo grid, blocked/needs_review, Live Activity Strip, shared repo grid, review queue, and next collaboration action widgets.
- Use existing Board data types and APIs where possible.
- Verification: frontend tests where available, API fixture assertions, `npm run lint`, `npm run build`, and screenshots for desktop/mobile if the app can run locally.

Checkpoint 11: Wily Board repo detail refactor (`s27/p11`).

- Update `/repos/[owner]/[name]` to render Stage map, child Phase list, Phase detail, checkpoint overlay rows, live session data, and relevant handoff links.
- Add Phase anchor route support for `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.
- Emphasize owner/freshness for shared repos and progress/next work for personal repos.
- Verification: component/render tests where present, `npm run lint`, `npm run build`, and screenshots for checkpoint row placement.

Checkpoint 12: Skills, commands, docs, and cache sync (`s27/p12`).

- Update Wily command skills and references so every lifecycle command documents `<stage-id>/<phase-id>`.
- Keep marketplace metadata and plugin manifest valid.
- Update README/docs for migration, Phase-only execution, Custom Workflow black-box adapter, Watch/Board projection, and approval-first remote boundaries.
- Verification: `python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py`, docs/reference contract checks, and cache/install comparison if plugin source changes require it.

Checkpoint 13: End-to-end migration and dashboard verification (`s27/p13`).

- Run complete Wily Roadmap verification suite.
- Run complete Wily Board backend and frontend verification.
- Run migration dry-run in both repos.
- Run apply/status/next/run dry-run only against disposable fixture copies first.
- Manually smoke that Stage id execution fails, checkpoint child rows render under owning Phase, `/me` and `/collab` show visibility-appropriate surfaces, and two repo projections remain coherent.
- Do not run production deploy, production live event, remote push, PR, or real repo destructive migration cleanup without explicit user approval.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval during an active `/goal`.
- Local dependency installs required by existing repo tooling may proceed if they do not require payment, secrets, production credentials, or global destructive changes.
- Local disposable fixture migration apply is in scope.
- Real repo migration dry-run is in scope.
- Real repo migration apply requires explicit user approval unless the user has separately authorized it for S27.
- Remote actions remain approval-first: push, PR creation/update, merge, production deploy/restart, production live event emission, GitHub issue mutation, and GitHub comments.
- Destructive actions remain approval-first: deleting `.wily` history, pruning legacy phase folders, overwriting user state, destructive DB migrations, and cleanup that cannot be reversed from the checkpoint's backup.
- Record externally visible or cross-repo actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, production/remote approval gates, impossible file-safety conflicts, repeated verification failure without new evidence, or acceptance criteria that cannot be verified.

## Live Status Board

- File: `agent-handoffs/s27-refactor-status.md`
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
- Used during package creation:
  - `Superpowers:using-superpowers`: loaded as discovery rule.
  - `Superpowers:writing-plans`: loaded for task granularity and implementation-plan discipline; the plan-goal-runner package is saved under `agent-handoffs/` per the requested workflow instead of `docs/superpowers/plans/`.
- Required before implementation:
  - `Superpowers:test-driven-development`: active for parser, migration, lifecycle, runner, projection, Board backend, and Board frontend behavior changes.
  - `Superpowers:systematic-debugging`: active for failing tests, flaky builds, migration surprises, or unexpected runtime behavior.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:using-git-worktrees`: use if either repo's dirty worktree makes safe editing impractical.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: use only for read-only evidence lanes or implementation lanes with explicit disjoint file ownership.
  - `Superpowers:requesting-code-review`: use bounded architecture/integration review before final completion because S27 spans schema, CLI, runner, projection, docs, and Board.
  - `Superpowers:finishing-a-development-branch`: use only after final verification if the user requests commit, PR, merge, or branch cleanup.

## Superpowers Autonomy Override

- Active when native `/goal` is active or autonomous execution was requested.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

Auto-resolution log for this package:

- Auto-resolved under active /goal: writing-plans default save path -> used requested `agent-handoffs/s27-refactor-*.md` package paths.
- Auto-resolved under active /goal: writing-plans execution choice prompt -> root `/goal` runner owns the checkpoint loop; subagents are optional only when lane ownership is safe.
- Auto-resolved under active /goal: plan-goal-runner default external-action YOLO wording -> preserved S27 requirements and repo AGENTS rule that remote/destructive actions remain approval-first.

## Goal Runtime Contract

Progress log:

- `agent-handoffs/s27-refactor-progress.md`

Live status board:

- `agent-handoffs/s27-refactor-status.md`

Verification evidence:

- `agent-handoffs/s27-refactor-verification.md`

Baseline:

- Current Wily Roadmap git status is dirty and must be preserved.
- Current Wily Board git status is dirty and must be inspected again before editing.
- Current S27 durable Stage exists with `execution_mode: "direct"`, `decomposition_status: "none"`, and no child Phases.
- Current Wily implementation still has legacy Phase id paths; `plugins/wily-roadmap/scripts/wily_runner.py` resolves `wily.find_phase(roadmap, phase_id)`.
- Initial package validation command: `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-refactor-execution-package.md`.
- Known broken tests unrelated to this task: none established during package creation.

User / pre-existing changes:

- Pre-existing modified files and untracked directories are listed in `## File / Ownership Boundaries`.
- Must not overwrite user changes.
- If a target file has user changes unrelated to this task, preserve them and continue when possible; stop only if safe editing is impossible.

Pre-existing modified files:

- Wily Roadmap: `.wily/roadmap.yaml`, `.wily/status.md`.
- Wily Board: `app/api/routes.py`, `app/live/events.py`, `app/web/routes.py`, `app/web/static/app.css`, `app/web/templates/_phase_row.html`, `app/web/templates/board.html`, `frontend/app/globals.css`, `frontend/components/desk.tsx`, `frontend/components/phase-list.tsx`, `frontend/components/stage-map.tsx`, `frontend/lib/types.ts`, `tests/test_api_routes.py`, `tests/test_live_events.py`, `tests/test_web_routes.py`.

Pre-existing untracked files:

- Wily Roadmap includes `.playwright-mcp/`, `.wily/revisions/2026-05-17-132403-replan-26.md`, `.wily/revisions/2026-05-17-204434-replan-27.md`, `.wily/revisions/2026-05-17-205537-replan-28.md`, `.wily/stages/s25-wily-board-ui-polish-usability/`, `.wily/stages/s26-wily-roadmap-plugin-improvement-cleanup/`, `.wily/stages/s27-wily-roadmap-large-refactor/`, `agent-handoffs/board-live-local-state-*`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`, `agent-handoffs/s27-refactor-contract-requirements.md`, and `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`.
- Wily Board includes untracked `agent-handoffs/`.

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

- At the end of each execution package checkpoint.
- Before changing durable schema, migration behavior, runner boundaries, projection contracts, or Board identity semantics.
- Before and after cross-repo edits.
- Before any public command contract change.
- After any failed verification retry.

Narrow hard-stop conditions:

- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside the execution package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Payment/purchase action is needed.
- Credential or secret exfiltration risk is discovered.
- Explicit user-forbidden action is needed.
- Production deploy/restart, production secret use, remote push, PR creation/update, merge, GitHub issue mutation, GitHub comments, or production live event is needed.
- Real repo destructive migration cleanup or `--prune-legacy` is needed.
- Existing behavior risk is discovered that is not covered by the plan and cannot be mitigated within scope.
- Tests fail in a way that cannot be attributed to the current change.

Finalization:

1. Run full Wily Roadmap verification commands.
2. Run full Wily Board backend and frontend verification commands.
3. Run disposable fixture migration apply/status/next/run dry-run verification.
4. Use `completion_verifier` or equivalent local final-verification review before any done claim.
5. Use `integration_reviewer` or equivalent local integration review for schema, CLI, runner, Watch, Board, and docs coherence.
6. Update `agent-handoffs/s27-refactor-status.md` to DONE, PARTIAL, or BLOCKED.
7. Produce final summary with diff, tests, risks, remote/destructive approval gates not crossed, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: S27 has a real dependency chain around schema, migration, lifecycle commands, runner adapter, projection, and Board contract. The root `/goal` runner should own integration and state transitions. Limited parallelism is safe for read-only evidence/review lanes throughout, for `s27/p03` and `s27/p04` after `s27/p02` if file ownership is separated carefully, and for `s27/p10` and `s27/p11` after `s27/p09` if frontend component ownership is disjoint. Cross-repo work must be coordinated from the root runner because Wily Board depends on Wily projection and event contracts.

## Lane Handoffs

### Lane A - Wily State And Migration Evidence

Agent: read-only reviewer or implementation worker only after root assigns files.
Mode: read_only_evidence first; implementation_disjoint only for state/migration files.
Timebox: 20-30 minutes for evidence, checkpoint-sized for implementation.
Allowed files:

- `plugins/wily-roadmap/scripts/wily_state_summary.py`
- New state/migration helper modules under `plugins/wily-roadmap/scripts/`
- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- Migration fixtures under `plugins/wily-roadmap/tests/fixtures/`

Must not edit:

- `plugins/wily-roadmap/scripts/wily.py` if Lane B is implementing lifecycle CLI in parallel.
- Wily Board files.

Task: map or implement schema v2 parsing, aggregate status, migration fixtures, and migration validation evidence.
Completion evidence: targeted state summary tests and migration fixture tests.
Dependencies: `s27/p01`; implementation depends on root checkpoint assignment.

### Lane B - Wily CLI Lifecycle And Runner

Agent: implementation worker only if root confirms no Lane A write conflict.
Mode: implementation_disjoint with limits.
Timebox: checkpoint-sized.
Allowed files:

- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_runner.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/skills/wily-run/SKILL.md`

Must not edit:

- Wily Board files.
- Custom Workflow plugin files.

Task: implement Phase-only command resolution, Stage rejection, runner adapter context, dry-run behavior, and checkpoint-sync namespace support.
Completion evidence: targeted CLI/runner tests and dry-run smoke.
Dependencies: `s27/p02`; `s27/p05` depends on `s27/p04`.

### Lane C - Projection, Watch, And Docs

Agent: read-only reviewer or implementation worker.
Mode: implementation_disjoint after runner contract is stable.
Timebox: checkpoint-sized.
Allowed files:

- New projection helper module under `plugins/wily-roadmap/scripts/`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `plugins/wily-roadmap/skills/wily-workflow/references/**`
- README/docs touched by projection contract.

Must not edit:

- Wily Board implementation files unless root converts lane to cross-repo integration.

Task: build and verify shared projection semantics for status/watch/Board emitters and checkpoint overlay rendering.
Completion evidence: projection fixture tests, watch render tests, `wily watch --once --ui ascii`.
Dependencies: `s27/p05` for checkpoint overlay inputs.

### Lane D - Wily Board Backend

Agent: implementation worker in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
Mode: implementation_disjoint after Wily event contract is stable.
Timebox: checkpoint-sized.
Allowed files:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`

Must not edit:

- Frontend IA files if Lane E is active.
- Wily Roadmap files.

Task: align Board storage/API/live events to `(repo, stage_id, phase_id)` and checkpoint overlay read-only semantics.
Completion evidence: targeted Board backend tests and full `uv run pytest`.
Dependencies: `s27/p07`.

### Lane E - Wily Board Frontend

Agent: implementation worker in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
Mode: implementation_disjoint after backend/API types are stable.
Timebox: checkpoint-sized.
Allowed files:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/**`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

Must not edit:

- Board backend files if Lane D is active.
- Wily Roadmap files.

Task: implement `/me`, `/collab`, repo detail Stage/Phase/checkpoint UI, and responsive web-native IA.
Completion evidence: `npm run lint`, `npm run build`, and screenshots when a local dev server can run.
Dependencies: `s27/p08`, `s27/p09`.

### Lane F - Final Integration Review

Agent: review_verification.
Mode: read_only_evidence.
Timebox: 20-30 minutes.
Allowed files:

- All touched files read-only.

Must not edit:

- Any file.

Task: review schema/CLI/runner/projection/Board/docs coherence, final verification evidence, and unapproved remote/destructive boundaries.
Completion evidence: integration review notes in progress and verification logs.
Dependencies: all implementation checkpoints complete.

## Sequential Gates

- Gate 1: Do not implement v2 parser or migration before Checkpoint 1 freezes the contract defaults and fixtures.
- Gate 2: Do not implement migration/lifecycle command behavior before Checkpoint 2 establishes canonical Stage/Phase parser and aggregate rules.
- Gate 3: Do not implement runner adapter changes before Phase-only lifecycle resolution exists.
- Gate 4: Do not update Watch/Board projection before runner/checkpoint overlay inputs are stable.
- Gate 5: Do not update Wily Board backend before Wily Roadmap event/projection contract is stable.
- Gate 6: Do not implement `/me`, `/collab`, or repo detail UI before Board backend/types can represent v2 identity.
- Gate 7: Do not claim S27 complete before two-repo final verification and disposable fixture migration apply evidence pass.
- Gate 8: Do not run remote/destructive/production actions unless the user explicitly approves that specific action.

## Verification Plan

Package-only verification:

```bash
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s27-refactor-execution-package.md
```

Wily Roadmap final verification:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py
# N/A unless this marker selects at least one test; do not report zero selected tests as PASS.
python3 -m pytest -m integration plugins/wily-roadmap/tests/
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Disposable fixture apply verification:

```bash
tmp="$(mktemp -d)"
cp -R plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy "$tmp/project"
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --apply)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily status)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily next)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily run s27/p04 --dry-run)
```

Wily Board final verification:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
cd frontend && npm run lint && npm run build
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

Manual smoke checks:

- Migration transforms synthetic `v1 only`, `mixed legacy`, and `already v2` fixtures as intended.
- Stage id passed to `wily run` fails with namespace guidance.
- `wily run <stage-id>/<phase-id> --dry-run` resolves Stage-local Phase without durable mutation.
- `wily-watch` shows Stage rows, Phase rows, and compact checkpoint child rows from projection.
- Board `/me` and `/collab` render visibility-appropriate surfaces.
- Board repo detail renders checkpoint child rows under the owning Phase.
- Two repos can be displayed from consistent projection semantics.

## Rollback / Stop Conditions

- For local code changes, rollback by reverting only the current checkpoint's own edits; never revert user/pre-existing changes.
- For migration apply tests, use disposable fixture copies by default. If real repo apply is explicitly approved later, verify backup exists under `.wily/backups/<timestamp>-wily-roadmap-v2/` before applying.
- For Wily Board DB/schema changes, ensure tests use local test DBs and no production DB connection.
- Stop if migration would require copying secrets from `.wily/local` or any production config into tracked files.
- Stop if a real repo cleanup requires `--prune-legacy`; ask for explicit approval.
- Stop if Board UI or backend requires production credentials, deployment, or remote live events.
- Stop if marketplace metadata no longer points to `./plugins/wily-roadmap` or the plugin manifest disappears, and fix only if the correction is directly in scope and safe.
- Stop if same verification failure repeats twice without new evidence.
- Stop if implementation would require editing Custom Workflow Skillset internals.

## Reviewer Notes

- Architect: The plan separates durable schema, migration, lifecycle, runner adapter, projection, Board backend, Board frontend, docs, and final E2E so each contract hardens before its consumers change. It keeps Custom Workflow black-box and avoids making Board a source of truth.
- Critic: The biggest risk is breadth. Keep the root `/goal` runner as integrator, use parallel implementation only at declared disjoint points, and do not let UI work start before the identity/event contract is stable.
- Parallel planner: `PARALLEL_SAFE_WITH_LIMITS`; safe windows are `p03 || p04` after parser, and `p10 || p11` after Board IA/types. Read-only reviewer lanes are safe throughout.
- Completion verifier: Before done, require fresh command output in `agent-handoffs/s27-refactor-verification.md`; no stale status-board claims.
- Integration reviewer: Confirm Wily Roadmap and Wily Board agree on canonical identity, checkpoint overlay shape, read-only Board behavior, and migration safety reports.
