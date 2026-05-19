# Wily Board Plan 2 Agent Verification

## Baseline

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -q
```

Result:

```text
40 passed, 2 warnings in 0.38s
```

Warnings:
- Starlette/TestClient cookie deprecation warnings in `tests/test_auth_sessions.py`.

## Final

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run pytest -v
```

Result:

```text
31 passed in 0.75s
```

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .
```

Result:

```text
All checks passed!
```

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v
```

Result:

```text
42 passed, 2 warnings in 0.35s
```

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .
```

Result:

```text
All checks passed!
```
