# Phase 09-3: wily-run 명령과 skill 추가

## Purpose

Wily phase를 runner로 dispatch하는 사용자-facing command/skill surface를 추가한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-bundled-runner-architecture.md`

## Dependencies

- 09-1 Runner adapter 계약과 Custom Workflow manifest 정의

## Parallel Group

09

## Expected Output

- `skills/wily-run/SKILL.md`
- Claude Code slash command wrapper such as `commands/wily-run.md` if command discovery is in scope.
- Plugin default prompt updates only if useful.
- Command docs for `$wily-run <phase-id> [--runner <id>] [--autonomy ...]`.

## Known Risks

- `wily-run` must not mark phases done.
- Remote or destructive actions remain approval-first.
