# Execution Package: Wily Workspace Manifest Multi-Repo CLI

## Native Goal Command

```text
/goal Complete Wily workspace manifest multi-repo CLI according to agent-handoffs/wily-workspace-manifest-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-workspace-manifest-progress.md.

Keep agent-handoffs/wily-workspace-manifest-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface; python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace status --json; python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace next; python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace watch --once.
```

## Source Request / Handoff

User requested, in Korean:

```text
부모 디렉터리에 두 레포 상태를 동시에 관리하는 상태 파일을 두는 대신,
상태 복제 없는 workspace manifest를 두고, 이 기능을 wily-roadmap plugin에
추가하자. 계획 세우고 실행 패키지 만들어줘.
```

Related design handoff:
- `agent-handoffs/wily-board-agent-visibility-design-grill.md`

Existing workspace facts:
- Parent coordination workspace: `/Users/wilycastle/Code/projects/wily-plugin`
- Child repos:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
- Parent should not become a Wily project source of truth.
- Each child repo keeps its own `.wily/tasks.yaml`.

## Inline Requirements

Outcome:
- Add a `wily workspace` command to the `wily-roadmap` plugin.
- Add parent manifest support via `wily-workspace.yaml` or `.wily-workspace.yaml`.
- Allow users to run workspace status/next/watch from `/Users/wilycastle/Code/projects/wily-plugin`.

In scope:
- Manifest discovery and parsing.
- Aggregated read-only status and next-task views across child repos.
- One-shot and polling workspace watch.
- Manifest initialization helper.
- Command docs, skill docs, README example, and tests.

Non-goals:
- No parent `.wily/`.
- No merged parent `tasks.yaml`.
- No cross-repo claim/go/done state transitions.
- No remote sync, Board server API, Azure deployment, or web UI.
- No mutation of child repo task state beyond normal child repo commands.

Assumptions:
- `wily-board` exists as a sibling repo and already has `.wily/tasks.yaml`.
- Parent manifest should be committed or tracked at the coordination workspace level when the user chooses, but this task only creates/reads it.
- Existing Wily v3 task loaders and scheduling helpers are the right source for child repo state.

## Acceptance Criteria

- `wily workspace init --repo wily-roadmap=./wily-roadmap --repo wily-board=./wily-board --title "Wily Plugin Workspace"` creates a manifest with `schema: wily-workspace-v1`.
- `wily workspace status` from the parent prints both child projects with progress, in-progress tasks, next ready tasks, and blocked tasks.
- `wily workspace status --json` emits a stable JSON payload containing manifest title and per-repo summaries.
- `wily workspace next` aggregates per-repo next tasks without claiming them.
- `wily workspace watch --once` renders a one-shot workspace snapshot.
- `wily workspace watch` redraws when any configured child repo `.wily/.touch` changes.
- Missing or invalid child repos are shown as per-repo errors and do not crash the whole workspace command.
- The implementation does not create parent `.wily/`.
- Existing single-repo `wily status`, `wily next`, and `wily watch` behavior remains unchanged.
- Docs and skill guidance explicitly state that the manifest is not a source of truth.
- Verification passes with the commands listed in `## Verification Plan`.

## File / Ownership Boundaries

Expected touchpoints:
- `plugins/wily-roadmap/scripts/wily/workspace.py`
- `plugins/wily-roadmap/scripts/wily/cli/workspace.py`
- `plugins/wily-roadmap/scripts/wily/cli/_common.py`
- `plugins/wily-roadmap/scripts/wily/cli/__main__.py` only if needed
- `plugins/wily-roadmap/commands/workspace.md`
- `plugins/wily-roadmap/skills/wily-workspace/SKILL.md`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `plugins/wily-roadmap/README.md`
- parent `/Users/wilycastle/Code/projects/wily-plugin/wily-workspace.yaml` for smoke testing only

Must not edit:
- `wily-board` implementation files.
- Azure/deploy files.
- Existing unrelated modified files in `wily-roadmap`.
- Parent `.wily/` must not be created.

