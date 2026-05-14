# Phase 04-2: Harden Lifecycle Status CLI

## Purpose

Improve confidence in Wily lifecycle commands and roadmap summaries.

## Expected Starting Conditions

- Phase 03 is done.
- Command skill contracts and tests are stable.

## Likely Files

- `scripts/wily.py`
- `scripts/wily_state_summary.py`
- `tests/test_wily_cli.py`
- `tests/test_wily_state_summary.py`
- `skills/wily-status/SKILL.md`
- `skills/wily-next/SKILL.md`
- `skills/wily-start/SKILL.md`
- `skills/wily-complete/SKILL.md`
- `skills/wily-block/SKILL.md`
- `skills/wily-retry/SKILL.md`
- `skills/wily-replan/SKILL.md`

## Completion Criteria

- Status output remains stable and useful for ready, blocked, superseded, and replacement phases.
- Lifecycle commands preserve session history and current phase state.
- Tests cover important parse, serialize, and session edge cases.
- Helper script output stays machine-facing and English.

## Known Risks

- The custom YAML-like parser is intentionally small; avoid expanding it into a fragile partial YAML implementation.
- Preserve compatibility with existing test fixtures and roadmap files.
