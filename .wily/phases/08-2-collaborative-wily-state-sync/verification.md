# Verification

Run:

```bash
git check-ignore -v .wily/roadmap.yaml .wily/phases/08-2-collaborative-wily-state-sync/phase.md .wily/sessions/example
python3 scripts/wily.py status
python3 scripts/wily.py next
python3 -m unittest tests.test_wily_cli
```

Expected:

- Shared Wily roadmap files are not ignored.
- Local-only session artifacts remain ignored if that is the selected policy.
- Next phase is `08-2` until it is completed.
