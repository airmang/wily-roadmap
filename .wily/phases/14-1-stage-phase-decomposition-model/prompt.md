# Execution Prompt

Implement Stage/Phase separation for Wily roadmap planning.

Scope:

- Treat Stage as the top-level roadmap unit created by `$wily-init`.
- Add a new Stage decomposition skill that runs when starting a Stage and breaks that Stage into executable Phase work.
- Preserve compatibility with existing Phase-only roadmaps.
- Update status/watch/next behavior so Stage-only and Stage-with-Phases states remain understandable.
- Add tests for schema parsing, lifecycle transitions, and migration compatibility.
- Do not add hooks, MCP servers, app integrations, or remote actions.

Before editing, confirm the exact skill name and CLI entry point from local conventions, then implement the smallest coherent path.
