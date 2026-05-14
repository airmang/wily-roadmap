# Wily Run Command Skill Implementation Plan

## Goal

Add the user-facing `wily-run` command and skill surface so users can request runner dispatch in a consistent Wily style, while leaving actual dispatch implementation to the later runner dispatch phase.

## Scope

1. Skill
   - Create `skills/wily-run/SKILL.md`.
   - Document `$wily-run <phase-id> [--runner <id>] [--autonomy conservative|goal_scoped|yolo]`.
   - State that the command prepares/dispatches a phase to a runner and must not mark the phase `done`.
   - Keep remote/destructive actions approval-first.

2. Claude command wrapper
   - Create `commands/wily-run.md`.
   - Follow existing command wrapper style.
   - Route model behavior to the `wily-run` skill.

3. Plugin prompt surface
   - Add `$wily-run` to `.codex-plugin/plugin.json` default prompts if useful.
   - Avoid changing lower-level dispatch behavior in `scripts/wily.py`.

## Verification

- Add focused command/skill tests.
- Run `python3 -m unittest tests.test_wily_cli`.

## Non-Goals

- Do not implement `scripts/wily.py run`.
- Do not create runner artifacts or sessions here.
- Do not mark phases `done`.
