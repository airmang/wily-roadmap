# Execution Package: Wily Parent-Owned Coordination Mode

## Native Goal Command

```text
/goal Complete Wily parent-owned coordination mode according to agent-handoffs/wily-parent-coordination-mode-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-parent-coordination-mode-progress.md.

Keep agent-handoffs/wily-parent-coordination-mode-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped local engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Do not stop merely because an action is externally visible if it is goal-scoped and local. Remote actions remain approval-first for this repository: do not push, open PRs, deploy, or publish without explicit user approval. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py; manual fixture smoke for parent-owned non-Git claim/done/cp/status/next/watch; manual fixture smoke for child-only and multi-repo wily land --dry-run.
```

## Source Request / Handoff

User requested, in Korean:

```text
[@custom-workflow-skillset] /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-coordination-project-design-grill.md deep-interview 해서 실행 패키지 만들자
```

Primary design handoff:
- `agent-handoffs/wily-coordination-project-design-grill.md`

Requirements handoff:
- `agent-handoffs/wily-parent-coordination-mode-requirements.md`

## Inline Requirements

Not used as the source of truth. Requirements were separated into `agent-handoffs/wily-parent-coordination-mode-requirements.md`.

## Acceptance Criteria

- In a directory with parent `.wily/tasks.yaml` and `.wily/coordination.yaml`, `wily claim <id>` succeeds even when the parent is not a Git repo.
- Coordination `claim` records `claim_snapshot` containing parent and registered child repo entries, including branch, sha when available, dirty state, changed files, and per-file fingerprints for dirty/untracked files.
- Existing single-repo `claim_sha` behavior remains accepted and serialized for old tasks.
- `wily done <id>` works in coordination mode and reports changed files using `claim_snapshot` where available.
- `wily cp import-status`, `wily status`, `wily next`, and `wily watch` operate against parent tasks in coordination mode.
- Active mode is explicit in text and JSON output for status/workspace-style project views.
- Parent-owned `wily land --dry-run <id>` and `wily land <id>` block clearly when parent-scoped changes exist and the parent is not Git.
- Coordination `wily land --dry-run <id>` and `wily land <id>` block before staging when out-of-scope repo changes are present.
- Child-only `wily land <id>` can commit child repo changes after preflight when parent is not Git; parent Wily ledger changes are reported separately and do not force parent Git by themselves.
- Multi-repo `wily land <id>` creates one local commit per task-scoped touched Git repo and includes `Wily-Task: <id>`.
- Dirty baseline classification reports `pre_existing_dirty`, `task_candidate_changes`, and `mixed_files`.
- Dirty baseline classification uses claim-time per-file fingerprints to distinguish unchanged claim-time dirty files from claim-time dirty files modified again after claim.
- Mixed files block by default and can only be included through explicit `--include-mixed` or `--include <repo:path>` behavior.
- `--push` is rejected in coordination mode and remains legacy single-repo behavior only.
- Commands run inside a registered child repo with its own `.wily/` use the child-local Wily project, not the parent coordination project.
- Existing manifest-only `wily workspace` behavior remains unchanged and still does not create parent `.wily/`.
- Existing single-repo Wily v3 lifecycle behavior remains compatible.
- Docs, skills, README, and surface tests describe coordination mode, manifest-only mode, mode precedence, `claim_snapshot`, and land preflight safety.

## File / Ownership Boundaries

