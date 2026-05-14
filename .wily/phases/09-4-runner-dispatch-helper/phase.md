# Phase 09-4: Runner dispatch helper 구현

## Purpose

`wily-run`이 phase, runner, autonomy mode를 해석하고 Custom Workflow 실행 패키지를 생성하도록 dispatch helper를 구현한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-bundled-runner-architecture.md`

## Dependencies

- 09-2 Custom Workflow bundled runner 파일 구성
- 09-3 wily-run 명령과 skill 추가

## Expected Output

- `scripts/wily.py run` command or dedicated `scripts/wily_runner.py`
- Runner resolution order: CLI flag, phase metadata, project default, bundled default
- Autonomy resolution order: CLI flag, phase metadata, project default, runner default
- Start or attach a Wily session without marking the phase done
- Generate runner input and Custom Workflow execution package/status/progress/verification files
- Include exact `/goal` command when native goal invocation is unavailable

## Known Risks

- Keep `scripts/wily.py` focused on state transitions if dispatch logic grows.
- Dispatch should stop after preparing runner artifacts unless runtime continuation is explicitly safe.
