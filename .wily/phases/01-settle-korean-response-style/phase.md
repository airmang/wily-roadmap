# Phase 01: Settle Korean Response-Style Update

## Purpose

Finish the current local change that makes Wily plugin and skill usage announcements Korean when the user is speaking Korean.

## Expected Starting Conditions

- Worktree contains the current response-style edits in Wily skill files.
- No Wily execution session has been created for this work yet.
- The roadmap has just been initialized.

## Likely Files

- `skills/wily-*/SKILL.md`
- `skills/wily-workflow/SKILL.md`
- `tests/test_wily_command_skills.py`

## Completion Criteria

- Every Wily command skill and the general workflow skill state the Korean announcement rule.
- Tests protect the rule from being dropped.
- Existing command skill tests still pass.
- Final summary clearly separates current local changes from any future roadmap work.

## Known Risks

- The worktree already contains user-visible changes, so avoid rewriting unrelated edits.
- Keep skill bodies concise while adding the response-style rule.
