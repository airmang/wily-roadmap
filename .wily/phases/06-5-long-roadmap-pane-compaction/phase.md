# Phase 06-5: 긴 로드맵 Pane에서 완료 Stage 접기 전략

## Purpose

로드맵이 길어져 watch pane 범위에서 잘릴 때 이미 처리된 Stage들을 어떻게 접고 보여줄지 정한다.

## Expected Starting Conditions

- Phase 05 is done.
- Watch pane already renders stage-based roadmap flow and can collapse leading done phases.

## Likely Files

- `scripts/wily_watch_ui.py`
- `tests/test_wily_watch_ui.py`
- `skills/wily-watch/SKILL.md`

## Completion Criteria

- 완료된 Stage를 접는 기준이 명확하다.
- 현재/ready/blocked/unfinished 단계는 pane 높이가 작아도 우선적으로 남는다.
- 접힌 Stage 개수와 의미가 사용자에게 분명히 표시된다.
- 긴 로드맵 fixture 테스트가 height constraints를 검증한다.

## Known Risks

- 너무 공격적으로 접으면 진행 맥락을 잃는다.
- 너무 보수적으로 접으면 중요한 현재 단계가 잘릴 수 있다.
