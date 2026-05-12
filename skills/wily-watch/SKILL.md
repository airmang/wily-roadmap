---
name: wily-watch
description: Use when the user types $wily-watch or wants a continuously refreshing Wily roadmap pane.
metadata:
  short-description: Watch Wily roadmap status
---

# Wily Watch

Use `$wily-watch` to show a continuously refreshing `.wily` roadmap view.

This is read-only. It must not create sessions, change phase status, revise roadmap files, or implement phases.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py watch --pane
```

## Behavior

- $wily-watch opens a tmux pane by default. It uses a vertical split on the right.
- Renders a vertical pipeline of the roadmap: header (`Wily Roadmap · vN  ⟳ Ns`), a progress bar (`done/total · pct%`), then one line per phase as `<status glyph> <id>  <title>`.
- Long phase titles use middle ellipsis so the start and end stay visible within the pane width.
- Phase lines include a `git log --graph`-style left rail: `│` for linear flow, `├──` for parallel branches, and `▼` for fan-in.
- Dependency labels show `needs` for unmet dependencies and `deps` for fan-in dependency lists.
- Falls back to a flat `Stage N` list when the dependency graph is too tangled for the rail, and to a one-line summary when the pane is very narrow.
- When the pane is too short, leading fully completed stages collapse to a single `● N phases done across M stages ▾` line; unfinished, current, ready, and blocked phases stay visible ahead of decorative rails or stage headers.
- Uses Rich when installed, otherwise falls back to ASCII. The ASCII fallback uses `*`/`>`/`~`/`x`/`o` glyphs and a `[####----]` progress bar.
- Adds a footer with git dirty-file count, the repo name, and a `^C to stop` hint.
- Opens a horizontal tmux split (`split-window -h`) when running inside tmux.
- Returns a clear fallback command when tmux is unavailable.
- Run `$wily-watch --install-ui` to install the optional Rich UI dependency.
- Accepts `--ui rich|ascii|auto` for UI selection.
- Accepts `--once` for tests or a one-shot preview.
- Accepts `--interval <seconds>` for refresh cadence.
- Use `--here` only when the user asks to run watch in the current pane.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- If the pane opens, report that it opened and how to stop it; show fallback commands only when tmux is unavailable.
