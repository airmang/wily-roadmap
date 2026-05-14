# Execution Prompt

Fix the Wily roadmap parser/serializer data-loss bug for YAML block scalars and block lists.

Scope:

- Reproduce the bug with tests before implementation.
- Support roadmap phase fields written as block scalars such as `summary: >-` or `summary: |`.
- Support block list fields such as:

```yaml
depends_on:
  - phase-00-foundation
```

- Ensure state-changing commands that save `.wily/roadmap.yaml` preserve the semantic values instead of dropping block bodies or inventing bogus phases.
- Keep the plugin local-first and avoid adding a new runtime dependency unless unavoidable.
- Keep existing inline roadmap format compatibility.

Do not add hooks, MCP servers, or app integrations.
