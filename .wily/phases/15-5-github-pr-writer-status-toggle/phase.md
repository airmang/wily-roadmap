# Phase 15-5: GitHub PR writer and phase status toggle

## Purpose

Add the first dashboard write action: safely create a GitHub PR that changes one Wily Phase status.

## Dependencies

- 15-4 Wily sync webhook, parser, and backfill

## Expected Output

- GitHub App installation token flow creates a branch, commit, and PR.
- Status changes use a narrow YAML edit that preserves unrelated formatting as much as practical.
- Phase status toggle action records `pr_created` events.
- Automatic merge remains off.
- Failure states are visible to the UI layer.

## Likely Files

- `app/actions/pr_writer.py`
- `app/actions/toggle_status.py`
- `app/web/routes.py`
- `tests/test_pr_writer.py`
- `tests/test_toggle_status.py`

## Known Risks

- Bytes-level YAML replacement must avoid changing the wrong status field when Stage and Phase IDs are similar.
- GitHub App setup is user-owned and may block live tests.
- Concurrent PRs against the same `.wily/` file may conflict; that is acceptable for v1.

