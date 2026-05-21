# Execution Package: S27 Missing-Work Remediation

## Native Goal Command

```text
/goal Complete S27 missing-work remediation according to agent-handoffs/s27-remediation-execution-package.md.

First read the execution package and the prior S27 package at agent-handoffs/s27-refactor-execution-package.md. Maintain agent-handoffs/s27-remediation-progress.md.

Keep agent-handoffs/s27-remediation-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not broaden scope beyond the identified S27 omissions. Preserve existing dirty worktrees and user-authored changes.

Because this /goal is active, continue without asking for approval on goal-scoped local engineering actions. Preserve local-first and approval-first boundaries for remote, production, GitHub, and destructive actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run relevant verification commands,
3. append progress and evidence,
4. continue unless a narrow hard-stop condition is triggered.

Done only when all remediation acceptance criteria are satisfied and final verification passes: Roadmap pytest/unittest targets, Roadmap smoke commands, Board pytest, Board frontend lint/build, Board browser smoke for changed routes, batch migration discovery verification, and final prompt-to-artifact audit.
```

## Source Request / Handoff

User request: `$custom-workflow-skillset:plan-goal-runner 지금 누락된거 전부 다시 구현해줘. 완벽하게 누락된거 없는지 검증해서 최종 완료 처리해라.`

Prior package: `agent-handoffs/s27-refactor-execution-package.md`.

Confirmed omissions from fresh audit:

- Board canonical Phase route `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]` was required but not implemented.
- Wily status/progress still renders superseded future stages as incomplete, so S27 appears incomplete despite `s27/p01` being done.
- `wily-retry`, `wily-run`, and related command/skill docs still expose legacy `<phase-id>` as primary user surface.
- Batch migration discovery included nested fixture repos under `plugins/wily-roadmap/tests/fixtures`.
- Integration verification was reported as a gate even though `pytest -m integration` selects no tests.
- Prior handoff/status evidence overstated completion and needs corrected remediation evidence.

## Inline Requirements

Outcome: close every identified S27 omission with code, tests, documentation, and fresh verification evidence.

In scope:

- Wily Board frontend/API route support and tests for canonical Stage/Phase detail URLs.
- Wily Roadmap status/watch/progress semantics for `superseded` stages as closed/non-blocking.
- Wily Roadmap command and skill docs for canonical `<stage-id>/<phase-id>` Phase refs.
- Batch migration discovery excluding nested fixtures/test data from "all local repo" candidates.
- Handoff/status/verification evidence updates.

Non-goals:

- No production deploy/restart.
- No remote push, PR creation/update, GitHub comments, issue mutation, or merge.
- No real repo `--prune-legacy`.
- No Custom Workflow Skillset plugin edits.
- No unrelated cleanup or broad refactor.

## Acceptance Criteria

- Board has a working frontend route at `/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]`.
- Board API accepts canonical Phase lookup by `{owner, name, stage_id, phase_id}` and tests cover duplicate local Phase ids under different stages.
- Repo detail links/anchors remain tuple-safe and route to the canonical Phase detail path where appropriate.
- `wily status` and `wily watch --once --ui ascii` treat `superseded` stages as closed for progress so S27 does not appear incomplete solely because s25/s26 are superseded.
- `wily_state_summary.py` reports closed totals coherently for v2 roadmaps with superseded stages.
- `wily-retry`, `wily-run`, start/complete/block/release/live commands and command docs use `<stage-id>/<phase-id>` as the primary v2 user-facing form.
- `live-worked` and `live-heartbeat` usage text is v2-compatible and does not imply bare Phase identity for v2.
- Batch migration discovery excludes nested `plugins/wily-roadmap/tests/fixtures/**` candidates.
- Integration verification policy is explicit: no integration tests are currently selected, so this is recorded as "not applicable" rather than "passed".
- Final completion audit maps every prior omission to evidence.

