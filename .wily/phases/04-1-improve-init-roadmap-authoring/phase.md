# Phase 04-1: Improve Init Roadmap Authoring

## Purpose

Improve the `$wily-init` experience so roadmap creation is easier to run repeatedly and less dependent on ad hoc manual scaffolding.

## Expected Starting Conditions

- Phase 03 is done.
- Command skill contracts and tests are stable.

## Likely Files

- `scripts/wily.py`
- `tests/test_wily_cli.py`
- `skills/wily-init/SKILL.md`
- `skills/wily-workflow/references/planning-style.md`
- `docs/superpowers/specs/2026-05-11-wily-roadmap-design.md`

## Completion Criteria

- Any deterministic init behavior belongs in `scripts/wily.py`.
- `$wily-init` still scans first and asks for a goal when none is supplied.
- Existing `.wily/` state is never overwritten without approval.
- Tests document the intended init behavior.

## Known Risks

- Fully automatic roadmap generation may be too broad or too interpretive for a deterministic script.
- Keep Codex responsible for project interpretation unless the behavior is deterministic.
