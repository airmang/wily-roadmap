# Wily Project

Root: /Users/wilycastle/Code/projects/wily-roadmap
Goal: wily roadmap 플러그인을 다듬는 중이야.

Current Baseline:
- Personal Codex plugin for Wily roadmap workflow behavior.
- Plugin discovery is driven by `.codex-plugin/plugin.json` and `skills/`.
- Deterministic local roadmap operations live in `scripts/wily.py`.
- Roadmap summary parsing lives in `scripts/wily_state_summary.py`.
- Tests are standard-library `unittest` under `tests/`.
- Existing design and implementation notes live under `docs/superpowers/`.
- Current worktree has uncommitted Wily skill response-style changes that should be settled before broader polish.

Constraints:
- Keep plugin behavior local-first and approval-first for remote or destructive actions.
- Keep skill bodies concise and move detailed policy into `references/`.
- Put repeated deterministic logic in `scripts/`.
- Do not add hooks, MCP servers, or app integrations without an explicit user request.
- Preserve Codex plugin discovery compatibility.
