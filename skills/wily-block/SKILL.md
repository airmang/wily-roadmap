---
name: wily-block
description: Use when the user types $wily-block or a Wily phase cannot safely continue.
metadata:
  short-description: Block a Wily phase
---

# Wily Block

Use `$wily-block <phase-id> "<reason>"` to record that a phase is blocked.

This is state-changing. It marks the phase `blocked`, records the blocker in roadmap state, and marks the current session `blocked`.

## Command

```bash
python3 <plugin-root>/scripts/wily.py block <phase-id> "<reason>"
```

## When To Use

- verification fails for an unclear reason
- required credentials, permissions, or environment are missing
- the requested work would cross into another phase
- dirty worktree state would risk user changes
- remote or destructive work is required but not approved
