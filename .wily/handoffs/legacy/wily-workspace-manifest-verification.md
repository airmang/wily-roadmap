# Verification: Wily Workspace Manifest Multi-Repo CLI

## Environment

- Installed local test dependency: `PyYAML 6.0.3` with `python3 -m pip install --user --break-system-packages PyYAML` because the existing Wily Python modules import `yaml`.

## RED / GREEN Evidence

- Manifest discovery RED: `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core -k workspace` failed with `ModuleNotFoundError: No module named 'wily.workspace'`.
- Manifest discovery GREEN: same command passed 2 tests after adding `wily.workspace`.
- Aggregate summary RED: same command failed because `workspace_snapshot` and `workspace_next_tasks` were missing.
- Aggregate summary GREEN: same command passed 4 tests after adding aggregate snapshot/next helpers.
- CLI RED: same command failed with `unknown command: 'workspace'`.
- CLI/watch GREEN: same command passed 6 tests after registering the command and adding watch touch-mtime coverage.
- Surface RED: `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_surface` failed for missing `commands/workspace.md`, `skills/wily-workspace`, and plugin prompt docs.
- Surface GREEN: same command passed 22 tests after docs/skill/prompt updates.
- Reviewer RED: added `test_workspace_next_reports_invalid_child_repos_without_hiding_valid_tasks`; it failed because `workspace next` suppressed invalid repo errors.
- Reviewer GREEN: `workspace next` now emits per-repo errors to stderr while still returning valid ready tasks; targeted workspace tests pass 7 tests.

## Final Commands

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: PASS, 115 tests.

After reviewer fix:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: PASS, 116 tests. Rerun after marking T27 done also passed, 116 tests.

```bash
cd /Users/wilycastle/Code/projects/wily-plugin
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace status --json
```

Result: PASS. JSON title is `Wily Plugin Workspace`; repos are `wily-roadmap` and `wily-board`; no per-repo errors.

```bash
cd /Users/wilycastle/Code/projects/wily-plugin
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace next
```

Result: PASS. Output includes `wily-roadmap T26` and `wily-board T01`.

```bash
cd /Users/wilycastle/Code/projects/wily-plugin
python3 wily-roadmap/plugins/wily-roadmap/scripts/wily.py workspace watch --once
```

Result: PASS. Output renders both child repos from the parent manifest.

```bash
cd /Users/wilycastle/Code/projects/wily-plugin
test ! -d .wily
```

Result: PASS. Parent `.wily/` is absent.

```bash
git diff --check
```

Result: PASS.

Final ledger check: `.wily/tasks.yaml` is valid JSON after marking T27 done, and parent workspace status still sees `wily-roadmap` and `wily-board` with no per-repo errors.

## Review / Completion

- Integration reviewer found one P2 issue: `workspace next` hid invalid child repo errors. Fixed with RED/GREEN coverage.
- Completion verifier result: PASS. All acceptance criteria are satisfied against implementation, docs, parent manifest, and verification evidence.
