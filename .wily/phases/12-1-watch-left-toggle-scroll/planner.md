# Planner

Use `superpowers:systematic-debugging` if existing mouse behavior is unclear, then use `superpowers:test-driven-development` before implementation.

The implementation plan should start by identifying the current contracts for:

- `parse_watch_mouse_event`;
- `watch_action_from_input`;
- `watch_here_interactive`;
- rendered body/chrome row counts in `scripts/wily_watch_ui.py`;
- existing watch tests that assume any mouse press toggles.

Prefer a small state model for interactive watch input: toggle, refresh, quit, scroll up, scroll down, or no-op.