Expected touchpoints:
- `plugins/wily-roadmap/scripts/wily/coordination.py`
- `plugins/wily-roadmap/scripts/wily/scope.py`
- `plugins/wily-roadmap/scripts/wily/models.py`
- `plugins/wily-roadmap/scripts/wily/config.py`
- `plugins/wily-roadmap/scripts/wily/observation.py`
- `plugins/wily-roadmap/scripts/wily/transitions.py`
- `plugins/wily-roadmap/scripts/wily/cli/claim.py`
- `plugins/wily-roadmap/scripts/wily/cli/done.py`
- `plugins/wily-roadmap/scripts/wily/cli/cp.py`
- `plugins/wily-roadmap/scripts/wily/cli/land.py`
- `plugins/wily-roadmap/scripts/wily/cli/status.py`
- `plugins/wily-roadmap/scripts/wily/cli/next.py`
- `plugins/wily-roadmap/scripts/wily/cli/watch.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_activity.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_layout.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `plugins/wily-roadmap/commands/claim.md`
- `plugins/wily-roadmap/commands/cp.md`
- `plugins/wily-roadmap/commands/done.md`
- `plugins/wily-roadmap/commands/land.md`
- `plugins/wily-roadmap/commands/next.md`
- `plugins/wily-roadmap/commands/status.md`
- `plugins/wily-roadmap/commands/watch.md`
- `plugins/wily-roadmap/commands/workspace.md`
- `plugins/wily-roadmap/skills/wily-claim/SKILL.md`
- `plugins/wily-roadmap/skills/wily-cp/SKILL.md`
- `plugins/wily-roadmap/skills/wily-done/SKILL.md`
- `plugins/wily-roadmap/skills/wily-land/SKILL.md`
- `plugins/wily-roadmap/skills/wily-next/SKILL.md`
- `plugins/wily-roadmap/skills/wily-status/SKILL.md`
- `plugins/wily-roadmap/skills/wily-watch/SKILL.md`
- `plugins/wily-roadmap/skills/wily-workspace/SKILL.md`
- `plugins/wily-roadmap/README.md`

Must not edit:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/**`
- Parent workspace files outside `wily-roadmap` except temporary fixture directories created under system temp paths.
- `.agents/plugins/marketplace.json` unless surface tests reveal a required plugin metadata update.
- Remote/deploy/Azure files.

User-owned or pre-existing changes to preserve:
- Existing modified `.wily/tasks.yaml` and `.wily/tasks/*/progress.jsonl`.
- Existing modified Wily Board docs/handoffs/specs.
- Existing modified `plugins/wily-roadmap/commands/init.md` and `plugins/wily-roadmap/skills/wily-init/SKILL.md`.
- Existing untracked `.wily/tasks/T29/`.
- Existing untracked `agent-handoffs/wily-coordination-project-design-grill.md`.
- Existing untracked `docs/design/shots/`.

## Execution Plan

1. Baseline and red-test map:
   - Record current `git status --short --branch`.
   - Read command/docs style around lifecycle commands.
   - Add failing tests for coordination config discovery, active-mode precedence, repo registry validation, and normalized scope parsing.
   - Targeted verification: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'`.

2. Project context, coordination config, and scope core:
   - Add `wily/coordination.py` with `.wily/coordination.yaml` loading, repo registry, active-mode detection, parent repo id, and non-Git-safe project context helpers.
   - Define `resolve_project_context(start)` before command rewrites. It must expose `active_mode`, parent root, `WilyPaths`, coordination config, repo registry, actor policy, observation policy, and whether the current command is in legacy single-repo mode, manifest-only workspace mode, or parent-owned coordination mode.
   - Coordination v1 commands are supported from the parent coordination root or a non-child descendant that resolves to the parent `.wily/`; commands run inside a registered child repo with its own `.wily/` use that child-local Wily project unless a future explicit parent override is added.
   - Add `wily/scope.py` with a typed `ScopeEntry` internal form, string/structured YAML parsing, plain-path compatibility, warnings for ambiguous coordination scopes, and repo-aware matching.
   - Keep task scope YAML persistence backward-compatible: string entries round-trip as strings, structured `{repo, path}` entries round-trip as structured mappings, and command consumers normalize through `scope.py` instead of raw `fnmatch`.
   - Keep `wily/workspace.py` manifest-only behavior unchanged.
   - Targeted verification: coordination/scope tests plus existing workspace tests, including child-repo invocation precedence.

