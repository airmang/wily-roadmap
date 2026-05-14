# Phase 11-1: Custom Workflow bundled runner 제거와 참조 전용 회귀

## Purpose

이전에 Wily 안으로 흡수했던 `custom-workflow` runner bundle을 Wily plugin에서 제거하고, Custom Workflow는 외부 플러그인/워크플로우로 참조해서 쓰는 방식으로 되돌린다.

## Dependencies

- 10-2 Codex app 환경의 wily-watch 전략 확정

## Expected Output

- `runners/custom-workflow/` bundled assets 제거.
- `scripts/wily_runner.py`와 `scripts/wily.py run`의 bundled runner dispatch 의존성 제거 또는 참조 전용 안내로 축소.
- `skills/wily-run/`, `commands/wily-run.md`, plugin default prompt에서 bundled runner dispatch 의미 제거 여부 결정.
- `skills/wily-workflow/references/runner-adapter-contract.md`를 삭제하거나, Custom Workflow를 외부 참조 workflow로 설명하는 짧은 reference 문서로 교체.
- `wily-watch` runner artifact progress 표시는 bundled runner artifact 전제에 묶여 있으면 제거하거나 generic session metadata 기반으로 낮춘다.
- 테스트에서 bundled runner 파일 존재/manifest/agent TOML/runner hooks를 요구하는 assertions 제거 또는 reference-only 계약에 맞게 교체.
- historical docs와 completed `.wily/phases/09-*` 기록은 완료된 과거 결정으로 보존하되, live plugin behavior가 bundled runner를 요구하지 않게 한다.

## Known Risks

- 완료된 09-* phase 기록을 수정/삭제하면 roadmap history가 깨진다. 과거 기록은 유지하고 새 phase로 되돌림을 기록한다.
- `wily-run`을 완전히 제거할지, 외부 runner handoff helper로 남길지 결정이 필요하다.
- tests가 bundled runner 파일 존재를 강하게 검증하므로 제거 작업은 테스트 계약 정리와 함께 해야 한다.
- Custom Workflow 관련 참조가 live skill guidance에 남으면 사용자가 여전히 bundled runner가 있다고 오해할 수 있다.
