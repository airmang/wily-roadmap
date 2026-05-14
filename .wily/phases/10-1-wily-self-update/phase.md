# Phase 10-1: Zip bootstrap에서 GitHub self-update 경로 제공

## Purpose

Zip으로 공유된 Wily 설치본이 다음 릴리즈부터 GitHub 기반 managed install로 전환하거나 스스로 업데이트할 수 있게 한다.

## Source Spec

- `docs/superpowers/specs/2026-05-14-wily-self-update-design.md`

## Dependencies

- 09-6 Optional runner hooks와 watch progress 후속 통합

## Expected Output

- `./wily update` CLI command.
- `$wily-update` Codex skill entrypoint.
- Zip install detection and clear migration guidance.
- Git-managed install update check and fast-forward-only update path.
- README guidance for zip bootstrap and managed GitHub install.
- Tests that avoid real network access.

## Known Risks

- The command must not update in the background.
- Zip installs must not be overwritten or deleted automatically.
- Dirty plugin checkouts must be protected from accidental pulls.
- Remote operations must remain explicit and approval-first.
