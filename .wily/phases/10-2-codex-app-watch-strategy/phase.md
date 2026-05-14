# Phase 10-2: Codex app 환경의 wily-watch 전략 확정

## Purpose

Codex app 환경에서 `wily-watch`를 어떻게 보여주고 운영할지 결정하고, 필요한 최소 구현을 추가한다.

## Dependencies

- 10-1 Zip bootstrap에서 GitHub self-update 경로 제공

## Expected Output

- Codex app에서 tmux pane 기반 watch가 가능한지, 불편한지, 또는 별도 표시 전략이 필요한지 명확히 정리한다.
- `wily watch`의 app-friendly 모드를 설계한다.
- 필요하면 `--once`, `--here`, `--ui ascii|rich|auto`와 별도로 Codex app에 맞는 출력 옵션을 추가한다.
- README 또는 Wily skill guidance에 Codex app watch 사용 방식을 문서화한다.
- 기존 terminal/tmux watch UX를 깨지 않는다.

## Known Risks

- Codex app 환경은 터미널 pane, background process, browser/plugin UI의 제약이 일반 터미널과 다를 수 있다.
- Watch가 너무 많은 출력을 만들면 Codex 대화 흐름을 방해할 수 있다.
- app-specific behavior가 core Wily CLI를 복잡하게 만들 수 있다.
