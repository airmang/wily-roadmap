---
name: wily-land
description: Use when the user types $wily-land after a task is done and asks to commit or push it.
---

# Wily Land

Collect scoped changed files, create a git commit with `Wily-Task: <id>`, and optionally push after explicit approval.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py land <id> [--no-push|--force|--include-ledger-closure]
```

## Behavior

- State-changing: creates a git commit.
- Without `--include-ledger-closure`, stop if out-of-scope Wily ledger files are present.
- Use `--include-ledger-closure` to include `.wily/tasks.yaml`, `.wily/tasks/<id>/result.md`, or task `progress.jsonl` closure files with the landing commit.
- Remote actions remain approval-first; do not push without explicit user approval.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
