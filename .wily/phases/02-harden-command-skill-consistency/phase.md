# Phase 02: Harden Command Skill Consistency

## Purpose

Make the `$wily-*` command skills consistently short, discoverable, and aligned with shared workflow policy.

## Expected Starting Conditions

- Phase 01 is done.
- Korean response-style guidance is already settled and tested.

## Likely Files

- `skills/wily-init/SKILL.md`
- `skills/wily-status/SKILL.md`
- `skills/wily-next/SKILL.md`
- `skills/wily-start/SKILL.md`
- `skills/wily-complete/SKILL.md`
- `skills/wily-block/SKILL.md`
- `skills/wily-retry/SKILL.md`
- `skills/wily-replan/SKILL.md`
- `skills/wily-workflow/SKILL.md`
- `skills/wily-workflow/references/*.md`
- `tests/test_wily_command_skills.py`

## Completion Criteria

- Each command skill has a clear trigger, helper command, boundary, and response style.
- Shared policy stays in `skills/wily-workflow/references/` instead of being duplicated across command skills.
- Frontmatter remains valid for Codex skill discovery.
- Tests cover the consistency requirements that matter for future edits.

## Known Risks

- Over-documenting each command skill would violate the repo guidance to keep skill bodies concise.
- Tests should verify important invariants without hard-coding brittle prose.
