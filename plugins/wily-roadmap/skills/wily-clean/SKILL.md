---
name: wily-clean
description: Use when the user types $wily-clean to remove safe local temporary artifacts generated during Wily development.
metadata:
  short-description: Clean local Wily temp artifacts
---

# Wily Clean

Use `$wily-clean` to inspect safe local cleanup candidates. By default this is a dry-run and deletes nothing.

This is state-changing local cleanup only when `--yes` is used. It removes a narrow allowlist of temporary artifacts:

- `.wily/local/live/**`
- `.wily/local/board-last-emit.json`
- `.playwright-mcp/**`
- Python test cache directories
- `__pycache__/**`
- `*.pyc`

It must preserve durable or audit-relevant files, including:

- `.wily/local/board.json`
- `.wily/roadmap.yaml`
- `.wily/stages/**`
- `.wily/phases/**`
- `.wily/revisions/**`
- `.wily/sessions/**`
- `agent-handoffs/**`
- source, test, and documentation files

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py clean [--yes]
```

## Required Before Running

- Run without `--yes` first when the user asks to inspect cleanup candidates.
- Use `--yes` only when the user explicitly asks to remove safe local temporary artifacts.
- Do not run broad destructive cleanup commands.
- Do not remove sessions, handoffs, roadmap state, source files, docs, or tests.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For dry-run, report that nothing was deleted and summarize the cleanup candidates.
- For `--yes`, report the removed candidate count and any failed removals.
