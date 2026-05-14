# Phase 06-4: 진행된 레포에서 wily-init 동작 계약 확정

## Purpose

이미 작업이 많이 진행된 레포에서 `$wily-init`을 실행했을 때 무엇을 보존하고, 무엇을 생성하고, 어떤 다음 행동을 안내할지 명확히 정한다.

## Expected Starting Conditions

- Phase 05 is done.
- Current init behavior preserves existing `.wily` files and repairs missing directories.

## Likely Files

- `scripts/wily.py`
- `tests/test_wily_cli.py`
- `skills/wily-init/SKILL.md`
- `skills/wily-workflow/references/`

## Completion Criteria

- mature repo init behavior contract가 문서화된다.
- 기존 `.wily` 상태가 있을 때 보존/수리/요약/다음 행동 기준이 명확하다.
- `.wily`가 없는 기존 코드베이스에서 어떤 baseline을 만들지 정해진다.
- 테스트가 clean repo, partial `.wily`, existing roadmap/status, mature repo hints를 커버한다.

## Known Risks

- init이 자동 분석을 너무 많이 하면 의도치 않은 변경이 늘어난다.
- 기존 사용자 작성 roadmap/status를 덮어쓰면 안 된다.
