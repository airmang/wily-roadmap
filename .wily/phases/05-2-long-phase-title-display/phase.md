# Phase 05-2: 긴 Phase 제목 표시 방식 개선 검토

## Purpose

Phase 제목이 길 때 `...`로 잘리는 현재 표시 방식을 검토하고, 정보를 덜 잃는 표시 전략으로 개선한다.

## Expected Starting Conditions

- Phases 04-1 and 04-2 are done.
- Current status/watch output can already show stage-based roadmap flow.

## Likely Files

- `scripts/wily_state_summary.py`
- `scripts/wily_watch_ui.py`
- `tests/test_wily_state_summary.py`
- `tests/test_wily_watch_ui.py`
- `skills/wily-status/SKILL.md`
- `skills/wily-watch/SKILL.md`

## Completion Criteria

- Long Phase titles are handled with a deliberate strategy instead of losing key context through blunt `...` truncation.
- The selected approach works for terminal width constraints.
- Tests cover long Korean and English titles where practical.
- Status and watch output remain readable and stable.

## Known Risks

- Removing truncation entirely can break compact watch layouts.
- Wrapping, middle truncation, and detail lines each have different tradeoffs; choose based on the actual UI surface.
