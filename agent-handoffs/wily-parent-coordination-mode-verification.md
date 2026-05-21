# Verification Evidence: Wily Parent-Owned Coordination Mode

## Package Creation Verification

Command:

```bash
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/wily-parent-coordination-mode-execution-package.md
```

Result:
- Exit: 0
- Output: `PASS: execution package contract is complete.`

Re-run after architect revisions:
- Exit: 0
- Output: `PASS: execution package contract is complete.`

Re-run after critic first-pass revisions:
- Exit: 0
- Output: `PASS: execution package contract is complete.`

Completed review:
- Parallel planner: `PARALLEL_SAFE_WITH_LIMITS`; package revised to restrict implementation parallelism before CP06 and split test-review passes.
- Plan architect: found shared context, fingerprinting, parent ledger, scope model, transition sequencing, root discovery, `--push`, and stale baseline gaps. Requirements and package revised.
- Plan critic first pass: REJECT; package revised to add out-of-scope land blocking AC/tests, child-local invocation precedence verification, and Lane E/F final review definitions.
- Plan critic second pass: PASS; implementation can proceed.

## Implementation Verification

### CP01 Red Tests

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'
```

Result:
- Exit: 1 (expected RED)
- Selected: 11 tests
- Passed: 7 existing selected tests
- Failed: 4 new CP01 tests
- Failure reason: missing modules `wily.coordination` and `wily.scope`, which are the intended CP02 implementation targets.

### CP02 Coordination Context and Scope Core

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope'
```

Result:
- Exit: 0
- Passed: 11

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope or workspace'
```

Result:
- Exit: 0
- Passed: 18

### CP03 Task Model and Claim Snapshot

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or scope or claim'
```

Initial RED:
- Exit: 1
- Failed: 2 expected CP03 tests
- Reasons: `Task.claim_snapshot` unsupported; non-Git coordination parent claim still called `head_sha(root)`.

GREEN:
- Exit: 0
- Passed: 20

### CP04 Coordination Lifecycle Commands

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (done or cp or status or next or watch)'
```

Initial RED:
- Exit: 1
- Failed: 2 expected CP04 tests
- Reasons: status-style JSON lacked `active_mode`; coordination `done` did not report child dirty files from `claim_snapshot`.

GREEN:
- Exit: 0
- Passed: 2

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
```

Result:
- Exit: 0
- Passed: 67

### CP05 Land Preflight

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and land'
```

Initial RED:
- Exit: 1
- Failed: 6 expected CP05 tests
- Reasons: legacy single-root `land` tried `git status` at the non-Git parent and did not support coordination preflight flags.

GREEN:
- Exit: 0
- Passed: 6

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
```

Result:
- Exit: 0
- Passed: 73

Read-only test-contract review:
- Result: gaps found, not a full approval.
- Follow-up gaps to cover before finalization: `cp import-status`, watch parent-task assertion, CLI child-local precedence, ambiguous plain coordination scope warning/behavior, `done` dirty/mixed fingerprint filtering, and claim branch/sha assertions.

### CP06 Land Commit Execution and Land Safety Follow-Up

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (land or cp or done or next or watch or claim)'
```

Initial RED:
- Exit: 1
- Failed: 2 expected CP06 tests
- Reason: coordination non-dry-run `land` reported commit execution as not implemented.

GREEN:
- Exit: 0
- Passed: 13

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q
```

Result:
- Exit: 0
- Passed: 14

Command:

```bash
python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land
```

Result:
- Exit: 0
- Passed: 14

Land-safety reviewer follow-up:
- Added explicit invalid `--include <repo:path>` coverage.
- Added legacy single-repo successful land coverage with `Wily-Task` trailer.
- Hardened parent artifact globbing for `docs/**`.

