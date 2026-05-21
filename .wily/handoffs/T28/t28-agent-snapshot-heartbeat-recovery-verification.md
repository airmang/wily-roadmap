# Verification Evidence: T28 Agent Snapshot, Heartbeat, And Status Recovery

## Baseline

### Missing pytest

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_builds_board_v3_snapshot_payload_from_local_wily_state or cp_import_status_converts_custom_workflow_board_idempotently or agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent" -q
```

Result:

- Exit: 1
- Evidence: `/opt/homebrew/opt/python@3.14/bin/python3.14: No module named pytest`

### Pytest Installation

Command:

```bash
python3 -m pip install --user pytest
```

Result:

- Exit: 1
- Evidence: Homebrew Python PEP 668 externally-managed environment blocked normal install.

Command:

```bash
python3 -m pip install --user --break-system-packages pytest
```

Result:

- Exit: 0

## Post-Wily-Done Verification

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -q
```

Result:

- Exit: 0
- Evidence: `107 passed in 11.20s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q
```

Result:

- Exit: 0
- Evidence: `22 passed, 41 subtests passed in 0.29s`

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py doctor
```

Result:

- Exit: 0
- Evidence: `ok: pre-commit-hook: pre-commit hook runs wily drift guard`; `ok: venv: virtual environment present`

Command:

```bash
git diff --check
```

Result:

- Exit: 0
- Evidence: installed `pytest 9.0.3` plus dependencies into `/Users/wilycastle/Library/Python/3.14`.

### Focused Baseline

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_builds_board_v3_snapshot_payload_from_local_wily_state or cp_import_status_converts_custom_workflow_board_idempotently or agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent" -q
```

Result:

- Exit: 0
- Evidence: `3 passed, 91 deselected in 0.30s`

## Package Validation

Command:

```bash
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/t28-agent-snapshot-heartbeat-recovery-execution-package.md
```

Result:

- Exit: 0
- Evidence: `PASS: execution package contract is complete.`

## Review Evidence

### Plan Architect

Result:

- Verdict: REVISE
- Required revisions incorporated:
  - explicit snapshot schema
  - recovery-layer ledger precedence guard
  - strict module boundaries
  - status-board metadata preservation
  - explicit sync-health path, atomic writes, and pending retry marker
  - full token-mode heartbeat contract
  - full-core final verification

### Plan Critic

Result:

- Verdict: REVISE
- Required revisions incorporated:
  - debounce/fallback unit coverage
  - fail-update-reconnect-success test
  - ambiguous status-board warning coverage
  - ledger downgrade regression test
  - full-core final verification

### Parallel Planner

Result:

- Status: timed out and closed.
- Root decision retained: `SEQUENTIAL_RECOMMENDED`.
- Reason: snapshot, daemon, recovery, progress, client, and test files overlap; use subagents for read-only review/verification rather than parallel implementation.

### Post-Revision Validator

Command:

```bash
python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.11/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/t28-agent-snapshot-heartbeat-recovery-execution-package.md
```

Result:

- Exit: 0
- Evidence: `PASS: execution package contract is complete.`

### Final Package Hygiene

Command:

```bash
git diff --check -- agent-handoffs/t28-agent-snapshot-heartbeat-recovery-execution-package.md agent-handoffs/t28-agent-snapshot-heartbeat-recovery-progress.md agent-handoffs/t28-agent-snapshot-heartbeat-recovery-requirements.md agent-handoffs/t28-agent-snapshot-heartbeat-recovery-status.md agent-handoffs/t28-agent-snapshot-heartbeat-recovery-verification.md .wily/tasks.yaml .wily/tasks/T28/progress.jsonl
```

Result:

- Exit: 0
- Evidence: no whitespace errors.

## Final Verification

Superseded by the fresh final verification evidence at the end of this file.

## CP01 RED Contract Tests

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_client_posts_t26_heartbeat_payload_in_token_mode or agent_builds_board_v3_snapshot_payload_from_local_wily_state or agent_recovery_imports_missing_status_events_without_downgrading_ledger or agent_recovery_warns_and_imports_nothing_for_ambiguous_status_boards or agent_sync_health_records_failure_success_and_pending_snapshot or agent_daemon_records_failure_then_reconnect_sends_latest_snapshot or agent_daemon_debounces_wily_changes_and_sends_fallback_snapshots" -q
```

Result:

- Exit: 1
- Evidence: `7 failed, 93 deselected in 0.51s`
- Expected RED failures:
  - `KeyError: 'payload_version'`
  - `TypeError: publish_heartbeat() got an unexpected keyword argument 'payload'`
  - daemon snapshot publish times were `['initial', 0.0, 4.5]`, expected `['initial', 4.5, 16.0]`
  - `ModuleNotFoundError: No module named 'wily.agent.recovery'`
  - `ModuleNotFoundError: No module named 'wily.agent.sync_health'`

## CP02 Snapshot Identity And Timeline

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent_client_posts_t26_heartbeat_payload_in_token_mode or agent_builds_board_v3_snapshot_payload_from_local_wily_state or agent_recovery_imports_missing_status_events_without_downgrading_ledger or agent_recovery_warns_and_imports_nothing_for_ambiguous_status_boards or agent_sync_health_records_failure_success_and_pending_snapshot or agent_daemon_records_failure_then_reconnect_sends_latest_snapshot or agent_daemon_debounces_wily_changes_and_sends_fallback_snapshots" -q
```