3. Task model and claim snapshot:
   - Extend `Task` with optional `claim_snapshot` serialization/deserialization and scope typing that can preserve strings and structured mappings.
   - Update transition flow before `claim.py`: either allow `apply_claim(..., sha=None, claim_snapshot=...)` or add `apply_coordination_claim()` so coordination mode does not fake a parent `claim_sha`.
   - Add observation helpers for Git/non-Git repo snapshots: branch, sha, dirty flag, changed files, git availability, and per-file fingerprints for dirty/untracked claim-time files.
   - Refactor `claim` to use `resolve_project_context(start)` when `.wily/coordination.yaml` exists; avoid `head_sha(parent)` when parent is not Git.
   - Preserve single-repo `claim_sha` behavior outside coordination mode.
   - Targeted verification: claim tests for non-Git parent and legacy single-repo claim.

4. Coordination lifecycle commands:
   - Refactor `done` to compare `claim_snapshot` against current repo snapshots in coordination mode, while preserving legacy `claim_sha` diff behavior.
   - Verify `cp import-status`, `status`, `next`, and `watch` resolve parent-owned tasks and expose active mode.
   - Update watch scope-conflict/render helpers to use normalized scope matching where relevant.
   - Targeted verification: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (done or cp or status or next or watch)'`.

5. Land preflight:
   - Add land preflight data model for per-repo changed files, scope match results, parent Git requirement, staged/untracked/dirty classification, pre-existing dirty files, task-candidate files, and mixed files.
   - Use claim-time per-file fingerprints to classify `mixed_files`; a path-only claim snapshot is insufficient.
   - Split `parent_ledger_changes` from `parent_task_artifact_changes`.
   - Parent ledger changes include coordination bookkeeping such as `.wily/tasks.yaml`, `.wily/tasks/<id>/progress.jsonl`, and `.wily/tasks/<id>/result.md`; report them but do not require parent Git for child-only land.
   - Parent task artifacts outside the Wily ledger require parent Git when touched and in scope.
   - Add `wily land --dry-run <id>` JSON/text preflight output.
   - Add `--include-mixed` and `--include <repo:path>` guards.
   - Reject `--push` in coordination mode before staging; preserve legacy single-repo `--push` unless separately deprecated.
   - Ensure preflight blocks before any staging/commit when ambiguity, mixed files, or out-of-scope repo changes exist.
   - Targeted verification: land dry-run/preflight tests, including `done -> child-only land` with parent `.wily` modified and no parent Git.

6. Land commit execution:
   - Commit one repo at a time after preflight passes.
   - Stage only files approved by preflight for that repo.
   - Include `Wily-Task: <id>` trailer in each commit.
   - Do not push.
   - Preserve legacy single-repo `land` behavior, including `--include-ledger-closure`.
   - Targeted verification: child-only and multi-repo fixture tests plus legacy land tests.

7. Docs and skills:
   - Update command docs, skills, README, and surface tests.
   - Document mode precedence:
     - `.wily/coordination.yaml` = parent-owned coordination mode.
     - `wily-workspace.yaml` / `.wily-workspace.yaml` = manifest-only read-only aggregate mode.
   - Document `claim_snapshot`, repo-qualified scope forms, `land --dry-run`, mixed file handling, and local-only land.
   - Targeted verification: `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py`.

8. Regression and manual smoke:
   - Run full v3 tests.
   - Create temporary parent-owned non-Git fixture with two child Git repos.
   - Smoke `claim`, `cp import-status`, `done`, `status --json`, `next`, `watch --json` or `watch --once` depending on command contract.
   - Smoke `land --dry-run` for parent-blocking, child-only, and multi-repo cases.
   - Record evidence in `agent-handoffs/wily-parent-coordination-mode-verification.md`.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Goal-scoped local test fixture commits may proceed when needed to verify `wily land` behavior.
- The implementation must not push, open PRs, deploy, publish, or perform production-affecting actions without explicit user approval.
- Do not auto-run `git init` in a real user workspace; use only temporary test/smoke fixtures.
- Record any externally visible or state-changing local actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, edits outside this package, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/wily-parent-coordination-mode-status.md`
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
  - `Superpowers:test-driven-development` for behavior changes: use red-green-refactor per checkpoint.
  - `Superpowers:systematic-debugging` for failures: use before changing code in response to unexpected test/build/smoke failures.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans` for detailed task decomposition: covered by this execution package; use only if checkpoint granularity proves insufficient.
  - `Superpowers:using-git-worktrees` if the dirty workspace makes safe editing impossible; otherwise preserve user changes in place.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` if lanes are independent; parallel implementation requires disjoint write ownership.
  - `Superpowers:requesting-code-review` before finalization because this touches lifecycle commands, scope semantics, and docs.
  - `Superpowers:finishing-a-development-branch` only if the user later asks to commit/push/PR this branch.

## Superpowers Autonomy Override

- Active when native `/goal` is active or autonomous execution was requested.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-parent-coordination-mode-progress.md`