### CP07 Docs and Skills

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q
```

Initial RED:
- Exit: 1
- Failed: coordination surface documentation test.

GREEN:
- Exit: 0
- Passed: 24 tests, 43 subtests

### CP08 Manual Smoke

Temporary fixture smoke command:

```bash
python3 - <<'PY'
# Inline temporary fixture smoke harness; see progress log for covered cases.
PY
```

Result:
- Exit: 0
- PASS lifecycle claim/cp/done/status/next/watch
- PASS parent-scoped dry-run blocks without parent git
- PASS out-of-scope dry-run blocks before staging
- PASS child-only dry-run and land commit
- PASS multi-repo dry-run and per-repo commits
- PASS dirty baseline and mixed-file blocking
- PASS child-local invocation precedence

Final command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Result:
- Exit: 0
- Passed: 154

## Parent-Git Safety Follow-Up Verification

Final integration follow-up found two parent-Git safety gaps:
- parent repo `out_of_scope_changes` and `mixed_files` were reported in the
  parent payload but did not block coordination land;
- parent Git snapshots expanded registered nested child repos as parent
  untracked files.

Regressions were added for both cases, then parent blockers and registered
nested-repo exclusions were wired through claim, done, and land.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'parent_git_changes or claim_snapshot_excludes' -q
```

Initial RED:
- Exit: 1
- Failed: 2 expected regressions.
- Reasons: parent out-of-scope changes did not block; parent snapshot included
  `wily-roadmap/README.md` and child `.git` internals.

GREEN:
- Exit: 0
- Output: `2 passed, 136 deselected`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q
```

Result:
- Exit: 0
- Output: `19 passed, 119 deselected`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch' -q
```

Result:
- Exit: 0
- Output: `87 passed, 51 deselected`

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Result:
- Exit: 0
- Output: `162 passed in 11.54s`

Command:

```bash
python3 agent-handoffs/wily-parent-coordination-mode-smoke.py
```

Result:
- Exit: 0
- Output:
  - `PASS lifecycle claim/cp/done/status/next/watch`
  - `PASS parent-scoped dry-run and land block without parent git`
  - `PASS out-of-scope dry-run and land block before staging`
  - `PASS child-only dry-run and land commit`
  - `PASS multi-repo dry-run and per-repo commits`
  - `PASS dirty baseline and mixed-file blocking`
  - `PASS child-local invocation precedence`

Updated final evidence status:
- Required full v3 pytest command: PASS with 162 tests.
- Required manual fixture smoke: PASS with 7 smoke cases.
- Parent-Git out-of-scope safety: PASS via regression.
- Parent snapshot nested child repo exclusion: PASS via regression.

### Post-Review Fix Verification

Integration and completion review found parent-Git coordination land,
structured coordination scope in `done`, and manifest-only lifecycle leakage
gaps. Fixes were added and verified with the following commands.

Commands:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'structured_repo_scope or parent_git_artifacts or manifest_only_parent'
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
python3 - <<'PY'
# Temporary parent-owned coordination fixture smoke harness, including parent-Git land.
PY
```

Result:
- Review regressions: exit 0, 3 passed
- Land selector: exit 0, 17 passed
- Broad lifecycle selector: exit 0, 84 passed
- Full v3 tests: exit 0, 159 passed
- Manual smoke: exit 0, `manual smoke passed`

### CP08 Manual Smoke

Command:

```bash
python3 - <<'PY'
# Temporary parent-owned coordination fixture smoke harness.
PY
```

Initial harness issue:
- Exit: 1
- Reason: the harness expected `wily status --json` to return 1 after the only task was already done; the CLI correctly returned 0 for all-done.

Second harness issue:
- Exit: 1
- Reason: the reused dirty fixture had both `src/app.py` and `src/pre.py` as unchanged pre-existing dirty files; the harness expected only `src/pre.py`.

Final result:
- Exit: 0
- Output: `manual smoke passed`
- Covered: non-Git parent claim/cp import-status/done/status/next/watch, parent Git blocking, out-of-scope blocking before staging, child-only dry-run and commit, multi-repo child commits, dirty/mixed classification, and child-local invocation precedence.

### CP06 Land Commit Execution

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination and (land or cp or done or next or watch or claim)'
```

Initial RED:
- Exit: 1
- Failed: 2 expected CP06 tests
- Reason: coordination non-dry-run `land` returned the placeholder "commit execution is not implemented" failure.