User-owned or pre-existing changes to preserve:
- Existing dirty `wily-roadmap` docs/handoffs from Board design work.
- Existing new `wily-board` repo and its `.wily/` state.
- Existing `agent-handoffs/wily-board-agent-visibility-design-grill.md`.

## Execution Plan

1. Baseline and Roadmap alignment:
   - Record git status for `wily-roadmap`, `wily-board`, and parent workspace.
   - If not already present, add or revise a Wily task in `wily-roadmap` for workspace manifest CLI before implementing.
   - Confirm no parent `.wily/` exists.

2. Red tests for manifest discovery:
   - Add tests for `wily-workspace.yaml` and `.wily-workspace.yaml`.
   - Verify tests fail because `wily.workspace` is missing.

3. Manifest model and parser:
   - Implement `workspace.py` dataclasses, discovery, parser, validation, and relative path resolution.
   - Run targeted tests.

4. Red tests for aggregate summaries:
   - Add temporary child repo fixtures with `.wily/tasks.yaml`.
   - Test per-repo progress, next task, blocked task, and invalid repo handling.
   - Verify tests fail before implementation.

5. Aggregate snapshot implementation:
   - Reuse `load_tasks`, `load_actors`, `repo_mode`, `parallel_candidates`, `waiting_candidates`, and `cp_summary`.
   - Keep parent manifest as configuration only.
   - Run targeted tests.

6. Red tests for CLI command:
   - Test unknown command before registering `workspace`.
   - Test expected `status`, `next`, `watch --once`, `show-config`, and `init` behavior.

7. CLI implementation:
   - Add `workspace` to `_common.COMMANDS`.
   - Create `cli/workspace.py`.
   - Implement text and JSON output.
   - Implement exit code behavior.
   - Run targeted CLI tests.

8. Watch implementation:
   - Add watch helper tracking child `.wily/.touch` mtimes.
   - Keep v1 without tmux pane support.
   - Run watch-specific tests.

9. Docs and surface:
   - Add command docs.
   - Add `wily-workspace` skill.
   - Update surface tests and README.
   - Run surface tests.

10. Parent workspace smoke:
   - Create or update `/Users/wilycastle/Code/projects/wily-plugin/wily-workspace.yaml` if needed for smoke.
   - Run workspace commands from the parent.
   - Confirm no parent `.wily/` exists.

11. Final verification:
   - Run full v3 core and surface tests.
   - Run manual parent smoke commands.
   - Update progress, verification, and status handoffs.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Creating/updating the parent `wily-workspace.yaml` is goal-scoped and allowed.
- Do not push, open PRs, deploy, SSH, or perform production-affecting actions unless the user explicitly requests it later.
- Record externally visible actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/wily-workspace-manifest-status.md`
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

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development` for behavior changes: active; implement each behavior with RED/GREEN evidence.
  - `Superpowers:systematic-debugging` for failures: load when a test/build/smoke command fails unexpectedly.
- Required before done:
  - `Superpowers:verification-before-completion`
- Conditional:
  - `Superpowers:writing-plans` for detailed task decomposition: used to shape `docs/superpowers/plans/2026-05-20-wily-workspace-manifest.md`.
  - `Superpowers:using-git-worktrees`: optional; dirty workspace exists, but expected edits are narrow and can preserve user changes in place.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: use only for read-only review or disjoint docs vs code lanes after tests define contracts.
  - `Superpowers:requesting-code-review`: use before finalization if implementation touches both command behavior and docs/surface registration.

## Superpowers Autonomy Override

