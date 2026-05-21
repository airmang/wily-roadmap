# Progress: Wily Workspace Manifest Multi-Repo CLI

## 2026-05-20

- Created execution package and status board.
- Implementation has not started.
- Native goal started for workspace manifest CLI.
- Checkpoint 1 started. Baseline: `git status --short` is dirty with existing Board docs/handoffs plus workspace handoff files; parent `/Users/wilycastle/Code/projects/wily-plugin/.wily` is absent. Lane A read-only repo-facts subagent launched.
- Auto-resolved under active /goal: Superpowers TDD approval/continue gate -> follow RED/GREEN evidence checkpoint-by-checkpoint without stopping for user approval.
- Checkpoint 1 complete. Added `.wily/tasks.yaml` T27 for this workspace manifest CLI while preserving existing user-added T26/T28 entries. Verified the ledger remains valid JSON with 28 unique task ids. Installed `PyYAML 6.0.3` into the user Python environment because the existing Wily code imports `yaml` and `python3 -m unittest` could not import it.
- Checkpoint 2 RED: added manifest discovery/parser tests in `plugins/wily-roadmap/tests/v3/test_v3_core.py`; `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core -k workspace` failed with `ModuleNotFoundError: No module named 'wily.workspace'`.
- Checkpoint 3 GREEN: added `plugins/wily-roadmap/scripts/wily/workspace.py` with `discover_workspace_manifest`, `load_workspace`, manifest dataclasses, schema validation, and relative child path resolution. Targeted command now passes 2 tests.
- Checkpoint 4 RED: added aggregate summary and aggregate next tests; targeted command failed because `workspace_snapshot` and `workspace_next_tasks` were missing.
- Checkpoint 5 GREEN: implemented workspace summaries using existing `load_tasks`, `load_actors`, `repo_mode`, `parallel_candidates`, and `waiting_candidates`; invalid repos now return per-repo error payloads.
- Checkpoint 6 RED: added CLI integration test for `workspace init`, `show-config --json`, `status --json`, `next`, and `watch --once`; targeted command failed with `unknown command: 'workspace'`.
- Checkpoint 7 GREEN: registered `workspace`, added `wily.cli.workspace`, and added Korean help description. `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core -k workspace` now passes 5 tests.
- Checkpoint 8 complete: added watch helper coverage for child `.wily/.touch` mtime tracking and interval validation. Targeted workspace tests pass 6 tests.
- Checkpoint 9 RED/GREEN: updated surface tests for `workspace`, observed missing docs/skill/prompt failures, then added `commands/workspace.md`, `skills/wily-workspace/SKILL.md`, README manifest docs, and plugin prompt entry. `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_surface` passes 22 tests.
- Checkpoint 10 started: parent `/Users/wilycastle/Code/projects/wily-plugin` has no `.wily/`; both child repos have `.wily/tasks.yaml`; created parent `wily-workspace.yaml` manifest.
- Checkpoint 10 complete: parent smoke passed from `/Users/wilycastle/Code/projects/wily-plugin`: `workspace status --json` sees `wily-roadmap` and `wily-board` with no per-repo errors; `workspace next` emits `wily-roadmap T26` and `wily-board T01`; `workspace watch --once` renders both repos; `test ! -d .wily` passes.
- Checkpoint 11 running: full verification passed with `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface` (115 tests). `git diff --check` passes. Read-only integration reviewer subagent is running.
- Integration reviewer finding: `workspace next` skipped invalid child repos. RED test `test_workspace_next_reports_invalid_child_repos_without_hiding_valid_tasks` failed as expected; implementation now emits `[repo] ERROR ...` to stderr while preserving valid next-task output. Targeted workspace tests pass 7 tests; full core/surface tests pass 116 tests; parent smoke still passes.
- Completion verifier PASS: all execution package acceptance criteria satisfied against implementation, docs, parent manifest, and verification evidence. Marked T27 and live status board DONE.
