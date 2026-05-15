# Verification

Run focused tests for roadmap parsing and lifecycle behavior:

```bash
python3 -m unittest tests.test_wily_state_summary tests.test_wily_cli
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
```

Then run the full suite:

```bash
python3 -m unittest discover
```

Expected:

- old Phase-only roadmaps still parse and render;
- new Stage-level roadmaps can be initialized without premature Phase expansion;
- Stage decomposition creates executable internal Phase work without losing Stage metadata;
- next/status/watch remain readable at both levels.
