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

- $wily-watch opens a tmux pane when already running inside tmux. It uses a vertical split on the right and targets the current pane from `TMUX_PANE` when available.
- Outside tmux, `$wily-watch` runs the live dashboard in the current interactive terminal.
- In Codex app, open a side terminal and run `./wily watch`.
- Renders a vertical pipeline of the roadmap: header (`Wily Roadmap · vN  ⟳ Ns`), a progress bar (`done/total · pct%`), then one line per phase as `<status glyph> <id>  <title>`.
- Long phase titles use middle ellipsis so the start and end stay visible within the pane width.
- Phase lines include a `git log --graph`-style left rail: `│` for linear flow, `├──` for parallel branches, and `▼` for fan-in.
- Dependency labels show `needs` for unmet dependencies and `deps` for fan-in dependency lists.
- Phase lines show shared assignment metadata from `roadmap.yaml`: `owner`, `assignee`, or `assigned_to` renders as `@name`; `task` or `assignment` renders as `task ...`.
- When a phase has external workflow progress artifacts under `.wily/sessions/<session>/runner/`, phase lines may include compact progress such as `workflow in_progress` or `workflow needs_review`.
- Falls back to a flat `Stage N` list when the dependency graph is too tangled for the rail, and to a one-line summary when the pane is very narrow.
- When the pane is too short, leading fully completed stages collapse to a single `● N phases done across M stages ▾` line; unfinished, current, ready, and blocked phases stay visible ahead of decorative rails or stage headers.
- In an interactive TTY pane, left-click the collapsed done-stage summary or visible done-stage body row, or press `d`, to expand/collapse completed stages. Right-click opens a tmux context menu. When completed stages are expanded and the body is taller than the pane, use the mouse wheel to scroll. Press `r` to refresh immediately and `q` or Ctrl-C to quit.
- Uses Rich when installed, otherwise falls back to ASCII. The ASCII fallback uses `*`/`>`/`~`/`x`/`o` glyphs and a `[####----]` progress bar.
- Adds a footer with git dirty-file count, the repo name, and either a `^C to stop` hint or the interactive click/key hints.
- Opens a horizontal tmux split (`split-window -h`) when running inside tmux, with `-t $TMUX_PANE` when the current pane id is available.
- Returns clear side-terminal guidance when invoked from a non-interactive process outside tmux.
- Run `$wily-watch --install-ui` to install the optional Rich UI dependency.
- Accepts `--ui rich|ascii|auto` for UI selection.
- Accepts `--once` for tests or a one-shot preview; this mode is deterministic and does not enable interaction.
- Accepts `--interval <seconds>` for refresh cadence.
- Accepts `--show-done` to start with completed stages expanded.
- Accepts `--no-interactive` to force the old passive refresh loop in `--here` mode.
- Use `--here` to force current-terminal live mode.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- If the pane or current-terminal dashboard opens, report that it opened and how to stop it; show side-terminal guidance only when the command is non-interactive outside tmux.
