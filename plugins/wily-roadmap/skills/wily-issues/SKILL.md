---
name: wily-issues
description: Use when the user types $wily-issues or asks to inspect GitHub Issues linked to the Wily roadmap.
metadata:
  short-description: Inspect GitHub issue linkage
---

# Wily Issues

Use `$wily-issues` to inspect GitHub Issues and compare them with Wily roadmap phases.

The default command is read-only. It may inspect GitHub Issues only because the user explicitly invoked this command. It must not create, update, comment on, close, label, assign, or otherwise mutate GitHub issues.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py issues
```

## Optional Local Roadmap Update

After showing unlinked open issues and suggested roadmap additions, ask for user approval before changing Wily state.

If the user approves adding suggested phases, run:

```bash
python3 <plugin-root>/scripts/wily.py issues --add-to-roadmap
```

This updates only local `.wily` roadmap and phase files. It does not write to GitHub.

## Boundaries

- Keep `$wily-status`, `$wily-next`, and `$wily-start` GitHub-free by default.
- Do not add unlinked issues to the roadmap without user approval.
- Do not create or update GitHub issues from this command.
- Treat issue creation, comments, labels, assignees, and closing as future explicit remote-write commands.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Show linked issues, unlinked open issues, and suggested roadmap additions.
