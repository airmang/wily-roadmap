# T09 Verification

Verification evidence will be appended as checkpoints run.

## RED tests

- `python3 plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - Exit: 1
  - Expected failures: missing `commands/agent.md`, missing `skills/wily-agent`, manifest lacks `$wily-agent`.
- `python3 plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - Exit: 1
  - Expected failure: `ImportError` for missing `wily.cli.agent`.

## GREEN and Final Verification

- `python3 plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - Exit: 0
  - Result: 12 tests OK.
- `python3 plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - Exit: 0
  - Result: 51 tests OK.
- `python3 -m py_compile plugins/wily-roadmap/scripts/wily/cli/agent.py plugins/wily-roadmap/scripts/wily/agent/*.py`
  - Exit: 0
- `python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
  - Exit: 0
  - Result: 63 tests OK.
- `python3 plugins/wily-roadmap/scripts/wily.py agent check --offline`
  - Exit: 0
  - Evidence: installed true, configured false, daemon running false, registry path printed.
- `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
  - Exit: 0
  - Evidence: valid JSON status with installed/configured/registry/launchd/daemon fields.
- `python3 plugins/wily-roadmap/scripts/wily.py agent dev --once --offline-ok --json`
  - Exit: 0
  - Evidence: valid JSON with empty results for an empty registry.