Result:

- Exit: 0
- Evidence: `7 passed, 93 deselected in 0.64s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "snapshot or project_id or branch or heartbeat or checkpoint_timeline" -q
```

Result:

- Exit: 0
- Evidence: `8 passed, 92 deselected in 0.67s`

## CP03 Status-Board Recovery

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "custom_workflow_checkpoint_column" -q
```

Result:

- Exit: 1
- Evidence: `1 failed, 100 deselected`; `wily cp import-status` imported `CP01`/`CP02` rather than display checkpoint names from the Custom Workflow table.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "custom_workflow_checkpoint_column or import_status or status_board or recovery or cp_summary or ledger_precedence or ambiguous" -q
```

Result:

- Exit: 0
- Evidence: `8 passed, 93 deselected in 0.72s`

## CP04 Heartbeat And Sync Health

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent or heartbeat or sync_health or debounce or fallback or reconnect" -q
```

Result:

- Exit: 0
- Evidence: `18 passed, 83 deselected in 2.86s`

## CP05 Surface And Smoke

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -k "agent_command_and_skill_surface" -q
```

Result:

- Exit: 1
- Evidence: `1 failed, 21 deselected`; docs did not yet mention `status-board recovery`.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -k "agent_command_and_skill_surface" -q
```

Result:

- Exit: 0
- Evidence: `1 passed, 21 deselected in 0.01s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q
```

Result:

- Exit: 0
- Evidence: `22 passed, 41 subtests passed in 0.25s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -q
```

Result:

- Exit: 0
- Evidence: `101 passed in 10.35s`

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json
```

Result:

- Exit: 0
- Evidence: six registered repos were processed. Board responses were best-effort failures (`502` or broken pipe), and sync-health payloads recorded `last_failed_push`, `last_failure_reason`, and `pending_snapshot_sha` without failing the command.

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py doctor
```

Result:

- Exit: 1
- Evidence: local setup warnings only: missing pre-commit hook and missing virtual environment.

Local repair commands:

```bash
python3 plugins/wily-roadmap/scripts/wily.py replan install-pre-commit-hook
mkdir -p .venv
```

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py doctor
```

Result:

- Exit: 0
- Evidence: `ok: pre-commit-hook: pre-commit hook runs wily drift guard`; `ok: venv: virtual environment present`

## Review-Fix Regression Evidence

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "uses_non_empty_timestamp or ignores_non_checkpoint_status_tables or isolated_per_registered_repo or legacy_live_config or failed_debounced_snapshot or presence_is_idle or custom_workflow_checkpoint_column" -q
```

Result:

- Exit: 1 before fixes.
- Evidence: `7 failed, 100 deselected`; failures matched completion/integration review blockers.

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "uses_non_empty_timestamp or ignores_non_checkpoint_status_tables or isolated_per_registered_repo or legacy_live_config or failed_debounced_snapshot or presence_is_idle or custom_workflow_checkpoint_column" -q
```

Result:

- Exit: 0 after fixes.
- Evidence: `7 passed, 100 deselected in 0.93s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k "agent or heartbeat or sync_health or debounce or fallback or reconnect or recovery or import_status or status_board or custom_workflow_checkpoint_column or ignores_non_checkpoint" -q
```

Result:

- Exit: 0
- Evidence: `30 passed, 77 deselected in 4.16s`

Command:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily/agent/recovery.py plugins/wily-roadmap/scripts/wily/agent/daemon.py plugins/wily-roadmap/scripts/wily/progress.py plugins/wily-roadmap/scripts/wily/agent/snapshot.py
```

Result:

- Exit: 0

## Fresh Final Verification

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -q
```

Result:

- Exit: 0
- Evidence: `107 passed in 11.11s`

Command:

```bash
python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_surface.py -q
```

Result:

- Exit: 0
- Evidence: `22 passed, 41 subtests passed in 0.24s`

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json
```

Result:

- Exit: 0
- Evidence: six registered repos processed; Board unavailable states returned `502` or broken pipe while sync-health recorded per-repo pending snapshot/failure details and the command stayed non-blocking.

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py doctor
```

Result:

- Exit: 0
- Evidence: `ok: pre-commit-hook: pre-commit hook runs wily drift guard`; `ok: venv: virtual environment present`

Command:

```bash
git diff --check
```

Result:

- Exit: 0