Live status board:
- `agent-handoffs/wily-parent-coordination-mode-status.md`

Verification evidence:
- `agent-handoffs/wily-parent-coordination-mode-verification.md`

Baseline:
- Current git status:
  - `## main...origin/main`
  - Modified: `.wily/tasks.yaml`
  - Modified: `.wily/tasks/T03/progress.jsonl`
  - Modified: `.wily/tasks/T05/progress.jsonl`
  - Modified: `.wily/tasks/T06/progress.jsonl`
  - Modified: `.wily/tasks/T07/progress.jsonl`
  - Modified: `.wily/tasks/T08/progress.jsonl`
  - Modified: `.wily/tasks/T09/progress.jsonl`
  - Modified: `.wily/tasks/T26/progress.jsonl`
  - Modified: `README.md`
  - Modified: `agent-handoffs/wily-board-1-server-execution-package.md`
  - Modified: `agent-handoffs/wily-board-1-server-status.md`
  - Modified: `agent-handoffs/wily-board-2-agent-execution-package.md`
  - Modified: `agent-handoffs/wily-board-2-agent-status.md`
  - Modified: `agent-handoffs/wily-board-3-ui-execution-package.md`
  - Modified: `agent-handoffs/wily-board-3-ui-status.md`
  - Modified: `docs/design/wily-board-mockup.html`
  - Modified: `docs/superpowers/plans/2026-05-19-wily-board-1-server.md`
  - Modified: `docs/superpowers/specs/2026-05-16-wily-board-live-overlay-design.md`
  - Modified: `docs/superpowers/specs/2026-05-16-wily-board-ui-redesign-design.md`
  - Modified: `docs/superpowers/specs/2026-05-17-s27-refactor-design.md`
  - Modified: `docs/superpowers/specs/2026-05-17-wily-board-live-draft-topology-design.md`
  - Modified: `docs/superpowers/specs/2026-05-19-wily-board-v3-design.md`
  - Modified: `docs/wily-board-plan.md`
  - Modified: `docs/wily-board-ui-spec.md`
  - Modified: `plugins/wily-roadmap/commands/init.md`
  - Modified: `plugins/wily-roadmap/skills/wily-init/SKILL.md`
  - Untracked: `.wily/tasks/T29/`
  - Untracked: `agent-handoffs/wily-coordination-project-design-grill.md`
  - Untracked: `agent-handoffs/wily-parent-coordination-mode-execution-package.md`
  - Untracked: `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - Untracked: `agent-handoffs/wily-parent-coordination-mode-requirements.md`
  - Untracked: `agent-handoffs/wily-parent-coordination-mode-status.md`
  - Untracked: `agent-handoffs/wily-parent-coordination-mode-verification.md`
  - Untracked: `docs/design/shots/`
- Initial failing/passing verification:
  - Not run for implementation; first implementation checkpoint must create red tests.
- Known broken tests unrelated to this task:
  - Unknown at package creation time.

User / pre-existing changes:
- Pre-existing modified files are listed above.
- Pre-existing untracked files are listed above.
- Must not overwrite user changes.
- If a target file has unrelated user changes, preserve them and continue when possible; stop only if safe editing is impossible.

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
- Before public task YAML, CLI JSON, or command surface changes.
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
- Safe editing becomes impossible because of unrelated user changes in the same target files.

Finalization:
1. Run full verification commands.
2. Run Lane E `verification_runner` or perform the same final command-evidence checklist locally if no subagent is available.
3. Run Lane F `completion_verifier` or perform the same acceptance-criteria evidence checklist locally if no subagent is available.
4. Run Lane D `integration_reviewer` because this is multi-component lifecycle work.
5. Update `agent-handoffs/wily-parent-coordination-mode-status.md` to DONE, PARTIAL, or BLOCKED.
6. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: The implementation is cross-cutting and should have a sequential root owner for coordination context, scope semantics, task serialization, observation snapshots, lifecycle command integration, and `land` staging/commit behavior. Parallel review lanes are safe. Parallel implementation is not safe before CP06 except for isolated review work or docs/surface work after behavior and JSON fields stabilize.

Default for long `/goal` work: root `/goal` owns sequential implementation. Use parallel subagents primarily for bounded read-only evidence/review. Parallel implementation requires explicit disjoint file ownership or separate worktrees.

Implementation subagent restriction:
- No implementation subagent may change shared contract modules before CP06:
  - `plugins/wily-roadmap/scripts/wily/coordination.py`
  - `plugins/wily-roadmap/scripts/wily/scope.py`
  - `plugins/wily-roadmap/scripts/wily/models.py`
  - `plugins/wily-roadmap/scripts/wily/config.py`
  - `plugins/wily-roadmap/scripts/wily/observation.py`
- `land` preflight and commit execution must have a single owner through CP05 and CP06.
- A docs/surface implementation lane may be considered after CP06, owning only command docs, skill docs, README, and `test_v3_surface.py`.

## Lane Handoffs

### Lane A - Repo Explorer

Agent: repo_explorer
Mode: read_only_evidence
Timebox: 10-20 minutes
Allowed files: all repo files read-only
Must not edit: all files
Task: Inspect existing Wily lifecycle/workspace/scope/observation code and tests for touchpoints, risks, and verification commands.
Completion evidence: concise repo facts, likely touchpoints, compatibility risks, and material ambiguity.
Dependencies: none.
Status: completed during package creation.

### Lane B1 - Test Contract Reviewer: Coordination Core

Agent: test_engineer
Mode: review_verification
Timebox: 10-20 minutes
Allowed files: read-only `plugins/wily-roadmap/tests/v3/test_v3_core.py`, `plugins/wily-roadmap/tests/v3/test_v3_surface.py`, and new tests after CP02.
Must not edit: all files unless explicitly reassigned in active `/goal`.
Task: Review whether red tests cover parent non-Git claim, coordination scope parsing, land preflight blocks, child-only land, multi-repo land, dirty/mixed classification, and manifest-only regression.
Completion evidence: gaps or approval with file/line references.
Dependencies: after CP02.

### Lane B2 - Test Contract Reviewer: Land Safety

Agent: test_engineer
Mode: review_verification
Timebox: 10-20 minutes
Allowed files: read-only `plugins/wily-roadmap/tests/v3/test_v3_core.py`, `plugins/wily-roadmap/tests/v3/test_v3_surface.py`, and new land tests after CP05.
Must not edit: all files unless explicitly reassigned in active `/goal`.
Task: Review whether land preflight tests cover parent Git blocking, child-only land, multi-repo land, dirty baseline classification, mixed-file blocking, out-of-scope blocking before staging, `--include-mixed`, and explicit `--include <repo:path>`.
Completion evidence: gaps or approval with file/line references.
Dependencies: after CP05.

### Lane C - Docs Surface Reviewer

Agent: integration_reviewer or docs-focused reviewer
Mode: review_verification
Timebox: 10-20 minutes
Allowed files: read-only command docs, skill docs, README, plugin prompt, surface tests.
Must not edit: all files unless explicitly reassigned in active `/goal`.
Task: Check that docs and skills describe active mode, mode precedence, local-only land, `claim_snapshot`, repo-qualified scope, and mixed-file safety without contradicting approval-first remote policy.
Completion evidence: gaps or approval with file/line references.
Dependencies: after CP07.

### Lane D - Final Integration Review

Agent: integration_reviewer
Mode: review_verification
Timebox: 15-30 minutes
Allowed files: read-only full diff and verification evidence.
Must not edit: all files.
Task: Review cross-command compatibility and final verification evidence before DONE.
Completion evidence: final findings, residual risks, and verification gaps.
Dependencies: after CP08.

### Lane E - Verification Runner

Agent: verification_runner
Mode: review_verification
Timebox: 10-20 minutes
Allowed files: read-only repo files and generated verification evidence.
Must not edit: all files except appending command evidence to `agent-handoffs/wily-parent-coordination-mode-verification.md` if explicitly assigned during active `/goal`.
Task: Run or independently confirm final verification commands and manual smoke evidence listed in `## Verification Plan`.
Completion evidence: command list, exit codes, and any residual failures.
Dependencies: after implementation and before final DONE.

