---
name: wily-block
description: Use when the user types $wily-block or a Wily phase cannot safely continue.
metadata:
  short-description: Block a Wily phase
---

# Wily Block

Use `$wily-block <phase-id> "<reason>"` to record that a phase is blocked.

This is state-changing. It marks the phase `blocked`, records the blocker in roadmap state, and marks the current session `blocked`.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py block <phase-id> "<reason>"
```

## When To Use

- verification fails for an unclear reason
- required credentials, permissions, or environment are missing
- the requested work would cross into another phase
- dirty worktree state would risk user changes
- remote or destructive work is required but not approved

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- For a block, include the phase id, blocker reason, and the smallest unblock requirement.
