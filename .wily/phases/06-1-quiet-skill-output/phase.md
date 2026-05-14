# Phase 06-1: Skill 실행 시 불필요한 출력 줄이기

## Purpose

각 Wily skill이 사용될 때 사용자에게 필요한 결과만 남기고, 반복적이거나 내부 절차에 가까운 출력은 줄인다.

## Expected Starting Conditions

- Phase 05 is done.
- Command skill entrypoints and response-style guidance are stable enough to revise.

## Likely Files

- `skills/wily-*/SKILL.md`
- `skills/wily-workflow/references/`
- `tests/test_wily_command_skills.py`

## Completion Criteria

- 각 command skill의 응답 지침이 짧고 목적 중심으로 정리된다.
- 상태 변경 명령은 결과, 경로, 다음 행동만 보고한다.
- read-only 명령은 핵심 출력만 전달하고 불필요한 절차 설명을 피한다.
- 테스트가 skill 문서의 핵심 응답 계약을 검증한다.

## Known Risks

- 출력을 줄이다가 필요한 안전 경고나 approval-first 안내까지 빠질 수 있다.
- skill 본문에 중복 정책이 쌓이면 유지보수가 어려워진다.
