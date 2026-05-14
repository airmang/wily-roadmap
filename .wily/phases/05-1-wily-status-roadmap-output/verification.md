# Verification

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_state_summary
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```

Also run `python3 scripts/wily.py status` in this repository and inspect the Roadmap output manually.
