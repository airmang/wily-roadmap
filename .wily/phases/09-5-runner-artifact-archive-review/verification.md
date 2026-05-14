# Verification

Run:

```bash
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_runner.py
```

Skip `scripts/wily_runner.py` in the compile command if no dedicated helper exists.
