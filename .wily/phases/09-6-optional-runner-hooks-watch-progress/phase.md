# Phase 09-6: Optional runner hooks와 watch progress 후속 통합

## Purpose

Bundled runner v1 이후, opt-in hooks와 `wily-watch` runner progress 표시를 검토하고 구현한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-bundled-runner-architecture.md`

## Dependencies

- 09-5 Runner artifact archive와 review handoff 연결

## Expected Output

- Hooks remain opt-in and respect Wily autonomy mode.
- PostToolUse evidence capture can update runner verification artifacts when enabled.
- Stop continuation guard can understand Wily phase status and autonomy mode when enabled.
- `wily-watch` can show runner progress from status artifacts if this remains useful.

## Known Risks

- Hooks, MCP servers, and app integrations must not become required for core Wily behavior.
- This is explicitly not part of first bundled runner implementation.