GREEN:
- Exit: 0
- Passed: 13

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
```

Result:
- Exit: 0
- Passed: 78

Land-safety review follow-up:
- Reviewer found stale commit-execution and parent artifact failures plus real gaps for explicit `--include` validation and legacy success coverage.

Commands:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land -q
uv run python -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py -k land
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'
```

Result:
- `pytest -k land`: exit 0, 14 passed
- `uv run python -m unittest ... -k land`: exit 0, 14 passed
- broad lifecycle selector: exit 0, 80 passed

## Final Post-Review Verification

Review follow-up added regressions for parent-Git coordination land,
structured coordination scope through `done`, manifest-only lifecycle
non-capture, coordination `--force` help/docs wording, stronger prompt/docs
surface assertions, and a reproducible smoke harness.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'land_help_distinguishes or coordination_land or coordination_done or lifecycle_commands_do_not_treat_manifest_only' -q
```

Result:
- Exit: 0
- Output: `17 passed, 119 deselected`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q
```

Result:
- Exit: 0
- Output: `24 passed, 43 subtests passed`

Command:

```bash
python3 agent-handoffs/wily-parent-coordination-mode-smoke.py
```

Result:
- Exit: 0
- Output:
  - `PASS lifecycle claim/cp/done/status/next/watch`
  - `PASS parent-scoped dry-run and land block without parent git`
  - `PASS out-of-scope dry-run and land block before staging`
  - `PASS child-only dry-run and land commit`
  - `PASS multi-repo dry-run and per-repo commits`
  - `PASS dirty baseline and mixed-file blocking`
  - `PASS child-local invocation precedence`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Result:
- Exit: 0
- Output: `160 passed in 11.40s`

Final evidence status:
- Required full v3 pytest command: PASS.
- Required manual fixture smoke for parent-owned non-Git claim/done/cp/status/next/watch: PASS via `agent-handoffs/wily-parent-coordination-mode-smoke.py`.
- Required manual fixture smoke for child-only and multi-repo `wily land --dry-run`: PASS via `agent-handoffs/wily-parent-coordination-mode-smoke.py`.
- Additional real non-dry-run blocking and commit cases: PASS via core regressions and smoke harness.

## Final Acceptance Audit

Objective: complete Wily parent-owned coordination mode so a parent `.wily`
ledger can own tasks while registered child Git repos own implementation files,
with repo-qualified scope, `claim_snapshot`, safe local-only multi-repo land,
and no regressions to manifest-only workspace or single-repo behavior.

Audit result: PASS. No acceptance criterion remains missing or weak after the
final full suite and reproducible smoke harness.

