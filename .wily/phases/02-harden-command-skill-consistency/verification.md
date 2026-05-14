# Verification

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
python3 -m unittest discover
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Search for obvious placeholders:

```bash
rg -n "TODO|TBD|placeholder|old external workflow" skills .codex-plugin tests
```
