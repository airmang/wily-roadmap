# Verification

Run focused update tests first, then the broader suite.

At minimum:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_command_skills
python3 -m unittest discover
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Manual checks:

- `./wily update --check` reports a zip/non-git install clearly when `.git` is absent in a temp copy.
- `./wily update --check` reports current version and commit in a git checkout.
- Dirty working trees are refused before any pull.
