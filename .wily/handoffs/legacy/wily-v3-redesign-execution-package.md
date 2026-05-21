# Execution Package: Wily Roadmap v3 Redesign

## Native Goal Command

```text
/goal Complete the Wily Roadmap v3 rewrite according to agent-handoffs/wily-v3-redesign-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-v3-redesign-progress.md.

Keep agent-handoffs/wily-v3-redesign-status.md updated as the live Codex status board.

Do not broaden scope beyond the package. Continue checkpoint-by-checkpoint without approval prompts for goal-scoped engineering actions. Stop only for hard destructive shell commands, payment or purchase actions, credential or secret exfiltration, explicit user-forbidden actions, edits outside the execution package that cannot be avoided, or repeated verification failure without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes:
python3 -m unittest discover -s plugins/wily-roadmap/tests -v
```

## Source Request / Handoff

- User request: read and execute `docs/superpowers/plans/2026-05-18-wily-roadmap-v3.md`, then repeatedly verify and implement missing work until complete.
- Spec reference: `docs/superpowers/specs/2026-05-18-wily-redesign-design.md`.

## Inline Requirements

- Replace v2 Stage/Phase/Session Wily with v3 Project + flat Task list.
- Implement Python package under `plugins/wily-roadmap/scripts/wily/` and make `scripts/wily.py` a thin shim.
- Implement 10 commands: `init`, `next`, `claim`, `go`, `done`, `block`, `replan`, `land`, `watch`, `status`.
- Replace skills with 10 command skills plus `wily-execute`.
- Remove v2 board code, v2-only commands, v2 skills, and v2 tests.
- Preserve pre-existing user changes:
  - `README.md` added repo-local launcher docs.
  - `plugins/wily-roadmap/tests/test_wily_cli.py` added root launcher tests.
  - untracked root `wily` launcher.
  - untracked `agent-handoffs/p6-bridge-durable-sync-handoff.md`.
- Migrate this repository's `.wily/` state to v3 while preserving legacy state under `.wily/archive/`.

## Acceptance Criteria

- `plugins/wily-roadmap/scripts/wily/` package implements all 10 v3 commands.
- `plugins/wily-roadmap/scripts/wily.py` is a thin shim.
- `plugins/wily-roadmap/skills/` contains exactly 11 v3 skill directories.
- Plugin manifests expose v3 surface only and marketplace still points to `./plugins/wily-roadmap`.
- v2 board code and command surface are absent from plugin runtime code.
- v2 test files tied to removed APIs are gone.
- `.wily/project.md`, `.wily/tasks.yaml`, and `.wily/actors.yaml` exist for this repo; old v2 state is archived.
- Final verification passes.

## File / Ownership Boundaries

- Expected touchpoints: `plugins/wily-roadmap/`, `.agents/plugins/marketplace.json`, `.wily/`, `README.md`, root `wily`, `agent-handoffs/wily-v3-redesign-*`.
- Must not edit: files outside this repository; user environment files such as `~/.codex/hooks.json`.
- User-owned changes to preserve: carry README launcher note into v3 docs; preserve root `wily` launcher by tracking or leaving intact; do not delete unrelated `p6-bridge-durable-sync-handoff.md`.

## Execution Plan

1. Baseline: branch, current status, initial tests.
2. Implement v3 core modules and tests: paths, models, config, transitions, progress, observation.
3. Implement CLI scaffold and commands.
4. Implement init/replan/adopt, watch/status renderer, land.
5. Replace shim, skills, manifests, commands docs.
6. Remove v2 runtime/test surface.
7. Migrate `.wily/` to v3 and update README.
8. Run verification loop: full test suite, grep for removed surface, CLI smoke tests, fix gaps, repeat.

## Autonomous Action Policy

- Goal-scoped local edits, branch creation, test execution, and local commits may proceed.
- Do not push or open PR; the plan explicitly defers push/PR to the user.
- Do not mutate external user config or GitHub Actions outside this repo; only document cleanup.

