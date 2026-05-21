# Progress Log: Wily Parent-Owned Coordination Mode

## 2026-05-21 - Package Creation

- Source design read: `agent-handoffs/wily-coordination-project-design-grill.md`.
- Requirements handoff created: `agent-handoffs/wily-parent-coordination-mode-requirements.md`.
- Execution package created: `agent-handoffs/wily-parent-coordination-mode-execution-package.md`.
- Repo explorer subagent found no existing `coordination.py` or `scope.py`, confirmed single-root assumptions in `claim`, `done`, and `land`, and identified verification commands.
- Superpowers routing recorded in the execution package.
- Execution package validator passed.
- Status board initialized: `agent-handoffs/wily-parent-coordination-mode-status.md`.
- Plan review subagents started:
  - `plan_architect`: architecture fit, sequencing, compatibility.
  - `parallel_planner`: lane safety and parallelization verdict.
- Parallel planner returned `PARALLEL_SAFE_WITH_LIMITS` and recommended keeping CP01-CP06 under one root implementation owner. Execution package revised to make parallel implementation restrictions explicit and split test review into B1/B2.
- Architect review returned eight findings. Execution package and requirements were revised to add a shared `resolve_project_context(start)`, require dirty-file fingerprints for mixed-file detection, separate parent ledger changes from parent artifacts, normalize scope through typed helpers, update transition sequencing before `claim.py`, define v1 coordination root behavior, reject `--push` in coordination mode, and refresh the baseline.
- Execution package validator passed again after architecture revisions.
- Plan critic subagent started.
- Plan critic first pass rejected the package for three missing specifics: out-of-scope land blocking, child-local invocation precedence verification, and final review tooling definitions. Requirements and execution package revised.
- Execution package validator passed after critic revisions.
- Plan critic second pass passed. Implementation can proceed from the execution package.
- Next: start `/goal` with the command in `agent-handoffs/wily-parent-coordination-mode-execution-package.md`.

## Superpowers Auto-Resolution Log

- Auto-resolved under active /goal/package creation: `Superpowers:brainstorming` design approval gate -> accepted the supplied design grill plus explicit user request to create an execution package as sufficient design approval evidence.
- Auto-resolved under active /goal: `Superpowers:executing-plans` branch/worktree review gate -> continuing in the current dirty worktree because the execution package, untracked handoffs, and user-owned baseline all live here; safe editing will be enforced by file scope and status checks.

## 2026-05-21 - Goal Execution Start

- Native goal created: complete parent-owned coordination mode according to `agent-handoffs/wily-parent-coordination-mode-execution-package.md`.
- Package, requirements, status board, verification evidence, and applicable AGENTS guidance read.
- Baseline refreshed with `git status --short --branch`; dirty/untracked state matches the execution package's known pre-existing changes.
- CP01 started. Next action: gather current code/test patterns and add failing tests for coordination config, active mode precedence, child-local precedence, and scope parsing.

## 2026-05-21 - CP01 Baseline and Red Tests

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'`
- Result:
  - Exit 1 as expected for RED.
  - 4 new tests fail with `ModuleNotFoundError` for `wily.coordination` and `wily.scope`.
  - 7 existing selected scope tests pass.
- Subagent evidence:
  - Test-pattern explorer confirmed existing temp workspace, subprocess, direct CLI, workspace, land, and surface-test patterns. No edits.
  - Lifecycle explorer confirmed existing root discovery, serialization, git helper, command entrypoint, and integration seam facts. No edits.
- Status board update:
  - CP01 marked DONE.
  - CP02 marked RUNNING.
- Next step:
  - Implement `wily.coordination` and `wily.scope` to satisfy CP01 contracts.

## 2026-05-21 - CP02 Coordination Context and Scope Core

- Files changed:
  - `plugins/wily-roadmap/scripts/wily/coordination.py`
  - `plugins/wily-roadmap/scripts/wily/scope.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - `agent-handoffs/wily-parent-coordination-mode-verification.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope or workspace'`
- Result:
  - `coordination or scope`: 11 passed.
  - `coordination or scope or workspace`: 18 passed.
