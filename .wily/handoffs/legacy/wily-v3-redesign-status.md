# Wily v3 Redesign Status

- Objective: Implement Wily Roadmap v3 rewrite and migrate repo `.wily`.
- State: DONE
- Progress: 5/5 (100%)
- Current checkpoint/action: Final verification complete.
- Next checkpoint: User review / optional commit.
- Last updated: 2026-05-18T22:34:00+09:00

| Checkpoint | Status |
|---|---|
| Handoffs and baseline | DONE |
| v3 implementation | DONE |
| v2 cleanup and migration | DONE |
| verification loop | DONE |
| final report | DONE |

| Verification | Status | Evidence |
|---|---|---|
| baseline unittest | PASS | 273 tests, 2 skipped before rewrite |
| v3 unittest | PASS | 6 tests |
| final unittest | PASS | 13 tests |
| removed-surface grep | PASS | no runtime matches outside historical docs |
| CLI smoke | PASS | `next`, `run` removed exit 2, `watch --once`, `status --json` |

## Recent Events

- Created branch `feat/wily-v3-redesign`.
- Active goal created.
- Baseline test suite passed before rewrite.
- Added v3 package, CLI dispatch, lifecycle/status/watch/replan/land/init commands.
- Added local JSON-compatible `yaml` compatibility layer because PyYAML is absent in current Python.
- Replaced v2 skills, command docs, manifests, README, and removed v2 runtime/test files.
- Migrated repo `.wily` through `init adopt-legacy` and `init --adopt`.
- Addressed final review: removed implicit fetch, narrowed stale live hook compatibility to `--from-hook`, documented external cleanup, and added coverage for block/replan/adopt/next --mine/no-fetch.