### Lane F - Completion Verifier

Agent: completion_verifier
Mode: review_verification
Timebox: 10-20 minutes
Allowed files: read-only full diff, execution package, status board, progress log, and verification evidence.
Must not edit: all files.
Task: Check every acceptance criterion against implementation and recorded evidence; identify missing criteria or unverifiable claims.
Completion evidence: PASS/PARTIAL/BLOCKED recommendation with gaps.
Dependencies: after verification runner and before final integration review.

## Sequential Gates

- Gate 1: Do not implement lifecycle command changes until `resolve_project_context(start)`, coordination config, and scope tests define the contracts.
- Gate 2: Do not implement committing behavior in `land` until dry-run preflight tests pass.
- Gate 3: Do not update docs as final until command behavior and JSON fields are stable.
- Gate 4: Keep CP01 through CP06 under one root implementation owner unless a disjoint docs/test-review lane is explicitly assigned.
- Gate 5: Do not mark DONE until full tests, manual smoke checks, Lane E verification runner, Lane F completion verifier, and Lane D integration reviewer complete.

## Verification Plan

Targeted commands:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Final command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Manual smoke checks:
- Temporary parent-owned non-Git fixture: `claim`, `cp import-status`, `done`, `status --json`, `next`, `watch --json` or `watch --once`.
- Temporary parent-owned fixture with parent-scoped changes and no parent Git: `land --dry-run` blocks with clear parent Git requirement.
- Temporary parent-owned fixture with out-of-scope child repo changes: `land --dry-run` blocks before staging and names the out-of-scope files.
- Temporary parent-owned fixture with child-only changes plus parent `.wily` ledger mutations from claim/done: `land --dry-run` reports parent ledger changes, passes without parent Git, and `land` creates one child commit.
- Temporary parent-owned fixture with two touched child repos and Git parent when needed: `land --dry-run` passes and `land` creates one commit per touched scoped repo.
- Temporary dirty-at-claim fixture: pre-existing, new, and mixed file classifications are visible and mixed files block by default.
- Temporary child-local invocation fixture: running lifecycle/view commands inside a registered child repo with its own `.wily/` resolves to the child-local project, not the parent coordination project.

