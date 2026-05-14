# Verification

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
python3 -m unittest discover
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```

Check:
- Wily skill files include the Korean announcement rule.
- Tests pass without warnings or failures.
