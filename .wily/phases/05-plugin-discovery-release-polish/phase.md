# Phase 05: Plugin Discovery and Release Polish

## Purpose

Prepare the plugin for reliable local use after the core skill and CLI polish phases are complete.

## Expected Starting Conditions

- Phases 04-1 and 04-2 are done.
- Command skills and helper scripts are stable.

## Likely Files

- `.codex-plugin/plugin.json`
- `skills/`
- `scripts/`
- `tests/`
- `docs/superpowers/`

## Completion Criteria

- Plugin manifest is valid and accurately describes Wily Roadmap.
- Skill directories remain discoverable by Codex.
- Tests and compile checks pass.
- Documentation reflects the final workflow state.
- Any release, commit, push, or PR action is left for explicit user approval.

## Known Risks

- Packaging polish can drift into remote actions; keep this phase local unless the user asks otherwise.
- Avoid adding plugin layers such as hooks, MCP servers, or apps without explicit direction.
