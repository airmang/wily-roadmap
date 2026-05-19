# Execution Package: Batch Migrate Wily State To V2

## Native Goal Command

```text
/goal Complete batch migration of all local Wily-managed repositories under /Users/wilycastle/Code/projects to wily-roadmap-v2 according to agent-handoffs/batch-migrate-wily-v2-execution-package.md.

Maintain agent-handoffs/batch-migrate-wily-v2-progress.md and keep agent-handoffs/batch-migrate-wily-v2-status.md updated as the live status board.

Use /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily for all Wily commands.

Do not run --prune-legacy. Do not push, deploy, create PRs, mutate GitHub, touch production services, reset, checkout, clean, or delete user changes.

For each repository root containing .wily/roadmap.yaml under /Users/wilycastle/Code/projects, excluding nested test data and fixture paths such as `*/tests/fixtures/**`:
1. Record git status --short.
2. Run migrate-state --to wily-roadmap-v2 --dry-run.
3. If dry-run fails, record the error and continue to the next candidate.
4. If dry-run succeeds, run migrate-state --to wily-roadmap-v2 --apply.
5. Run wily status and wily next.
6. Record backup/report paths printed by migration.
7. Run git diff --check.

Done only when every discovered candidate is reported as skipped, dry-run failed, migrated, or already v2, and status, next, and git diff --check evidence is recorded. Do not mark complete if any repo failed migration or verification.
```

## Source Request

Batch migrate local Wily-managed repositories to `wily-roadmap-v2` under `/Users/wilycastle/Code/projects`. Corrected S27 remediation rule: fixture and test-data directories are not local repo candidates even when they contain `.wily/roadmap.yaml`.

## Inline Requirements

Outcome: migrate eligible local Wily state to `wily-roadmap-v2` using the local plugin binary.

In scope: local filesystem candidates only; dry-run before apply; post-apply `status`, `next`, and `git diff --check`.

Non-goals: no `--prune-legacy`, no remote actions, no GitHub mutation, no production service interaction, no destructive git cleanup.

Assumptions: candidate root is the directory that directly contains `.wily/roadmap.yaml` via its `.wily` child directory and is not under a fixture/test-data path. Exclude `*/tests/fixtures/**`, `*/fixtures/**`, `.venv`, `node_modules`, `.git`, and generated dependency/cache directories from "all local repo" discovery.

## Acceptance Criteria

- Every corrected non-fixture candidate under `/Users/wilycastle/Code/projects` is listed in the final output.
- Nested fixture/test-data `.wily/roadmap.yaml` paths are explicitly excluded from candidate processing.
- Each candidate has one of: skipped, dry-run failed, migrated, already v2.
- Migrated candidates include backup/report paths printed by migration.
- `wily status`, `wily next`, and `git diff --check` results are recorded where applicable.
- Final output explicitly states that `--prune-legacy` was not run.
- Work is not marked complete if any migration or verification fails.

## File / Ownership Boundaries

- Expected touchpoints: `.wily/` state in candidate directories; local `agent-handoffs/batch-migrate-wily-v2-*` evidence files.
- Must not edit: remote repositories, GitHub data, production services, non-candidate project files except generated evidence.
- User-owned or pre-existing changes to preserve: all existing dirty worktrees.

## Execution Plan

1. Discover candidates with `.wily/roadmap.yaml`, excluding nested fixture/test-data/cache/dependency directories.
2. Record baseline `git status --short` for each candidate.
3. Run dry-run migration for each candidate.
4. Apply migration only when dry-run succeeds.
5. Run `wily status`, `wily next`, and `git diff --check` after each successful apply.
6. Summarize results and failures without pruning legacy state.

## Autonomous Action Policy

- Local migration commands in the candidate directories are goal-scoped and may proceed.
- Remote actions, GitHub mutation, production service access, destructive git commands, and `--prune-legacy` are explicitly forbidden.
- Stop for a candidate if dry-run fails; continue to the next candidate.

## Live Status Board

- File: `agent-handoffs/batch-migrate-wily-v2-status.md`
- Update cadence: after discovery, after each candidate, after final verification.

## Superpowers Skill Routing

- Available: yes.
- Required before implementation:
  - `Superpowers:test-driven-development`: skipped; this task executes an existing migration command and does not implement behavior changes.
  - `Superpowers:systematic-debugging`: use if migration or verification fails unexpectedly.
- Required before done:
  - `Superpowers:verification-before-completion`.

## Superpowers Autonomy Override

- Active because the migration goal is active in this Codex session.
- Superpowers approval/review/continue prompts are converted into recorded progress checkpoints unless a hard stop condition is reached.
- Active goal auto-resolution log:
  - Auto-resolved under active /goal: `Superpowers:test-driven-development` gate -> skipped because no behavior-changing implementation is planned; this run executes an existing migration command.
  - Auto-resolved under active /goal: `Superpowers:verification-before-completion` gate -> retained as final evidence requirement before any completion claim.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/batch-migrate-wily-v2-progress.md`

Live status board:
- `agent-handoffs/batch-migrate-wily-v2-status.md`

Verification evidence:
- `agent-handoffs/batch-migrate-wily-v2-verification.md`

Baseline:
- Current git status: repository already dirty before this run.
- Initial candidates: populated in progress and verification files.
- Corrected discovery candidates: `agent-handoffs/batch-migrate-wily-v2-corrected-candidates.tsv`.
- Known broken tests unrelated to this task: not evaluated; this task verifies migration commands, `wily status`, `wily next`, and `git diff --check`.

User / pre-existing changes:
- Pre-existing modified files: root marketplace repository had modified `.wily/roadmap.yaml`, `.wily/status.md`, plugin command docs, plugin scripts, skills, references, and tests before this run.
- Pre-existing untracked files: root marketplace repository had `.playwright-mcp/`, several `.wily/revisions/`, `.wily/stages/`, `agent-handoffs/`, docs, projection script, v2 contract reference, and test fixtures before this run.
- Preserve existing dirty worktrees.
- Do not reset, checkout, clean, delete, or prune.
- Must not overwrite user changes; if migration touches files already dirty, record the pre-run status and preserve the worktree.

Checkpoint loop:
1. Choose the next candidate from the discovered list.
2. Record its `git status --short`.
3. Run dry-run migration and record output.
4. Apply only if dry-run succeeds.
5. Run `wily status`, `wily next`, and `git diff --check` after apply.
6. Update status, progress, and verification evidence before moving to the next candidate.

Reviewer gates:
- Package validator must pass before migration loop.
- Final acceptance checklist must be verified before marking the goal complete.
- completion_verifier: final checklist review in this session before completion.
- integration_reviewer: skipped unless multiple independent implementation lanes are introduced; current migration loop is sequential.

## Parallelization Decision

Verdict: SEQUENTIAL_REQUIRED

Reason: each candidate may have dirty local state and migration commands mutate local roadmap files; sequential processing keeps evidence and failures isolated.

## Verification Plan

- For each applied candidate: `wily status`, `wily next`, and `git diff --check`.
- Final evidence review against acceptance criteria.

## Rollback / Stop Conditions

- Do not attempt rollback automatically because existing dirty worktrees must be preserved.
- Stop processing a candidate after dry-run failure.
- Do not mark complete if any candidate migration or verification fails.

## Reviewer Notes

- Architect: user supplied a precise command sequence; no code architecture changes planned.
- Critic: original run incorrectly included non-standalone fixture candidates. S27 remediation corrects the discovery contract to exclude fixture/test-data paths and records the invalidated fixture entries as historical evidence only.