## File / Ownership Boundaries

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`:

- `agent-handoffs/s27-remediation-*.md`
- `agent-handoffs/s27-refactor-*.md` for corrected final evidence only
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/scripts/wily_state_summary.py`
- `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`
- `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- `plugins/wily-roadmap/tests/test_wily_watch_ui.py`
- `plugins/wily-roadmap/tests/test_wily_command_skills.py`
- `plugins/wily-roadmap/skills/**`
- `plugins/wily-roadmap/commands/**`
- batch migration handoff files if generated by prior session
- `.wily/status.md` if needed to reflect actual S27 completion

Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`:

- `app/api/routes.py`
- `tests/test_api_routes.py`
- `frontend/app/repos/[owner]/[name]/**`
- `frontend/components/**`
- `frontend/lib/api.ts`
- `frontend/lib/types.ts`
- frontend tests/build inputs as needed

Must not edit:

- `/Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/**`
- `plugins/wily-roadmap/.codex-plugin/plugin.json` unless validation detects drift
- `.agents/plugins/marketplace.json` unless validation detects drift
- production service files, deploy scripts, or secrets

User/pre-existing changes:

- Worktree is dirty in both Wily Roadmap and Wily Board. Preserve unrelated changes and do not reset/checkout/clean.

Pre-existing modified files:

- Wily Roadmap already has S27/batch migration changes across `.wily/**`, `agent-handoffs/**`, `docs/superpowers/specs/**`, and `plugins/wily-roadmap/**`.
- Wily Board may have independent user changes; re-check with `git status --short` before editing and preserve unrelated changes.
- Any file not touched by this remediation package is user/pre-existing unless created or modified during this remediation run.

## Execution Plan

CP01: Package and baseline audit.

- Create remediation package/status/progress/verification files.
- Record failing evidence for the identified omissions.
- Validate execution package.

CP02: Board canonical Phase route.

- Add TDD coverage for canonical duplicate-safe route/API behavior.
- Implement route and frontend detail surface.
- Verify Board API tests, frontend lint/build, and browser smoke.

CP03: Roadmap closed/progress semantics.

- Add TDD coverage for v2 superseded stages counting as closed while still displayed as superseded.
- Fix status summary/watch progress as needed.
- Update `.wily/status.md` to reflect S27 completion if stale.

CP04: Command/skill v2 docs and usage.

- Add command-skill tests that fail on legacy primary `<phase-id>` surfaces.
- Update retry/run/start/complete/block/release/live docs and usage text.
- Verify command skill tests and CLI usage tests.

CP05: Batch migration discovery and integration policy.

- Add or update tests/evidence so fixture directories are not treated as local repos in batch migration handoff logic.
- Correct handoff evidence to mark `pytest -m integration` as not applicable when zero tests are selected.

CP06: Final verification and completion audit.

- Run full Roadmap verification.
- Run full Board verification.
- Run local browser smoke for changed Board route.
- Run prompt-to-artifact audit against prior S27 and remediation criteria.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Remote actions, production service changes, destructive cleanup, GitHub mutation, and `--prune-legacy` remain approval-gated.

## Live Status Board

- File: `agent-handoffs/s27-remediation-status.md`
- Update cadence: every checkpoint start/finish and verification result.

## Superpowers Skill Routing

- Available: yes.
- Required before implementation: `Superpowers:test-driven-development` for behavior changes.
- Required for failures: `Superpowers:systematic-debugging`.
- Required before done: `Superpowers:verification-before-completion`.
- Superpowers approval/review gates are auto-resolved under active goal with recorded evidence unless a narrow hard-stop condition is reached.

## Superpowers Autonomy Override

Active. User input is required only for hard destructive commands, payment/purchase, credential/secret exposure, explicit user-forbidden action, impossible file-safety conflict, or repeated verification failure without new evidence.

## Active Goal Auto-Resolution Log

- Auto-resolved under active /goal: Superpowers approval/review/continue prompts are converted into recorded progress checkpoints and local verification evidence.
- Auto-resolved under active /goal: plan-goal-runner specialist/subagent review prompts are handled by the root runner sequentially because current session policy permits subagents only when explicitly requested.
- Auto-resolved under active /goal: integration verification gate is evaluated by selected-test count; zero selected tests are recorded as N/A, not PASS.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/s27-remediation-progress.md`

Live status board:
- `agent-handoffs/s27-remediation-status.md`

Verification evidence:
- `agent-handoffs/s27-remediation-verification.md`

Checkpoint loop:
1. Mark checkpoint RUNNING in status.
2. Write failing test/evidence first for behavior changes.
3. Implement focused fix.
4. Run targeted verification.
5. Append progress and verification evidence.
6. Continue until DONE, PARTIAL, or BLOCKED.

Narrow hard-stop conditions:
- Same failure repeats twice without new evidence.
- Required fix needs destructive cleanup or production/remote mutation.
- Safe editing is impossible due user-owned changes.

Finalization:
1. Run full verification commands.
2. Complete prompt-to-artifact audit.
3. Update remediation and prior S27 handoffs with corrected evidence.
4. Mark remediation DONE only when no uncovered requirement remains.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED.

Reason: work spans two dirty repos and touches overlapping status/API/docs/tests. Current session policy does not permit subagents unless explicitly requested; root runner will implement sequentially.

## Lane Handoffs

No parallel lanes.

## Sequential Gates

- CP02 before Board final verification.
- CP03 before final Roadmap status verification.
- CP04 before command skill verification.
- CP05 before final audit.

## Verification Plan

Roadmap:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_watch_ui.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
git diff --check
```

Board:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build
```

Browser smoke:

- Render `/repos/R-W-LAB/wily-roadmap/stages/s15/phases/15-6` or equivalent dev-seeded canonical Phase detail route.

## Rollback / Stop Conditions

- Do not use `git reset`, `git checkout --`, or `git clean`.
- Revert only self-made accidental files/edits using scoped patches.

## Reviewer Notes

- Architect: sequential root runner due overlapping dirty repos.
- Critic: prior completion claim failed because proxy verification did not map every requirement; final audit must be explicit.
- completion_verifier: final DONE requires mapped evidence for each omission plus full Roadmap and Board verification.
- integration_reviewer: integration marker currently selects zero tests, so it must be reported as N/A unless a real integration test is added and selected.
