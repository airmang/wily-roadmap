---
name: wily-watch
description: Use when the user types $wily-watch for a continuously refreshing Wily v3 project pane.
---

# Wily Watch

Render a live task snapshot, including actor lane, blocker text, and cp progress.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py watch [--once|--here|--interval N] [--ui auto|rich|ascii]
```

## Behavior

- Read-only: does not mutate `.wily/`.
- `--once` prints one snapshot and exits.
- In tmux, `wily watch` opens a right-side pane and runs the live view there.
- `--here` runs the live view in the current terminal.
- `--ui auto` uses Rich styling when available, including repo-local
  `.venv-watch`; `--ui ascii` forces plain ASCII.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Do not echo internal helper commands in normal user-facing responses.
