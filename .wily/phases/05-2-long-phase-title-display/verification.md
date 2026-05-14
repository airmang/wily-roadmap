# Verification

Run:

```bash
python3 -m unittest tests.test_wily_state_summary tests.test_wily_watch_ui
python3 -m unittest discover
python3 -m py_compile scripts/wily_state_summary.py scripts/wily_watch_ui.py
```

Also inspect representative status/watch output with a long Korean Phase title.