- Implementation notes:
  - Added `.wily/coordination.yaml` loader with schema validation, parent repo, child repo registry, duplicate-id checks, and resolved paths.
  - Added `resolve_project_context(start)` returning explicit `active_mode` for `coordination`, `single_repo`, or manifest-only `workspace`.
  - Child-local `.wily/` resolution wins when invoked inside a registered child repository that has its own `.wily/`.
  - Added typed `ScopeEntry` normalization, YAML round-tripping, and repo-aware matching.
- Status board update:
  - CP02 marked DONE.
  - CP03 marked RUNNING.
- Next step:
  - Add red tests for `Task.claim_snapshot`, non-Git coordination `claim`, and legacy `claim_sha` compatibility.

## 2026-05-21 - CP03 Task Model and Claim Snapshot

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/scripts/wily/models.py`
  - `plugins/wily-roadmap/scripts/wily/transitions.py`
  - `plugins/wily-roadmap/scripts/wily/observation.py`
  - `plugins/wily-roadmap/scripts/wily/cli/claim.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - `agent-handoffs/wily-parent-coordination-mode-verification.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope or claim'`
- Result:
  - Initial RED: 2 expected failures (`Task.claim_snapshot` unsupported and `claim` called parent `HEAD` in non-Git parent).
  - GREEN: 20 passed.
- Implementation notes:
  - `Task` now preserves optional `claim_snapshot`; legacy `claim_sha` remains unchanged.
  - `apply_claim` accepts `sha=None` and optional `claim_snapshot`.
  - Added repo snapshot helpers with Git availability, branch, sha, dirty files, and file fingerprints.
  - `claim` uses `resolve_project_context`; coordination claims record `claim_snapshot` and do not synthesize parent `claim_sha`.
- Status board update:
  - CP03 marked DONE.
  - CP04 marked RUNNING.
- Next step:
  - Add and satisfy red tests for coordination `done`, `cp`, `status`, `next`, and `watch`.

## 2026-05-21 - CP04 Coordination Lifecycle Commands

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/scripts/wily/cli/done.py`
  - `plugins/wily-roadmap/scripts/wily/cli/status.py`
  - `plugins/wily-roadmap/scripts/wily/cli/next.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - `agent-handoffs/wily-parent-coordination-mode-verification.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (done or cp or status or next or watch)'`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'`
- Result:
  - Initial RED: 2 expected failures (`status --json` lacked `active_mode`; coordination `done` returned no child changed files).
  - Focused GREEN: 2 passed.
  - Broader lifecycle regression: 67 passed.
- Implementation notes:
  - `status --json` and `watch --json` expose `active_mode`.
  - Coordination `next --json` wraps the selected task with `active_mode`.
  - Coordination `done` compares current repo dirty fingerprints against `claim_snapshot` and reports repo-qualified changed files.
  - Result files now include a changed-file list when changed files are known.
- Status board update:
  - CP04 marked DONE.
  - CP05 marked RUNNING.
- Next step:
  - Add and satisfy land preflight tests for parent Git blocking, out-of-scope blocking, child-only dry-run, mixed-file classification, `--include-mixed`, and explicit `--include`.

## 2026-05-21 - CP05 Land Preflight

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/scripts/wily/cli/land.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - `agent-handoffs/wily-parent-coordination-mode-verification.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and land'`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'`
- Result:
  - Initial RED: 6 expected failures in single-root `land`.
  - Focused GREEN: 6 passed.
  - Broader lifecycle regression: 73 passed.
- Implementation notes:
  - Added coordination-only `land --dry-run` preflight with JSON output.
  - Blocks parent-scoped artifacts when the parent is not Git.
  - Blocks out-of-scope child repo changes before staging.
  - Reports parent Wily ledger changes separately and does not require parent Git for child-only work.
  - Classifies `pre_existing_dirty`, `task_candidate_changes`, `mixed_files`, and explicit mixed-file includes.
  - Rejects `--push` in coordination mode before preflight.
- Subagent evidence:
  - CP01-CP04 test reviewer found coverage gaps for `cp import-status`, watch task assertion, CLI child-local precedence, ambiguous plain coordination scope behavior, dirty/mixed `done` filtering, and child branch/sha claim assertions. These are accepted as follow-up checks inside CP06/CP08 rather than blockers to CP05 preflight.
