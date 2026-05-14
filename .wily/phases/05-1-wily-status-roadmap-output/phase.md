# Phase 05-1: wily-status에서 Roadmap 출력 예시 보여주기

## Purpose

`$wily-status`가 현재 로드맵의 흐름을 한 번에 이해할 수 있게 Roadmap 출력 예시를 직접 보여주는 방식으로 개선한다.

## Expected Starting Conditions

- Phases 04-1 and 04-2 are done.
- `scripts/wily.py status` and `scripts/wily_state_summary.py` are stable enough to revise output shape.

## Likely Files

- `scripts/wily.py`
- `scripts/wily_state_summary.py`
- `tests/test_wily_cli.py`
- `tests/test_wily_state_summary.py`
- `skills/wily-status/SKILL.md`

## Completion Criteria

- `$wily-status` output includes a clear Roadmap example or Roadmap-shaped summary once, without noisy duplication.
- The behavior is covered by focused tests.
- Output remains useful in Korean and still keeps helper details deterministic.
- Existing lifecycle and init behavior is preserved.

## Known Risks

- Status output can become too verbose if the Roadmap example duplicates the normal summary.
- Keep the command useful for repeated use, not only as a tutorial.
