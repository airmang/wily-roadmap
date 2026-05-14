# Verification

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_watch_ui
python3 -m py_compile scripts/wily.py
```

If a manifest parser or command skill parser is introduced, add and run focused tests for it.
