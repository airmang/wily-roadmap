# Phase 09-2: Custom Workflow bundled runner 파일 구성

## Purpose

Custom Workflow runner assets를 `runners/custom-workflow/` 아래에 bundled runner로 배치한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-bundled-runner-architecture.md`

## Dependencies

- 09-1 Runner adapter 계약과 Custom Workflow manifest 정의

## Parallel Group

09

## Expected Output

- `runners/custom-workflow/skills/*`
- `runners/custom-workflow/agents/*.toml`
- `runners/custom-workflow/scripts/status_board.py`
- `runners/custom-workflow/scripts/validate_execution_package.py`
- `runners/custom-workflow/scripts/watch_status.py`
- optional `runners/custom-workflow/hooks/hooks.json`
- Top-level skill wrappers only if Codex discovery requires them.

## Known Risks

- Do not auto-install hooks globally.
- Keep runner-local files canonical unless a later decision changes that.
