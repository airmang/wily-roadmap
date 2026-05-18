---
name: wily-status
description: Use when the user types $wily-status for a one-shot Wily v3 project snapshot.
---

# Wily Status

Print one Wily v3 project snapshot, or JSON for agent/automation use.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py status [--json] [--ui auto|rich|ascii]
```

## Behavior

- Read-only: does not mutate `.wily/`.
- Exit codes: 0 all done, 1 active work remains, 2 blocked task exists.
- Non-JSON output uses the same Rich-capable renderer as `wily watch`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Do not echo internal helper commands in normal user-facing responses.
