# Execution Prompt

Implement smartphone Codex app support for `$wily-watch`.

Scope:

- Make watch open as a bottom horizontal pane for smartphone/Codex app usage, either through reliable detection or an explicit option with safe defaults.
- Add a width-first compact layout for short horizontal panes.
- Preserve existing desktop side-pane behavior unless the new mode is selected or confidently detected.
- Add tests for dry-run pane commands and render output at mobile-like dimensions.
- Keep the change local-first and avoid hooks, MCP servers, or app integrations.

Pay special attention to text cropping and footer behavior in very short panes.