- Status board update:
  - CP05 marked DONE.
  - CP06 marked RUNNING.
- Next step:
  - Add and satisfy coordination commit execution tests for child-only and multi-repo local commits, then close the recorded test coverage gaps.

## 2026-05-21 - CP06 Land Commit Execution

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/scripts/wily/cli/land.py`
  - `agent-handoffs/wily-parent-coordination-mode-status.md`
  - `agent-handoffs/wily-parent-coordination-mode-progress.md`
  - `agent-handoffs/wily-parent-coordination-mode-verification.md`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (land or cp or done or next or watch or claim)'`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'`
- Result:
  - Initial RED: 2 expected failures for missing coordination commit execution.
  - Focused GREEN: 13 passed.
  - Broader lifecycle regression: 78 passed.
- Implementation notes:
  - Coordination `land` now commits one touched registered child repo at a time after preflight passes.
  - It stages only `task_candidate_changes` approved by preflight.
  - Commit messages reuse the existing Wily trailer format and include `Wily-Task: <id>`.
  - Coordination mode remains local-only and rejects `--push`.
  - Added coverage for reviewer gaps: `cp import-status`, watch parent task payload, child-local CLI precedence, done dirty/mixed filtering, and child branch/sha claim assertions.
- Land-safety reviewer follow-up:
  - Verified stale commit-execution findings were fixed by the CP06 patch.
  - Hardened parent artifact globbing for `docs/**` under `uv run python -m unittest`.
  - Added invalid explicit `--include <repo:path>` coverage.
  - Added legacy single-repo successful `land --no-push` trailer regression.
- Additional commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q`
  - `uv run python -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'`
- Additional result:
  - `pytest -k land`: 14 passed.
  - `uv run python -m unittest ... -k land`: 14 passed.
  - Broader lifecycle regression after follow-up: 80 passed.
- Status board update:
  - CP06 marked DONE.
  - CP07 marked RUNNING.
- Next step:
  - Update docs, skills, README, and surface tests for coordination mode, mode precedence, `claim_snapshot`, repo-qualified scope, dry-run preflight, mixed files, and local-only land.

## 2026-05-21 - CP07 Docs and Skills

- Files changed:
  - `plugins/wily-roadmap/.codex-plugin/plugin.json`
  - `plugins/wily-roadmap/README.md`
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
  - `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q`
- Result:
  - Initial RED: coordination surface documentation test failed.
  - GREEN: 24 passed, 43 subtests passed.
- Implementation notes:
  - Documented parent-owned coordination mode, mode precedence, repo-qualified scope, `claim_snapshot`, `active_mode`, land dry-run, mixed-file handling, local-only land, and `--push` rejection.
- Next step:
  - Run final regression, manual smoke fixtures, and final review lanes.

## 2026-05-21 - CP08 Regression and Manual Smoke

- Commands run:
  - Temporary fixture manual smoke harness.
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Result:
  - Manual smoke passed all required fixture cases:
    - lifecycle claim/cp/done/status/next/watch
    - parent-scoped dry-run blocks without parent Git
    - out-of-scope child changes block before staging
    - child-only dry-run and local land commit
    - multi-repo dry-run and one local commit per touched child repo
    - dirty baseline and mixed-file blocking
    - child-local invocation precedence
  - Final pytest command passed: 154 passed.
- Current git status:
  - Worktree still includes pre-existing unrelated modified/untracked files from the execution package baseline.
  - Goal-scoped files include Wily code, tests, command docs, skills, plugin prompt, and these handoff files.
- Next step:
  - Run documentation, completion, and integration review lanes; perform final completion audit before marking DONE.

## 2026-05-21 - CP07 Docs and Skills

