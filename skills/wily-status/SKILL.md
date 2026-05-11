---
name: wily-status
description: Use when the user types $wily-status or asks to summarize current Wily roadmap progress.
metadata:
  short-description: Show Wily roadmap status
---

# Wily Status

Use `$wily-status` to show the current `.wily` roadmap pane once.

This is read-only. It must not create sessions, change phase status, or revise roadmap files.

## Command

```bash
python3 <plugin-root>/scripts/wily.py status
```

## Report

- roadmap version
- progress counts
- ASCII `Wily Roadmap` pane output
- progress bar and done/total percentage
- stage-based roadmap lines
- current, ready, pending, blocked, and done phase glyphs
- dependency hints such as `needs`
- git footer

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Include the `Wily Roadmap` pane output verbatim in the user response.
- Do not replace the visual roadmap pane with a prose-only summary.
- Do not switch to the fallback stage summary when the pane renderer is available.