| # | Acceptance criterion | Evidence |
| --- | --- | --- |
| 1 | Non-Git parent coordination `claim` succeeds. | `test_coordination_claim_from_non_git_parent_records_claim_snapshot`; smoke `PASS lifecycle claim/cp/done/status/next/watch`. |
| 2 | `claim_snapshot` contains parent and registered child entries with branch, sha, dirty state, changed files, and dirty/untracked fingerprints, while parent snapshots exclude registered nested child repos. | `claim.py` `_claim_snapshot`; `observation.py` `claim_snapshot_for_repos`/`repo_snapshot`; `test_coordination_claim_from_non_git_parent_records_claim_snapshot`; `test_coordination_claim_snapshot_excludes_registered_child_repos_from_parent_git`. |
| 3 | Existing single-repo `claim_sha` serialization remains compatible. | `models.py` preserves `claim_sha`; `transitions.py` `apply_claim`; full v3 suite includes existing claim/lifecycle tests. |
| 4 | Coordination `done` works and reports changed files from `claim_snapshot`. | `done.py` `_coordination_changed_files`; `test_coordination_done_from_non_git_parent_reports_child_changes_from_claim_snapshot`; smoke lifecycle PASS. |
| 5 | `cp import-status`, `status`, `next`, and `watch` operate on parent tasks in coordination mode. | `test_coordination_cp_status_next_and_watch_use_parent_tasks_and_expose_active_mode`; `test_coordination_cp_import_status_uses_parent_task_progress`; smoke lifecycle PASS. |
| 6 | Active mode is explicit in text and JSON status/project views. | `status.py`, `next.py`, `watch --json`; `test_coordination_cp_status_next_and_watch_use_parent_tasks_and_expose_active_mode`. |
| 7 | `land --dry-run` and `land` block parent-scoped changes when parent is not Git. | `test_coordination_land_dry_run_blocks_parent_artifact_when_parent_is_not_git`; `test_coordination_land_blocks_parent_artifact_before_commit_when_parent_is_not_git`; smoke parent-block PASS. |
| 8 | `land --dry-run` and `land` block out-of-scope repo changes before staging, including parent Git changes. | `test_coordination_land_dry_run_blocks_out_of_scope_child_changes_before_staging`; `test_coordination_land_blocks_out_of_scope_child_changes_before_staging`; `test_coordination_land_blocks_out_of_scope_parent_git_changes`; smoke out-of-scope PASS. |
| 9 | Child-only `land` commits child changes when parent is not Git and reports parent ledger changes separately. | `test_coordination_land_dry_run_allows_child_only_changes_with_parent_ledger_reported`; `test_coordination_land_commits_child_only_repo_changes_without_parent_git`; smoke child-only PASS. |
| 10 | Multi-repo `land` creates one local commit per touched repo with `Wily-Task: <id>`. | `test_coordination_land_commits_one_local_commit_per_touched_child_repo`; smoke multi-repo PASS. |
| 11 | Dirty baseline classification reports `pre_existing_dirty`, `task_candidate_changes`, and `mixed_files`. | `land.py` `coordination_preflight`; `test_coordination_land_dry_run_classifies_pre_existing_task_candidate_and_mixed_files`; smoke dirty/mixed PASS. |
| 12 | Dirty baseline uses claim-time fingerprints to distinguish unchanged vs modified dirty files. | `observation.py` fingerprints; `done.py`/`land.py` fingerprint comparisons; `test_coordination_done_filters_unchanged_claim_dirty_files_and_reports_mixed_files`; dirty/mixed land test. |
| 13 | Mixed files block by default and require explicit include. | `test_coordination_land_dry_run_classifies_pre_existing_task_candidate_and_mixed_files`; `test_coordination_land_dry_run_allows_mixed_files_only_with_explicit_include`; `test_coordination_land_dry_run_rejects_invalid_explicit_include`. |
| 14 | `--push` is rejected in coordination mode and legacy push behavior is preserved for single-repo mode. | `test_coordination_land_rejects_push_before_preflight`; legacy single-repo land tests; `land.py` routes push rejection only in coordination mode. |
| 15 | Commands inside registered child repo with its own `.wily/` use child-local project. | `resolve_project_context`; `test_coordination_cli_inside_registered_child_uses_child_local_project`; smoke child-local PASS. |
| 16 | Manifest-only `wily workspace` behavior remains unchanged and does not create parent `.wily/`. | Workspace tests including `test_workspace_cli_init_status_next_show_config_and_watch_once`; `test_lifecycle_commands_do_not_treat_manifest_only_parent_as_wily_project`. |
| 17 | Existing single-repo Wily v3 lifecycle behavior remains compatible. | Full v3 suite PASS; legacy `land` trailer and ledger-closure tests still pass. |
| 18 | Docs, skills, README, plugin prompt, and surface tests describe coordination mode, manifest-only mode, precedence, `claim_snapshot`, and land safety. | `test_coordination_surface_documents_parent_owned_mode`; `test_workspace_surface_documents_manifest_only_contract`; docs/skills/prompt grep evidence. |

Verification gates:
- Execution package validator: PASS.
- CP01 RED verified before implementation.
- CP02 through CP08 targeted commands: PASS as recorded above.
- Required final command: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py` -> 162 passed.
- Required manual smoke command: `python3 agent-handoffs/wily-parent-coordination-mode-smoke.py` -> 7 PASS lines.

### CP07 Docs and Skills

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -k coordination -q
```

Initial RED:
- Exit: 1
- Reason: coordination surface wording was missing from README/docs/skills/plugin prompt.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Result:
- Exit: 0
- Passed: 24

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py
```

Result:
- Exit: 0
- Passed: 154
