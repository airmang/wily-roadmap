# Verification

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui tests.test_wily_cli
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_watch_ui.py
```

Manually inspect:

```bash
./wily watch --once --ui ascii
```

If interactive mode is implemented, manually run `$wily-watch` or `./wily watch --here` in a tmux pane and verify:

- click toggles folded completed stage details,
- keyboard fallback toggles the same state,
- `q` or `Ctrl-C` exits and restores terminal behavior.
