# Wily Watch Interactive Stage Toggle Implementation Plan

## Goal

Add local terminal interaction to `wily watch --here` so completed Stage groups that are folded for short panes can be expanded and collapsed without leaving the watch pane.

## Scope

- Keep `watch --once` deterministic and non-interactive.
- Add a render option that controls whether the leading completed-stage summary is folded or expanded.
- Add pure input parsing for keyboard and terminal mouse escape sequences so behavior is testable without real mouse hardware.
- Add a TTY-only interactive loop for `watch --here` with terminal restoration in all exits.
- Document the watch controls in the Wily watch skill.

## Design

1. Rendering state
   - Extend `wily_watch_ui.render_watch()` with `expand_done` and `interactive` flags.
   - Preserve existing default output by keeping completed stages folded only when height requires it and `expand_done` is false.
   - When `expand_done` is true, skip leading-done compaction so completed stages render as individual phase lines.
   - Change the footer only when interactive mode is active: show click/key toggle, refresh, and quit hints.

2. Input model
   - Add small, pure helpers in `scripts/wily.py`:
     - parse `d`, `r`, `q`, and Ctrl-C.
     - parse SGR mouse press events like `ESC [ < 0 ; x ; y M`.
     - map clicks on the folded summary row to the same `toggle_done` action as `d`.
   - Keep mouse support local to terminals that emit SGR mouse events. Unknown input is ignored.

3. Interactive loop
   - In `watch --here`, enable cbreak input and SGR mouse reporting only when stdin/stdout are TTYs and `--no-interactive` is absent.
   - Use `select.select()` with the refresh interval so keyboard/mouse events can trigger immediate redraws.
   - Restore terminal mode and disable mouse reporting in a `finally` block.
   - Keep non-TTY `watch --here` behavior as a simple periodic redraw.

4. Tests
   - Add renderer tests for folded vs expanded done stages and interactive footer text.
   - Add CLI helper tests for keyboard actions and SGR mouse action mapping.
   - Keep existing pane command and one-shot preview tests stable.

5. Verification
   - Run focused watch and CLI unit tests.
   - Run full unittest discovery.
   - Compile touched scripts.
   - Smoke `./wily watch --once --ui ascii`.
   - Run a TTY smoke of `watch --here` with synthetic key/mouse input and `q` exit.