## Live Status Board

- File: `agent-handoffs/wily-v3-redesign-status.md`

## Superpowers Skill Routing

- Available: yes.
- Used before implementation: `superpowers:subagent-driven-development`, `superpowers:test-driven-development`, `superpowers:using-git-worktrees` guidance.
- Required before done: `superpowers:verification-before-completion`.
- Autonomy override: user explicitly requested continuous execution; approval gates are recorded as progress checkpoints unless a hard-stop condition applies.

## Superpowers Autonomy Override

- Active because the user explicitly requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates for goal-scoped work.
- Convert them into progress/evidence checkpoints and continue unless a narrow hard-stop condition is reached.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- Active goal auto-resolution log starts in `agent-handoffs/wily-v3-redesign-progress.md`.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-v3-redesign-progress.md`

Live status board:
- `agent-handoffs/wily-v3-redesign-status.md`

Verification evidence:
- `agent-handoffs/wily-v3-redesign-verification.md`

Baseline:
- Current branch: `feat/wily-v3-redesign`
- Initial verification: `python3 -m unittest discover -s plugins/wily-roadmap/tests -v` passed 273 tests, 2 skipped before v3 rewrite.
- Pre-existing modified files: `README.md`, `plugins/wily-roadmap/tests/test_wily_cli.py`.
- Pre-existing untracked files: `wily`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`.
- Dirty working tree guard: preserve and incorporate relevant pre-existing changes; do not revert user edits. Root launcher behavior from the dirty v2 test must be carried into v3 tests before deleting the v2 test file.

User / pre-existing changes:
- Pre-existing modified files: `README.md`, `plugins/wily-roadmap/tests/test_wily_cli.py`.
- Pre-existing untracked files: `wily`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`.
- Must not overwrite user changes; incorporate the root launcher docs/tests into v3 output.

Checkpoint loop:
1. Mark checkpoint running in status board.
2. Make focused edits.
3. Run targeted or full verification.
4. Record progress and evidence.
5. Continue until DONE, PARTIAL, or BLOCKED.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS
Reason: implementation touches shared CLI/package files, so root session owns edits. Subagents may run read-only exploration and final review.

## Lane Handoffs

### Lane A - Read-only Requirements Review

Agent: explorer
Mode: read_only_evidence
Allowed files: all repository files
Must not edit: all files
Task: identify acceptance requirements, pitfalls, and final verification gaps.
Completion evidence: concise checklist returned to root session.

## Sequential Gates

- Gate 1: v3 package imports and core unit tests pass.
- Gate 2: all command tests pass.
- Gate 3: skills/manifests expose v3 only.
- Gate 4: `.wily` migration smoke passes.
- Gate 5: final full verification and removed-surface grep pass.

## Reviewer Gates

- Repo explorer: read-only requirements and pitfall checklist.
- Plan architect/critic: root session records architecture and executability decisions in progress log instead of pausing.
- completion_verifier: final grep/test/CLI evidence before DONE.
- integration_reviewer: final pass over multi-component changes after verification loop.

## Verification Plan

- `python3 -m unittest discover -s plugins/wily-roadmap/tests -v`
- `python3 plugins/wily-roadmap/scripts/wily.py status --json`
- `python3 plugins/wily-roadmap/scripts/wily.py watch --once`
- `find plugins/wily-roadmap/skills -mindepth 1 -maxdepth 1 -type d | sort`
- `grep -rE "emit_board_live_event|wily-roadmap-v2|live-worked|board check|decompose-stage|wily run" plugins/wily-roadmap/`

## Rollback / Stop Conditions

- Stop if a required destructive git operation is needed.
- Stop if accepting the plan would require deleting unrelated user data.
- Stop if final verification repeats the same failure twice without new evidence.

## Reviewer Notes

- Architect: module split matches spec and limits monolith risk.
- Critic: live migration of `.wily` is the riskiest file operation; archive first and verify new schema before finalizing.