- Files changed:
  - `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - `plugins/wily-roadmap/README.md`
  - `plugins/wily-roadmap/.codex-plugin/plugin.json`
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
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -k coordination -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Result:
  - Initial RED: coordination surface test missing README/docs/skills/prompt wording.
  - Surface GREEN: 24 passed.
  - Full v3 tests: 154 passed.
- Documentation notes:
  - Documented manifest-only mode vs parent-owned coordination mode.
  - Documented `.wily/coordination.yaml` precedence, `claim_snapshot`, repo-qualified scope, `active_mode`, `land --dry-run`, mixed file handling, local-only coordination land, and push rejection.
- Status board update:
  - CP07 marked DONE.
  - CP08 marked RUNNING.
- Next step:
  - Run manual smoke fixtures, final verification, and review lanes.

## 2026-05-21 - CP08 Regression, Manual Smoke, and Reviews

- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'land_help_distinguishes or coordination_land or coordination_done or lifecycle_commands_do_not_treat_manifest_only' -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q`
  - `python3 agent-handoffs/wily-parent-coordination-mode-smoke.py`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Final result:
  - Targeted review regression slice: 17 passed.
  - Surface suite: 24 passed, 43 subtests passed.
  - Reproducible smoke script: 7 PASS lines.
  - Full v3 suite: 160 passed.
- Review findings handled:
  - Documentation reviewer found stale `wily-execute` and weak plugin prompt/surface assertions; docs, prompt, and surface tests were updated.
  - Completion verifier found weak reproducible smoke and direct blocking/text-mode evidence; `agent-handoffs/wily-parent-coordination-mode-smoke.py` and direct regressions were added.
  - Integration reviewer found parent-Git land, structured coordination `done` scope, manifest-only lifecycle leakage, and `--force` wording risks. Parent-Git land, structured scope, manifest-only lifecycle behavior, and `--force` help/docs regressions now pass.
- Current git status:
  - Worktree still includes pre-existing unrelated modified/untracked files from the execution package baseline.
  - Goal-scoped files include Wily code, tests, command docs, skills, plugin prompt, smoke harness, and these handoff files.
- Status board update:
  - CP08 marked DONE.
  - State moved to VERIFYING for final prompt-to-artifact acceptance audit.
- Next step:
  - Complete acceptance audit, then mark the native goal complete only if every acceptance criterion maps to verified evidence.

## 2026-05-21 - Final Acceptance Audit

- Acceptance audit:
  - Objective and 18 acceptance criteria from the execution package were mapped to implementation files, tests, smoke output, and documentation evidence in `agent-handoffs/wily-parent-coordination-mode-verification.md`.
  - No missing or weak acceptance item remained after review follow-up.
- Final commands run:
  - `python3 agent-handoffs/wily-parent-coordination-mode-smoke.py`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Final result:
  - Smoke script: 7 PASS lines.
  - Full v3 suite: 160 passed.
- Status board update:
  - State marked DONE.

## 2026-05-21 - Parent-Git Safety Follow-Up

- Reviewer finding:
  - Parent-Git coordination `land --dry-run --json` reported parent `out_of_scope_changes` and `mixed_files` but did not add parent blockers to `errors`.
  - Parent snapshots expanded nested registered child repos as parent untracked files, including child `.git` internals.
- Files changed:
  - `plugins/wily-roadmap/scripts/wily/coordination.py`
  - `plugins/wily-roadmap/scripts/wily/observation.py`
  - `plugins/wily-roadmap/scripts/wily/cli/claim.py`
  - `plugins/wily-roadmap/scripts/wily/cli/done.py`
  - `plugins/wily-roadmap/scripts/wily/cli/land.py`
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- Implementation notes:
  - Added registered nested repo exclusions for coordination snapshots.
  - Passed parent nested repo exclusions through coordination claim, done, and land paths.
  - Applied the same out-of-scope and mixed-file blockers to the parent repo payload as to child repo payloads.
  - Added regressions for parent-Git out-of-scope blocking and parent claim snapshots excluding registered child repos.
- Commands run:
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'parent_git_changes or claim_snapshot_excludes' -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q`
  - `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch' -q`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - `python3 agent-handoffs/wily-parent-coordination-mode-smoke.py`
- Result:
  - Parent safety regressions: 2 passed.
  - Land selector: 19 passed.
  - Broad lifecycle selector: 87 passed.
  - Full v3 suite: 162 passed.
  - Smoke script: 7 PASS lines.
- Status board update:
  - State moved back to VERIFYING while a narrow parent-Git safety reviewer runs.
