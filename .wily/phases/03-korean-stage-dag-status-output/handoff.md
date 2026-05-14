# Handoff

Start from `scripts/wily_state_summary.py`.

Useful design decision:
- Use stage/rank layout instead of nested tree layout.
- Keep each stage near the left edge.
- Show multi-dependency phases with `의존: ...`.
- Consider Graphviz/Mermaid export only as a later optional feature.
