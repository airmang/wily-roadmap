# Verification

Run watch-focused tests and the broader suite.

At minimum:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_watch_ui
python3 -m unittest discover
```

Manual checks:

- Existing `./wily watch --once --ui ascii` output still works.
- Existing tmux pane behavior remains documented and unchanged unless intentionally revised.
- Any Codex app-friendly mode produces bounded output suitable for a conversation update.
