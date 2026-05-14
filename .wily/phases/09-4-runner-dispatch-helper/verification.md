# Verification

Run:

```bash
python3 -m unittest tests.test_wily_cli
python3 -m py_compile scripts/wily.py scripts/wily_runner.py
```

Skip `scripts/wily_runner.py` in the compile command if no dedicated helper is created.
