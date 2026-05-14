# Phase 08-1: Watch pane Stage별 접기 펼치기 인터랙션

## Purpose

`$wily-watch` pane에서 완료된 stage summary나 stage header를 마우스 클릭 또는 키보드로 접었다 펼칠 수 있게 한다.

## Dependencies

- 06-5 긴 로드맵 Pane에서 완료 Stage 접기 전략

## Parallel Group

08

## Expected Starting Conditions

- Watch pane already collapses leading completed stages when height is constrained.
- `$wily-watch` opens a tmux pane by default and supports `--here`, `--once`, `--ui`, and `--interval`.
- Current renderer is deterministic for non-interactive tests.

## Expected Output

- Interactive watch mode supports stage expand/collapse.
- Mouse click on a folded done summary or stage row toggles that stage group when terminal/tmux mouse events are available.
- Keyboard fallback exists, at minimum `d` for done-stage expand/collapse and `q` to quit.
- Footer tells the user the available interaction: click or key toggle, refresh, quit.
- `--once` remains deterministic and non-interactive.
- Tests cover input parsing/state transitions without requiring real mouse hardware.

## Likely Files

- `scripts/wily.py`
- `scripts/wily_watch_ui.py`
- `tests/test_wily_cli.py`
- `tests/test_wily_watch_ui.py`
- `skills/wily-watch/SKILL.md`

## Known Risks

- Terminal mouse reporting differs by terminal/tmux settings.
- Raw terminal mode must be restored on exit.
- Mouse support should not make `$wily-watch --once` flaky.
- If click support is unavailable, keyboard fallback must still work.