## Rollback / Stop Conditions

- For code changes, rollback by reverting only files changed by this goal; never revert pre-existing user changes.
- For test fixture commits, use temporary directories only.
- For accidental staging during development, unstage only files staged by this goal after confirming no user staging is present.
- Stop for hard destructive commands, payment/purchase actions, credential/secret risk, explicit user-forbidden actions, or safe-editing conflicts.
- Stop if preserving manifest-only workspace behavior would require breaking parent-owned coordination requirements; ask for a product decision.
- Stop if the same verification failure repeats twice without new evidence.

## Reviewer Notes

- Architect: reviewed and package revised. Key revisions: add shared `resolve_project_context(start)`, require claim-time per-file fingerprints for mixed-file detection, split parent ledger changes from parent task artifacts, normalize scope through typed helpers, update transition sequencing before `claim.py`, define child-repo root discovery as parent-root-only for v1, reject `--push` in coordination mode, and refresh baseline during implementation.
- Parallel planner: `PARALLEL_SAFE_WITH_LIMITS`; recommended keeping CP01-CP06 sequential under root ownership, with parallel lanes limited to read-only review until behavior/JSON contracts are stable. Incorporated.
- Critic: first pass rejected for missing explicit out-of-scope land blocking, child-repo invocation precedence verification, and final review tool definitions. Package revised.
- Completion verifier: pending.
- Integration reviewer: pending.
