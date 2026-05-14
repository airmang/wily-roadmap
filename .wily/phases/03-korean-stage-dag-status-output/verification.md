# Verification

Run:

```bash
python3 -m unittest tests.test_wily_state_summary
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```

Manual check:

```bash
python3 scripts/wily.py status
```

Confirm the output uses Korean headings and a stage-based DAG layout.
