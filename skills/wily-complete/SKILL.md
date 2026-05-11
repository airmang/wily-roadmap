---
name: wily-complete
description: Use when the user types $wily-complete after a Wily phase has been implemented and verified.
metadata:
  short-description: Complete a verified Wily phase
---

# Wily Complete

Use `$wily-complete <phase-id>` to mark a verified phase as done.

This is state-changing. It marks the phase `done`, clears stale phase blocker metadata, and marks the current session `verified` when one exists.

## Command

```bash
python3 <plugin-root>/scripts/wily.py complete <phase-id>
```

## Required Before Running

- The phase implementation matches the approved scope.
- Verification has run, or the reason it could not run is recorded.
- Changed files and result are summarized in the current session.
- The user approved completion when review is required.

Complete does not implement the phase or run broad verification by default. It closes a verified execution attempt.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
