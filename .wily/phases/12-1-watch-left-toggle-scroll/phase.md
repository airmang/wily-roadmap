# Phase 12-1: Watch pane 왼쪽 버튼 토글과 펼친 상태 스크롤 보정

## Purpose

`$wily-watch` interactive pane에서 접기/펼치기 입력을 왼쪽 마우스 버튼으로만 처리하고, 완료 stage를 펼친 뒤에는 마우스 휠로 본문을 위아래로 스크롤할 수 있게 한다.

## Dependencies

- 10-2 Codex app 환경의 wily-watch 전략 확정
- 11-1 Custom Workflow bundled runner 제거와 참조 전용 회귀

## Expected Output

- 접힌 완료 stage summary나 stage row를 왼쪽 마우스 버튼으로 클릭할 때만 접기/펼치기가 토글된다.
- 오른쪽 버튼, 가운데 버튼, 마우스 버튼 release 이벤트는 접기/펼치기를 토글하지 않는다.
- 마우스 휠 이벤트는 접기/펼치기 토글로 해석하지 않는다.
- 완료 stage가 펼쳐진 상태에서 본문이 화면 높이를 넘으면 마우스 휠로 위아래 스크롤할 수 있다.
- 스크롤 위치는 본문 길이와 화면 높이에 맞춰 clamp되고, 접힌 상태로 돌아갈 때는 필요 없는 스크롤 위치가 남지 않는다.
- `d`, `r`, `q` 키보드 fallback과 `--once` deterministic output은 유지한다.
- footer나 skill 안내는 실제 동작과 맞게 갱신한다.
- 테스트는 SGR mouse button code를 기준으로 왼쪽 클릭, 오른쪽 클릭, 휠 업/다운, 스크롤 clamp를 검증한다.

## Likely Files

- `scripts/wily.py`
- `scripts/wily_watch_ui.py`
- `tests/test_wily_cli.py`
- `tests/test_wily_watch_ui.py`
- `skills/wily-watch/SKILL.md`

## Known Risks

- 현재 mouse parser가 button code를 버리면 오른쪽 클릭과 휠 입력을 구분할 수 없다.
- Rich/ascii 렌더러의 chrome row 계산이 맞지 않으면 스크롤 가능한 줄 수가 흔들릴 수 있다.
- tmux나 터미널에 따라 휠 이벤트 code가 다를 수 있으므로 일반 SGR 1006 기준을 우선하고, 알 수 없는 button code는 no-op으로 둔다.
