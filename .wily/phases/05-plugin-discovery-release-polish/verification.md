# Verification

Run:

```bash
python3 -m unittest discover
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
rg -n "TODO|TBD|placeholder|old external workflow" .codex-plugin skills scripts tests docs
```

Review `git status --short` and summarize changed files before asking for any commit approval.
