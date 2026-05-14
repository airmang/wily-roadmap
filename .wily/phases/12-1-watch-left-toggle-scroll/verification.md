# Verification

Run focused watch interaction tests and CLI checks:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_watch_ui
python3 -m py_compile scripts/wily.py scripts/wily_watch_ui.py
```

Add or update tests that cover:

- left mouse press toggles completed-stage expand/collapse;
- right and middle mouse presses do not toggle;
- mouse release does not toggle;
- wheel up/down return scroll actions and never toggle;
- scroll offset clamps when expanded content is longer than visible rows;
- `--once --ui ascii` output remains deterministic.

Manual smoke check in a real terminal or tmux pane:

```bash
./wily watch --here --ui ascii
```

Expected: left click toggles the done-stage view, and after expanding a long roadmap body the mouse wheel scrolls up and down.
