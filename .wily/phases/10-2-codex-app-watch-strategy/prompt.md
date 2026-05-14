# Execution Prompt

Decide and implement the Codex app strategy for `wily-watch`.

Scope:

- Inspect current watch behavior in `scripts/wily.py` and `scripts/wily_watch_ui.py`.
- Evaluate Codex app constraints for terminal panes and long-running watch output.
- Prefer a minimal app-friendly snapshot mode if continuous panes are brittle.
- Preserve existing tmux, `--here`, `--once`, and UI selection behavior.
- Document the recommended Codex app workflow.

Do not add MCP servers, app integrations, or browser UI unless the user explicitly asks for that layer.
