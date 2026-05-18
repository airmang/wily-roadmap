# Wily Watch V3 Tmux UI Design

## Goal

Restore the pre-v3 `wily watch` terminal experience on top of the v3 flat task model.

## Scope

`wily watch` opens a right-side tmux pane when invoked inside tmux, and that pane runs a live `watch --here` loop. The renderer keeps the v3 data model: tasks, actors, checkpoint progress, blockers, and observed commits. Stage, phase, Board, live bridge, hooks, MCP servers, and app integrations stay out of scope.

## Behavior

- `wily watch --once` prints one snapshot and returns the same status code as `wily status`.
- `wily watch --here` runs in the current terminal and refreshes in place.
- `wily watch` inside tmux opens a horizontal split on the right and runs `watch --here`.
- `wily watch` outside tmux runs in the current TTY when possible, otherwise prints a manual fallback.
- `--ui auto|rich|ascii` and `--interval N` continue to work.

## UI

The UI remains terminal-native. Rich mode uses glyphs, rails, and color. ASCII mode uses stable plain characters. The layout shows a compact header, progress bar, mode, actors, then one task row per task with child rows for checkpoint progress, blockers, and observed commit guesses.

## Tests

Unit tests cover launch-mode selection, tmux command construction, interval parsing, renderer task rows, and `--once` preservation. Smoke verification runs the v3 tests and a one-shot ASCII watch command.
