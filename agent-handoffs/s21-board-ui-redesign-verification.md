# S21 Board UI Redesign Verification

## Baseline

Command:

```sh
uv run pytest
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board
```

Result:

```text
71 passed, 26 warnings in 1.33s
```

Notes:
- Warnings are existing Starlette TestClient cookie deprecations.

## Execution Package Validator

Command:

```sh
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/s21-board-ui-redesign-execution-package.md
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
```

First result:

```text
FAIL: execution package is missing required contract items:
- pre-existing modified files
- reviewer gates
```

Remediation:
- Added explicit package sections for both required contract items.

Second result:

```text
PASS: execution package contract is complete.
```

## API Route Tests

Command:

```sh
uv run pytest tests/test_api_routes.py -q
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board
```

First RED result:

```text
8 failed
```

Expected cause:
- New `/api/*` endpoints did not exist yet and returned 404.

Final result:

```text
8 passed, 7 warnings in 0.31s
```

## Full Python Suite After API

Command:

```sh
uv run pytest
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board
```

Result:

```text
79 passed, 33 warnings in 1.38s
```

## Final Verification

### Wily Plugin Suite

Command:

```sh
python3 -m unittest discover plugins/wily-roadmap/tests
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
```

Result:

```text
Ran 204 tests in 6.183s
OK (skipped=2)
```

### Wily Script Compile

Command:

```sh
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_watch_ui.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_runner.py
```

Result: pass.

### Board Backend Suite

Command:

```sh
uv run pytest
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board
```

Result:

```text
79 passed, 31 warnings in 1.79s
```

### Frontend Lint

Command:

```sh
npm run lint
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
```

Result: pass.

### Frontend Build

Command:

```sh
npm run build
```

Working directory:

```text
/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
```

Result:

```text
Compiled successfully. Routes: /, /api/repos, /repos/[owner]/[name].
```

### Browser Smoke

Desktop repo workspace:
- `CP04` checkpoint overlay visible in Global/Local Desk and Phase row.
- React Flow rendered with dark/light themed controls.
- No app layout overflows beyond the known 3px internal React Flow pane measurement.

Mobile repo workspace:
- `CP04` checkpoint overlay visible.
- Local Desk mobile bar visible.
- Rail hidden.
- React Flow hidden.
- Horizontal overflow: 0.

### Wily Roadmap Closure

Commands:

```sh
python3 plugins/wily-roadmap/scripts/wily.py status --once
python3 plugins/wily-roadmap/scripts/wily.py next
```

Result:

```text
23/23 - 100%
Next phase: none
```