- Active when native `/goal` is active or autonomous execution was requested.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-workspace-manifest-progress.md`

Live status board:
- `agent-handoffs/wily-workspace-manifest-status.md`

Verification evidence:
- `agent-handoffs/wily-workspace-manifest-verification.md`

Baseline:
- Current git status:
  - `wily-roadmap`: dirty with existing Board design/handoff docs, `.wily/tasks.yaml`, and untracked `agent-handoffs/wily-board-agent-visibility-design-grill.md`.
  - `wily-board`: new sibling repo with untracked `.wily/`, `AGENTS.md`, and `CLAUDE.md`.
  - parent workspace: no parent `.wily/`; no `wily-workspace.yaml` yet unless created during execution.
- Initial failing/passing verification:
  - Not run before implementation; first checkpoint must create RED tests.
- Known broken tests unrelated to this task:
  - Unknown until verification.

User / pre-existing changes:
- Pre-existing modified files:
  - multiple Board design docs and agent handoffs in `wily-roadmap`
  - `.wily/tasks.yaml` from Roadmap restructuring
- Pre-existing untracked files:
  - `agent-handoffs/wily-board-agent-visibility-design-grill.md`
  - new `wily-board` repo files
- Must not overwrite user changes:
  - Preserve all unrelated Board design docs/handoffs.
  - Preserve `wily-board` Roadmap state.
  - Do not create parent `.wily/`.
- If a target file has user changes unrelated to this task, preserve them and continue when possible; stop only if safe editing is impossible.

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
- Before public CLI contract changes.
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
2. Run a `completion_verifier` review pass over acceptance criteria and verification evidence.
3. Run an `integration_reviewer` pass for CLI dispatch, docs/surface registration, and parent smoke behavior.
4. Update `agent-handoffs/wily-workspace-manifest-status.md` to DONE, PARTIAL, or BLOCKED.
5. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: CLI behavior, parser, and tests are tightly coupled, so root should implement the code path sequentially with TDD. Read-only review agents are safe. A docs-only lane can run after the command behavior stabilizes, but final surface tests must be integrated by root.

## Lane Handoffs

### Lane A — Repo Facts

Agent: explorer
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: read `plugins/wily-roadmap/scripts/wily/**`, `plugins/wily-roadmap/tests/v3/**`, `plugins/wily-roadmap/commands/**`, `plugins/wily-roadmap/skills/**`
Must not edit: all files
Task: confirm CLI dispatch, reusable helpers, and test patterns for `wily workspace`.
Completion evidence: concise facts report with file paths and risks.
Dependencies: none.

### Lane B — Final Review

Agent: reviewer/verifier
Mode: review_verification
Timebox: 15 minutes
Allowed files: read final diff and run read-only verification commands
Must not edit: source files
Task: check command contract, no parent `.wily/`, and docs/surface coverage before final.
Completion evidence: review report.
Dependencies: implementation complete.

## Sequential Gates

- Do not implement production code before writing and running failing tests for manifest parsing.
- Do not register `workspace` in `_common.COMMANDS` before CLI tests cover help/surface expectations.
- Do not create or modify parent `.wily/`.
- Do not claim completion until parent workspace smoke verifies `wily-roadmap` and `wily-board` are both visible from `/Users/wilycastle/Code/projects/wily-plugin`.

## Reviewer Gates

- Planning review gate:
  - Confirm the plan preserves child `.wily/` as the only source of truth.
  - Confirm the parent manifest stores only repo list/display metadata.
  - Confirm no scope includes Board server/UI work.
- Pre-implementation review gate:
  - Re-read `_common.COMMANDS`, `status.py`, `next.py`, `watch.py`, and test fixtures before code edits.
  - Record any divergence from this package in the progress log.
- Pre-final review gate:
  - Review final diff for accidental parent `.wily/` creation or child state mutation.
  - Run final verification commands fresh.
  - If possible, use a reviewer/verifier agent for read-only diff and command-contract review.

## Verification Plan

Targeted:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core -k workspace
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_surface
```

Full plugin:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Manual parent smoke:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace status --json
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace next
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace watch --once
test ! -d .wily
```

## Rollback / Stop Conditions

- Roll back by removing the new `workspace` command module, `workspace.py`, docs/skill files, tests, and parent manifest if created.
- Do not delete child repo `.wily/` files.
- Stop if manifest parsing would require parent task state replication.
- Stop if current dirty files conflict with target source files and safe merge is not obvious.

## Reviewer Notes

- Architect: keep source of truth in child repos; parent manifest is configuration only.
- Critic: verify exit codes do not make workspace status unusable in scripts; blocked should dominate ready/in-progress.
