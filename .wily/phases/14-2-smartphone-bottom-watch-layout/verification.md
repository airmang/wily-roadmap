# Verification

Run focused watch tests:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_watch_ui
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_watch_ui.py
```

Then run the full suite:

```bash
python3 -m unittest discover
```

Expected:

- dry-run pane command uses the intended bottom horizontal split mode for smartphone/Codex app watch;
- compact horizontal layout fits short pane heights;
- existing side-pane watch behavior remains covered.
