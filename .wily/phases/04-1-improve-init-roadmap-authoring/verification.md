# Verification

Run:

```bash
python3 -m unittest tests.test_wily_cli
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```

Also test a temporary project init path manually if script behavior changes.
