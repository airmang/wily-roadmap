# Execution Prompt

Bundle Custom Workflow runner files under `runners/custom-workflow/`.

Scope:
- Keep bundled runner files separate from Wily core.
- Preserve `.codex-plugin/plugin.json`, `skills/`, `.claude-plugin/plugin.json`, and `commands/` compatibility.
- Do not install or activate hooks automatically.
