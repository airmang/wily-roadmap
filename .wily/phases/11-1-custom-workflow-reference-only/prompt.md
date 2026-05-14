# Execution Prompt

Remove the bundled Custom Workflow runner integration from live Wily behavior and return to reference-only usage.

Scope:

- Preserve completed roadmap history.
- Remove bundled runner assets and tests that require those assets.
- Remove or downgrade `wily-run` behavior that assumes an included Custom Workflow runner.
- Update docs and skills so Custom Workflow is described only as an external workflow Wily can reference.
- Keep Wily local-first and approval-first.
- Do not add MCP servers, hooks, or app integrations.

Stop and ask for direction if removing `wily-run` entirely would be better than converting it to a reference-only handoff command.
