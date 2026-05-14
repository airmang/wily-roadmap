# Phase 13-1: roadmap YAML 블록 문법 데이터 손실 방지

## Purpose

`.wily/roadmap.yaml`에 유효한 YAML 블록 스칼라나 블록 리스트가 들어 있을 때 `$wily-start`, `$wily-complete`, `$wily-replan` 같은 상태 변경 명령이 값을 손실한 채 다시 저장하지 않도록 한다.

## Dependencies

- 12-1 Watch pane 왼쪽 버튼 토글과 펼친 상태 스크롤 보정

## Expected Output

- `summary: >-` 또는 `summary: |` 형태의 블록 스칼라를 파싱해 본문을 보존한다.
- `depends_on:` 아래의 블록 리스트를 phase 리스트 시작으로 오인하지 않는다.
- 상태 변경 명령이 roadmap을 다시 쓸 때 파싱된 블록 스칼라와 블록 리스트의 의미 값이 유지된다.
- 기존 인라인 리스트와 한 줄 scalar 형식은 계속 동작한다.
- 데이터 손실 재현 테스트가 추가된다.

## Likely Files

- `scripts/wily_state_summary.py`
- `scripts/wily.py`
- `tests/test_wily_state_summary.py`
- `tests/test_wily_cli.py`

## Known Risks

- 외부 YAML dependency를 추가하면 플러그인 설치/실행 경로가 무거워질 수 있다.
- 미니 파서를 유지할 경우 전체 YAML이 아니라 Wily roadmap subset만 지원한다는 경계를 분명히 해야 한다.
- serializer가 멀티라인 문자열을 잘못 쓰면 다음 파싱에서 다시 손실이 생길 수 있다.
