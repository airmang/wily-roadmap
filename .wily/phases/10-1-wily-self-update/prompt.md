# Execution Prompt

Implement Wily self-update support from the approved design.

Scope:

- Add `update` support to `scripts/wily.py`.
- Add `$wily-update` skill and command metadata.
- Expose the command in plugin defaults if appropriate.
- Support `--check`, `--migrate`, and `--yes`.
- Keep all remote or file-changing work explicit.
- Update README with zip bootstrap and managed GitHub install instructions.

Do not add background update checks, hooks, MCP servers, app integrations, or global shell changes.
