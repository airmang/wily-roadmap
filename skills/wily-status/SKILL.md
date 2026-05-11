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
- Korean user-facing headings and progress labels
- ASCII `Roadmap:` section grouped by dependency stage
- phase status labels rendered in Korean while roadmap file status values remain English
- phase lines with explicit `의존:` and `병렬:` annotations
- next phase
- ready phases
- blocked phases and blockers
- superseded or replaced phases when present

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Include the `Roadmap:` section verbatim in the user response.
- Do not replace the visual roadmap with a prose-only summary.
- Keep the ASCII roadmap visible even when also summarizing next or ready phases.
