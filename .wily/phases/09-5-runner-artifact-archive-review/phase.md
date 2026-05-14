# Phase 09-5: Runner artifact archive와 review handoff 연결

## Purpose

Runner output을 Wily session history 안에 durable archive로 남기고 review handoff 흐름을 연결한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-bundled-runner-architecture.md`

## Dependencies

- 09-4 Runner dispatch helper 구현

## Expected Output

- `.wily/sessions/<session>/runner/` archive layout support
- `status.yaml` runner metadata recording
- Copy or snapshot runner artifacts at dispatch and finalization
- Completion/review handoff guidance for `needs_review`, `blocked`, and verified completion
- Tests proving `wily-run` does not mark phases done

## Known Risks

- Active runner-native files and durable Wily history must not diverge silently.
- Existing session history must remain readable.
