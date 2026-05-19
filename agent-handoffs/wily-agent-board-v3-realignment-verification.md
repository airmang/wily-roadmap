# Wily Agent Board V3 Realignment Verification

Verification evidence will be appended checkpoint-by-checkpoint.

## Roadmap focused tests

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state plugins.wily-roadmap.tests.v3.test_v3_core.CliLifecycleTest.test_agent_cli_dispatch_lists_lifecycle_subcommands
```

Result:

```text
Ran 2 tests in 0.117s

OK
```

## Board agent route tests

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-board && uv run pytest tests/test_agent_routes.py -q
```

Result:

```text
3 passed in 0.21s
```

## Final verification

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result:

```text
Ran 102 tests in 6.044s

OK
```

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-board && uv run pytest -q
```

Result:

```text
102 passed, 16 warnings in 2.26s
```

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-board && uv run ruff check .
```

Result:

```text
All checks passed!
```

Command:

```bash
git diff --check
git -C /Users/wilycastle/Code/projects/wily-board diff --check
```

Result: both commands exited 0 with no output.
