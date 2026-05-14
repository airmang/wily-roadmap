# Wily Runner Dispatch Helper Implementation Plan

## Goal

Implement `wily run` / `$wily-run` dispatch so Wily can prepare a selected phase for the bundled Custom Workflow runner without marking the phase done.

## Scope

1. Add `scripts/wily_runner.py`
   - Validate the phase exists.
   - Allow dispatch for ready/pending-with-done-dependencies phases, or attach to an existing `in_progress` phase session.
   - Resolve runner by CLI flag, phase metadata, project config, then bundled manifest default.
   - Resolve autonomy by CLI flag, phase metadata, project config, then runner manifest default.
   - Start a Wily session when needed by reusing existing `wily.py` lifecycle behavior.
   - Build runner-native handoff files under `agent-handoffs/`.
   - Build session archive files under `.wily/sessions/<session>/runner/`.
   - Include an exact `/goal` command for runtimes that cannot set goals directly.

2. Add `wily.py run`
   - Keep `scripts/wily.py` thin.
   - Delegate dispatch to `scripts/wily_runner.py`.

3. Update `wily-run` guidance
   - Document the internal command.
   - Remove the old "dispatch not implemented" boundary.
   - Keep completion separate from dispatch.

4. Tests
   - Verify dispatch starts a phase, creates runner artifacts, and does not mark it done.
   - Verify CLI runner/autonomy override behavior.
   - Verify non-executable phases fail.

## Non-Goals

- Do not execute the runner after dispatch.
- Do not mark a phase `done`.
- Do not implement artifact finalization; that belongs to 09-5.
