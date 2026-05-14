# Verification

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_state_summary
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```
