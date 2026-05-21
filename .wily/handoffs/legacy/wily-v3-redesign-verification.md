# Wily v3 Redesign Verification

## Baseline

```text
python3 -m unittest discover -s plugins/wily-roadmap/tests -v
Result: PASS, 273 tests, 2 skipped
```

## Final

```text
python3 -m unittest discover -s plugins/wily-roadmap/tests -v
Result: PASS, 13 tests
```

```text
python3 plugins/wily-roadmap/scripts/wily.py status --json
Result: PASS command execution; exit 1 because T01 is ready, which is expected for status health semantics.
```

```text
python3 plugins/wily-roadmap/scripts/wily.py watch --once
Result: PASS command execution; exit 1 because T01 is ready, which is expected for status health semantics.
```

```text
rg -n "emit_board_live_event|wily-roadmap-v2|live-worked|board check|decompose-stage|wily run|wily-board" plugins/wily-roadmap -g '!**/docs/superpowers/**' -g '!*.pyc'
Result: PASS, no matches.
```

```text
rg -n "git fetch|fetch origin|subprocess.run\(\[\"git\", \"fetch\"" plugins/wily-roadmap/scripts/wily plugins/wily-roadmap/tests/v3
Result: PASS, no matches.
```

## v3 Unit Checkpoint

```text
python3 -m unittest discover -s plugins/wily-roadmap/tests/v3 -v
Result: PASS, 6 tests
```
