# Wily Self-Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit Wily update command that lets zip recipients migrate to a managed GitHub install and lets git-managed installs check or apply fast-forward-only updates.

**Architecture:** `scripts/wily.py update` operates on the plugin install root, not the target project root. The command separates read-only checks, git-managed updates, and zip migration; command skills and README documentation expose the workflow without adding background behavior.

**Tech Stack:** Python standard library `subprocess`, `json`, `unittest`, Markdown command skills, Codex and Claude plugin manifests.

---

## File Structure

- `scripts/wily.py`: add update helpers, `command_update`, usage text, and main dispatch.
- `tests/test_wily_cli.py`: add red-green tests for zip detection, dirty git refusal, already-current git checks, and migration with a local bare remote.
- `tests/test_wily_command_skills.py`: add `$wily-update` to command discovery and default prompt expectations.
- `skills/wily-update/SKILL.md`: new Codex skill entrypoint for the update command.
- `commands/wily-update.md`: new Claude Code command metadata.
- `.codex-plugin/plugin.json`: add `$wily-update` to default prompts.
- `README.md`: document zip bootstrap, managed GitHub install, and update command.
- `.wily/sessions/2026-05-14-215005-phase-10-1-attempt-1/*`: record result and verification evidence before completion.

## Task 1: Add Failing CLI Tests

- [ ] Add `SelfUpdateCliTest` to `tests/test_wily_cli.py`.
- [ ] Test `update --check` in a copied zip-style plugin reports the install is zip-based and suggests `./wily update --migrate`.
- [ ] Test `update --check` refuses a dirty git-managed install before fetch or pull.
- [ ] Test `update --check` reports an already-current git-managed install using a local bare remote and an expected-repository environment override.
- [ ] Test `update --migrate` clones a local bare remote into a sibling managed directory without deleting the source zip install.
- [ ] Run the focused tests and confirm they fail because `update` is not implemented yet.

## Task 2: Implement Update Command

- [ ] Add manifest version loading from `.codex-plugin/plugin.json`.
- [ ] Add a small `run_git()` helper that captures stdout and stderr.
- [ ] Add git root detection for the plugin root.
- [ ] Add dirty tree detection with compact changed path output.
- [ ] Add remote URL resolution with `WILY_UPDATE_REPOSITORY_URL` test override and `https://github.com/airmang/wily-roadmap` default.
- [ ] Implement `update --check` for non-git, dirty git, already-current, and update-available states.
- [ ] Implement `update --yes` as the only noninteractive fast-forward update path.
- [ ] Implement `update --migrate` for zip installs by cloning into a sibling `wily-roadmap-managed` directory.
- [ ] Wire `update` into usage and main dispatch.
- [ ] Run focused CLI tests and fix only failures related to this feature.

## Task 3: Add Command Skill and Docs

- [ ] Add `skills/wily-update/SKILL.md` with local-first approval-first boundaries.
- [ ] Add `commands/wily-update.md`.
- [ ] Add `$wily-update` to command skill tests and plugin default prompts.
- [ ] Update README with zip bootstrap and managed install guidance.
- [ ] Run command skill tests and JSON manifest validation.

## Task 4: Verify and Complete

- [ ] Run focused tests: `python3 -m unittest tests.test_wily_cli tests.test_wily_command_skills`.
- [ ] Run full tests: `python3 -m unittest discover`.
- [ ] Run manifest validation: `python3 -m json.tool .codex-plugin/plugin.json >/dev/null`.
- [ ] Update session handoff with changed files and verification evidence.
- [ ] Run `python3 scripts/wily.py complete 10-1`.
