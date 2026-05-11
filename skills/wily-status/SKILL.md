---
name: wily-status
description: Use when the user types $wily-status or asks to summarize current Wily roadmap progress.
metadata:
  short-description: Show Wily roadmap status
---

# Wily Status

Use `$wily-status` to summarize current `.wily` roadmap state.

This is read-only. It must not create sessions, change phase status, or revise roadmap files.

## Command

```bash
python3 <plugin-root>/scripts/wily.py status
```

## Report

- roadmap version
- progress counts
- next phase
- ready phases
- blocked phases and blockers
- superseded or replaced phases when present
