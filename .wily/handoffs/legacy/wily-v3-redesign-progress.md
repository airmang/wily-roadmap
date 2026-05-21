# Wily v3 Redesign Progress

## 2026-05-18T21:47:00+09:00 - Baseline

- Branch: `feat/wily-v3-redesign`.
- Initial status had pre-existing changes in `README.md` and `plugins/wily-roadmap/tests/test_wily_cli.py`.
- Initial untracked files: `wily`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`.
- Baseline verification: `python3 -m unittest discover -s plugins/wily-roadmap/tests -v` passed 273 tests, 2 skipped.
- Auto-resolved under active /goal: Superpowers review/continue gates -> proceed checkpoint-by-checkpoint with local evidence and final verification.

## 2026-05-18T22:05:00+09:00 - v3 Implementation Checkpoint

- Files changed: added `plugins/wily-roadmap/scripts/wily/` package, `plugins/wily-roadmap/scripts/yaml.py`, v3 CLI modules, and `plugins/wily-roadmap/tests/v3/test_v3_core.py`.
- Replaced `plugins/wily-roadmap/scripts/wily.py` with a v3 entry shim.
- Commands run:
  - `PYTHONPATH=plugins/wily-roadmap/scripts python3 -m wily.cli --help`
  - `python3 -m unittest discover -s plugins/wily-roadmap/tests/v3 -v`
- Result: v3 tests passed, 6 tests.
- Note: legacy local Codex hook still invokes `live-worked`; v3 shim makes legacy live hook commands non-blocking during migration and README will document removing the hook.

## 2026-05-18T22:18:00+09:00 - Cleanup, Migration, Verification Loop

- Removed v2-only runtime helpers and v2 tests.
- Replaced `plugins/wily-roadmap/skills/` with 11 v3 skills and `plugins/wily-roadmap/commands/` with v3 command docs.
- Updated `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, marketplace metadata, `.gitignore`, root README, and plugin README.
- Ran this repo's migration:
  - `python3 plugins/wily-roadmap/scripts/wily.py init adopt-legacy`
  - `python3 plugins/wily-roadmap/scripts/wily.py init --adopt`
  - answered brownfield interview
  - added and committed T01 into v3 `.wily/tasks.yaml`
- Verification commands:
  - `python3 -m unittest discover -s plugins/wily-roadmap/tests -v` -> PASS, 10 tests
  - `python3 plugins/wily-roadmap/scripts/wily.py status --json` -> PASS, exit 1 because T01 remains ready
  - `python3 plugins/wily-roadmap/scripts/wily.py watch --once` -> PASS, exit 1 because T01 remains ready
  - `python3 plugins/wily-roadmap/scripts/wily.py next` -> PASS, T01 ready
  - `python3 plugins/wily-roadmap/scripts/wily.py run T01` -> PASS, removed command exits 2
  - `rg -n "emit_board_live_event|wily-roadmap-v2|live-worked|board check|decompose-stage|wily run|wily-board" plugins/wily-roadmap -g '!**/docs/superpowers/**' -g '!*.pyc'` -> PASS, no matches

## 2026-05-18T22:34:00+09:00 - Review Fixes and Final Verification

- Applied final review fixes:
  - Removed implicit `git fetch` from status/watch observation path.
  - Kept stale `live-* --from-hook` non-blocking for local Codex hook safety, while normal `live-*` user calls exit 2 as removed v3 commands.
  - Added root README manual cleanup checklist for `~/.codex/hooks.json`, `.github/workflows/wily-board-sync.yml`, and `~/.wily/board.json`.
  - Added tests for block, replan, adopt-legacy, next `--mine`, no-fetch observation, cleanup docs, and live command behavior.
- Final verification commands:
  - `python3 -m unittest discover -s plugins/wily-roadmap/tests -v` -> PASS, 13 tests.
  - `python3 plugins/wily-roadmap/scripts/wily.py status --json` -> command OK, exit 1 because T01 is ready.
  - `python3 plugins/wily-roadmap/scripts/wily.py next` -> PASS, T01 ready.
  - `python3 plugins/wily-roadmap/scripts/wily.py run T01` -> PASS, removed command exits 2.
  - Runtime grep for removed/board/fetch surface under `plugins/wily-roadmap` excluding historical docs -> PASS, no matches.
