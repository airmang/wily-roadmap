# Execution Package: T05 custom workflow checkpoint sync

## Native Goal Command

```text
/goal Complete T05: diagnose and fix custom-workflow checkpoint records not appearing in Wily Roadmap/watch according to agent-handoffs/t05-custom-workflow-cp-sync-execution-package.md.

First read the execution package. Maintain agent-handoffs/t05-custom-workflow-cp-sync-progress.md.

Keep agent-handoffs/t05-custom-workflow-cp-sync-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward T05 and its acceptance criteria.

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

User asked why the custom workflow checkpoints used during T04 were not reflected in Roadmap/watch, and asked to compare the just-executed records, find the cause, and fix it.

## Inline Requirements

Outcome: custom-workflow checkpoint progress must be recordable as Wily cp events, so `wily watch` can show them.

In scope:
- Compare T04 `agent-handoffs/t04-parallel-watch-*` records against `.wily/tasks/T04/progress.jsonl` and `result.md`.
- Document the cause in `agent-handoffs/t05-custom-workflow-cp-analysis.md`.
- Add a durable Wily mechanism to record/import checkpoint start/done/note events.
- Update the custom workflow-facing Wily skill contract so future runs use that mechanism.
- Preserve existing `progress.jsonl` format and watch compatibility.

Non-goals:
- No remote service, hook, MCP server, or app integration.
- No rewrite of custom-workflow-skillset internals outside this repository.
- No push/PR unless separately requested.

Assumptions:
- Wily watch reads only `.wily/tasks/<id>/progress.jsonl` through `cp_summary`.
- The T04 custom workflow harness wrote its checkpoint evidence into `agent-handoffs/`, not into Wily progress JSONL.
- A local Wily CLI command is the cleanest boundary for agents and custom workflow instructions.

## Acceptance Criteria

- T04 record comparison and root cause are documented.
- A test reproduces that custom workflow checkpoint material can be converted into Wily cp events.
- Wily provides an explicit checkpoint recording/import path.
- `wily-go` / `wily-execute` guidance instructs custom workflow to use Wily checkpoint recording, not only handoff logs.
- Existing progress files and watch rendering remain backward compatible.
- Final unittest suite and watch smoke pass.

## File / Ownership Boundaries

- Expected touchpoints:
  - `plugins/wily-roadmap/scripts/wily/progress.py`
  - `plugins/wily-roadmap/scripts/wily/cli/cp.py`
  - `plugins/wily-roadmap/scripts/wily/cli/__main__.py`
  - `plugins/wily-roadmap/scripts/wily/cli/go.py`
  - `plugins/wily-roadmap/scripts/wily/cli/done.py`
  - `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
  - `plugins/wily-roadmap/skills/wily-execute/SKILL.md`
  - `plugins/wily-roadmap/skills/wily-go/SKILL.md`
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - `agent-handoffs/t05-custom-workflow-cp-analysis.md`
  - `.wily/tasks/T04/progress.jsonl`
- Must not edit:
  - unrelated `.claude/`
  - unrelated pre-existing `agent-handoffs/*`
  - remote or plugin cache files unless separately requested
- User-owned or pre-existing changes to preserve:
  - T05 claim state in `.wily/tasks.yaml`
  - pre-existing untracked handoffs listed in git status

## Execution Plan

1. Write root-cause analysis from T04 handoffs vs Wily progress files.
2. RED: add tests for a `wily cp` recording path and custom workflow-facing instructions.
3. GREEN: add `wily cp <task-id> <cp-name> <start|done|note> [--note text] [--actor id]` with transition validation and timestamped JSONL events.
4. GREEN: update `wily go` output and `wily-execute` / `wily-go` skills to call `wily cp` for checkpoint start/done instead of asking agents to hand-edit JSONL.
5. Add T04 backfill evidence by converting the T04 handoff checkpoints into `.wily/tasks/T04/progress.jsonl`.
6. Run focused tests and watch smoke.
7. Use review/verification agents for final evidence.
8. Mark T05 done only after verification.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Do not push, open PRs, add hooks, add MCP/app integrations, or edit plugin cache.
- Stop for hard destructive commands, payment/purchase, secret exfiltration risk, explicit user-forbidden action, impossible file safety conflict, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/t05-custom-workflow-cp-sync-status.md`
- Intended use: keep this Markdown file open in Codex while the goal runs.
- Update cadence: after each checkpoint and verification command.

## Superpowers Skill Routing

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development`: used; tests first.
  - `Superpowers:systematic-debugging`: use for failures or unexpected behavior.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans`: folded into this execution package.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: read-only evidence/review only.

## Superpowers Autonomy Override

- Active for this user-requested execution.
- Superpowers review/approval prompts are converted into recorded progress checkpoints.
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/t05-custom-workflow-cp-sync-progress.md`

Live status board:
- `agent-handoffs/t05-custom-workflow-cp-sync-status.md`

Verification evidence:
- `agent-handoffs/t05-custom-workflow-cp-sync-verification.md`

Baseline:
- Current git status: dirty with T05 claim state and pre-existing untracked files.
- Initial verification:
  - `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface` passed 33 tests.
- Known broken tests unrelated to this task: none known.

User / pre-existing changes:
- Preserve unrelated `.claude/` and unrelated pre-existing `agent-handoffs/` files.

Checkpoint loop:
1. Update status board.
2. Make the smallest focused change.
3. Run targeted verification.
4. Append progress and evidence.
5. Continue until DONE, PARTIAL, or BLOCKED.

Narrow hard-stop conditions:
- Acceptance cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside this package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Credential or secret exfiltration risk is discovered.

Finalization:
1. Run final verification commands.
2. Review acceptance criteria against outputs.
3. Update status to DONE, PARTIAL, or BLOCKED.
4. Summarize diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: exploration and review can run in parallel. Implementation should be sequential because CLI, progress file semantics, skill docs, and tests share one behavior contract.

## Lane Handoffs

### Lane A - Repo Explorer
Agent: explorer
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: repository read-only
Must not edit: all files
Task: identify current progress/checkpoint contract and T04 evidence gap.
Completion evidence: concise fact report.
Dependencies: none.

### Lane B - Architecture / Critic
Agent: default
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: repository read-only
Must not edit: all files
Task: review minimal design, risks, and verification plan.
Completion evidence: concise recommendation report.
Dependencies: none.

## Sequential Gates

- Do not write implementation before a failing test for the new cp command/contract.
- Do not mark T05 done until final verification passes and T04 cp backfill is visible to watch/cp summary.

## Verification Plan

- Focused suite:
  - `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface`
- CLI smoke:
  - `python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii`
- Targeted CLI checks:
  - create temp Wily repo, run `wily cp`, inspect `.wily/tasks/<id>/progress.jsonl`, and check `cp_summary`.

## Rollback / Stop Conditions

- Revert only this task's edits if the new cp command cannot preserve compatibility.
- Do not revert pre-existing user changes.

## Reviewer Notes

- Architect: pending.
- Critic: pending.
