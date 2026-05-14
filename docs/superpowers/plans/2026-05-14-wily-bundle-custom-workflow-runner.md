# Wily Bundle Custom Workflow Runner Implementation Plan

## Goal

Add a runner-local Custom Workflow bundle skeleton under `runners/custom-workflow/` that matches the manifest and can be validated without installing hooks or changing Wily core dispatch behavior.

## Scope

1. Runner-local skills
   - `skills/deep-interview/SKILL.md`
   - `skills/plan-goal-runner/SKILL.md`
   - `skills/parallel-lane-runner/SKILL.md`
   - Include the execution package template required by the verifier.

2. Runner-local agents
   - Add the TOML agent files named in the architecture spec.
   - Keep each file declarative and small.

3. Runner-local scripts
   - `scripts/status_board.py`
   - `scripts/validate_execution_package.py`
   - `scripts/watch_status.py`
   - Keep scripts deterministic and local-only.

4. Optional hooks
   - Add inert `hooks/hooks.json` documentation metadata only.
   - Do not install or activate hooks automatically.

## Verification

- `python3 -m compileall -q runners/custom-workflow`
- `python3 runners/custom-workflow/scripts/validate_execution_package.py runners/custom-workflow/skills/plan-goal-runner/templates/execution-package.md`

## Non-Goals

- Do not implement `wily-run` dispatch.
- Do not add top-level wrapper skills unless discovery requires them.
- Do not install hooks.
