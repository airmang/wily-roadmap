# Execution Package: T04 advanced parallel watch model

## Native Goal Command

```text
/goal Complete T04: implement the advanced parallel work model, watch visualization, and Korean UI guidance according to agent-handoffs/t04-parallel-watch-execution-package.md.

First read the execution package. Maintain agent-handoffs/t04-parallel-watch-progress.md.

Keep agent-handoffs/t04-parallel-watch-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward T04 and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Done only when all acceptance criteria are satisfied and final verification passes:
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

## Source Request / Handoff

User requested `$custom-workflow-skillset:plan-goal-runner T04 작업 구현해줘` after claiming T04.

## Inline Requirements

Outcome: Wily watch should show advanced parallel work signals, not just a status list.

In scope:
- Optional task metadata for parallel lane, priority, and actor capacity hint.
- Backward-compatible load/save for existing `tasks.yaml` files.
- Watch grouping that distinguishes parallel-ready tasks, dependency-waiting tasks, scope conflicts, and actor capacity.
- Korean UI guidance in Wily watch skill and command docs.
- Tests for model compatibility, watch rendering, and documentation contract.

Non-goals:
- No remote sync, hooks, MCP servers, or app integrations.
- No destructive migration of existing `.wily/tasks.yaml`.
- No branch push or PR unless separately requested.

Assumptions:
- Existing status and dependency fields remain authoritative.
- Optional fields must be omitted from serialized output when unset to keep older files clean.
- Scope conflict detection can be conservative and path-pattern based.

## Acceptance Criteria

- Task model supports optional parallel metadata.
- Existing task files without new fields still load and save.
- Watch output distinguishes parallel-ready lanes, dependency waiting, scope conflict warnings, and actor capacity.
- Korean UI writing guidance exists in the relevant watch skill or command docs.
- Tests verify schema compatibility, parallel classification/rendering, conflict display, and Korean wording.

## File / Ownership Boundaries

- Expected touchpoints:
  - `plugins/wily-roadmap/scripts/wily/models.py`
  - `plugins/wily-roadmap/scripts/wily/config.py`
  - `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
  - `plugins/wily-roadmap/scripts/wily/ui/watch_activity.py`
  - `plugins/wily-roadmap/skills/wily-watch/SKILL.md`
  - `plugins/wily-roadmap/commands/watch.md`
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Must not edit:
  - plugin hook/MCP/app integration files
  - unrelated generated worktrees under `.claude/`
  - unrelated `agent-handoffs/*` files
- User-owned or pre-existing changes to preserve:
  - prior Korean UI and replan contract edits
  - `.wily/tasks/T03/`
  - existing untracked agent handoffs

## Execution Plan

1. Baseline: record git status and run the current focused test suite.
2. RED: add tests for optional parallel metadata, Korean watch guidance, and watch output with parallel lane/capacity/conflict/dependency signals.
3. GREEN: extend `Task` with optional `parallel_lane`, `priority`, and `capacity_hint`; load/save them only when present.
4. GREEN: add watch classification helpers that infer ready-vs-waiting and scope conflicts from existing fields plus optional metadata.
5. GREEN: render Korean parallel lane and capacity lines in watch output, keeping ASCII and Rich paths compatible.
6. GREEN: update watch activity panel with actor capacity hints.
7. GREEN: add Korean UI guidance to watch skill and command docs.
8. Refactor: keep helpers pure and renderer-local unless model changes require shared code.
9. Final verification: run full focused tests and a one-shot ASCII watch.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- No branch push, PR, merge, remote sync, purchase, credential access, hook addition, MCP server addition, or app integration is in scope.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, impossible file-safety conflict, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/t04-parallel-watch-status.md`
- Intended use: keep this Markdown file open in Codex while the goal runs.
- Update cadence: after each checkpoint and verification command.

## Superpowers Skill Routing

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development`: used; tests first.
  - `Superpowers:systematic-debugging`: use if verification fails unexpectedly.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans`: used through this execution package.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: limited to read-only planning/review evidence.

## Superpowers Autonomy Override

- Active for this user-requested execution.
- Superpowers approval/review/continue prompts are converted into progress/evidence checkpoints.
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/t04-parallel-watch-progress.md`

Live status board:
- `agent-handoffs/t04-parallel-watch-status.md`

Verification evidence:
- `agent-handoffs/t04-parallel-watch-verification.md`

Baseline:
- Current git status: dirty with prior Wily UI/replan work and T04 claim state.
- Initial verification:
  - `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface`
  - `python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii`
- Known broken tests unrelated to this task: none known.

User / pre-existing changes:
- Preserve unrelated `.claude/` and unrelated `agent-handoffs/` files.
- If a target file has prior user changes, preserve and extend them.

Checkpoint loop:
1. Update status board.
2. Make the smallest focused change.
3. Run targeted verification.
4. Append progress and evidence.
5. Continue until DONE, PARTIAL, or BLOCKED.

Narrow hard-stop conditions:
- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside this package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Credential or secret exfiltration risk is discovered.
- Existing behavior risk is discovered that cannot be mitigated within scope.

Finalization:
1. Run final verification commands.
2. Review acceptance criteria against outputs.
3. Update status to DONE, PARTIAL, or BLOCKED.
4. Summarize diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: read-only review/exploration can run in parallel. Implementation should stay sequential because model, renderer, docs, and tests share tight contracts.

## Lane Handoffs

### Lane A - Repo Explorer
Agent: explorer
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: repository read-only
Must not edit: all files
Task: identify existing model/render/test touchpoints and compatibility risks.
Completion evidence: concise fact report.
Dependencies: none.

### Lane B - Architecture / Parallel Planner
Agent: default
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: repository read-only
Must not edit: all files
Task: review proposed model and watch visualization, classify safe parallelization, identify risks.
Completion evidence: concise recommendation report.
Dependencies: none.

## Sequential Gates

- Do not write production implementation until RED tests fail for the new behavior.
- Do not mark T04 done until final verification passes.

## Verification Plan

- Focused model/render/docs tests:
  - `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface`
- CLI smoke:
  - `python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii`

## Rollback / Stop Conditions

- Revert only this task's edits if compatibility breaks cannot be resolved.
- Do not revert pre-existing user changes.

## Reviewer Notes

- Architect: pending.
- Critic: pending.
