# Wily Decisions

- Keep Wily state local in `.wily/` and do not commit or push without explicit user approval.
- Use Korean for Wily plugin or skill usage announcements when the user is speaking Korean.
- Render `wily-status` user-facing output in Korean for Korean users.
- Prefer a stage-based DAG summary over recursive tree indentation so long roadmaps do not drift to the right.
- Keep Graphviz/Mermaid export as a future extension, not the default status format.
- Keep machine-facing markers, commands, frontmatter, and helper script output in English unless a file has a clear reason to store Korean user-facing text.
- Treat the existing dirty worktree as baseline context, not as something to revert during roadmap initialization.
