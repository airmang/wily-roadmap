# Execution Prompt

Add interactive stage expand/collapse to `$wily-watch`.

Scope:
- Preserve deterministic `--once` output.
- Add interactive state for stage/done-summary expansion in continuous watch mode.
- Support mouse click toggles where terminal/tmux mouse events are available.
- Add keyboard fallback for the same behavior.
- Restore terminal modes and mouse reporting on exit.
- Update `$wily-watch` guidance and focused tests.
