---
name: wily-next
description: Use when the user types $wily-next or asks which Wily task to pick up next.
---

# Wily Next

Find the first ready task whose dependencies are done.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py next [--mine|--json]
```

## Behavior

- Read-only: does not mutate `.wily/`.
- `--mine` filters by the current git author actor mapping.
- Parent-owned coordination mode is active when `.wily/coordination.yaml`
  exists. `wily next --json` includes `active_mode` and returns the parent task.
- Inside a registered child repo with its own `.wily/`, use the child-local
  project instead of the parent coordination project.
- In parent-owned coordination mode, `.wily/coordination.yaml` keeps `next` on
  the parent task ledger, JSON includes `active_mode`, and commands run inside a
  registered child repo with its own `.wily/` use the child-local project.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Do not echo internal helper commands in normal user-facing responses.
