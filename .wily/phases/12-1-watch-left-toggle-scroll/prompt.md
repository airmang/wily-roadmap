# Execution Prompt

Adjust `$wily-watch` interactive mouse handling so only the left mouse button toggles completed-stage expand/collapse, and add mouse-wheel scrolling when the expanded watch body is taller than the visible pane.

Scope:

- Preserve completed roadmap history.
- Keep the current side-terminal watch strategy.
- Treat SGR mouse button code `0` press as left-click toggle.
- Treat right/middle clicks and release events as no-op for toggling.
- Treat wheel up/down events as scroll actions, not toggle actions.
- Clamp scroll offset to the available rendered body range.
- Reset or clamp scroll offset when the body size changes or done stages are collapsed.
- Keep `--once` non-interactive output deterministic.
- Update tests and `wily-watch` guidance to match the new behavior.

Do not add hooks, MCP servers, app integrations, or remote actions.
