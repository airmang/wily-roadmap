# Verification

Run focused tests for plugin discovery, CLI behavior, and watch output after removing bundled runner assumptions.

At minimum:

```bash
python3 -m unittest tests.test_wily_command_skills tests.test_wily_cli tests.test_wily_watch_ui
python3 -m unittest discover
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py scripts/wily_watch_ui.py
```

Also search live plugin files for stale bundled-runner wording:

```bash
rg -n "bundled runner|runners/custom-workflow|custom-workflow|Custom Workflow" .codex-plugin README.md skills commands scripts tests
```

Expected: remaining matches, if any, describe Custom Workflow as external/reference-only rather than bundled inside Wily.
