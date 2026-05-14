# Planner

Use `superpowers:writing-plans` before implementation.

The implementation plan should start with an inventory of live bundled-runner references:

- `.codex-plugin/plugin.json`
- `README.md`
- `skills/wily-*`
- `commands/wily-*`
- `scripts/wily.py`
- `scripts/wily_runner.py`
- `scripts/wily_watch_ui.py`
- `tests/test_wily_cli.py`
- `tests/test_wily_command_skills.py`
- `tests/test_wily_watch_ui.py`
- `runners/custom-workflow/`

Decide explicitly whether `wily-run` remains as a generic external-runner handoff command or is removed from the user-facing command set.
