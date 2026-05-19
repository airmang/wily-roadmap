# Wily Board Reflection Fixes Verification

Verification evidence will be appended during execution.

## Final Evidence

### Roadmap Focused Tests

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m unittest \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_daemon_reloads_registry_each_tick \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent \
  plugins.wily-roadmap.tests.v3.test_v3_surface.V3SurfaceTest.test_readme_documents_v3_board_reflection_contract \
  plugins.wily-roadmap.tests.v3.test_v3_surface.V3SurfaceTest.test_plugin_manifest_and_readme_document_agent_onboarding
```

Result:

```text
Ran 5 tests in 0.098s

OK
```

### Board Agent Route Tests

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_agent_routes.py -q
```

Result:

```text
3 passed in 0.22s
```

### Roadmap V3 Full Isolated Tests

Command:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
WILY_AGENT_CONFIG=/private/tmp/wily-agent-test-config-empty.json \
WILY_AGENT_REGISTRY=/private/tmp/wily-agent-test-registry-empty.json \
WILY_AGENT_PLIST=/private/tmp/wily-agent-test.plist \
python3 -m unittest discover plugins/wily-roadmap/tests/v3
```

Result:

```text
Ran 104 tests in 6.165s

OK
```

Note: the same full suite without isolated Wily agent config reads the user's real configured agent and fails `test_agent_check_is_best_effort_without_configured_daemon` because `configured=true`; isolated config is the correct regression mode for that test.

### Agent Status

Command:

```bash
python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent status --json
```

Result:

```text
configured: true
daemon.running: true
registry paths include /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
```

### Agent Foreground Tick

Command:

```bash
python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json
```

Result:

```text
All registered repos were read. Board returned 401 invalid bearer token for snapshot and heartbeat sends. Each failure is now reported with sent=false.
```

### Active Old-Path Scan

Command:

```bash
rg -n '/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py|live-worked --from-hook' \
  /Users/wilycastle/.codex/hooks.json \
  /Users/wilycastle/Library/LaunchAgents/com.wily.roadmap.agent.plist \
  /Users/wilycastle/.config/wily/agent/registry.json
```

Result: no matches.

### Diff Whitespace

Command:

```bash
git -C /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap diff --check -- \
  README.md \
  plugins/wily-roadmap/README.md \
  plugins/wily-roadmap/scripts/wily/agent/client.py \
  plugins/wily-roadmap/tests/v3/test_v3_core.py \
  plugins/wily-roadmap/tests/v3/test_v3_surface.py \
  agent-handoffs/wily-board-reflection-fixes-execution-package.md \
  agent-handoffs/wily-board-reflection-fixes-status.md \
  agent-handoffs/wily-board-reflection-fixes-progress.md \
  agent-handoffs/wily-board-reflection-fixes-verification.md
git -C /Users/wilycastle/Code/projects/wily-plugin/wily-board diff --check -- docs/OPERATIONS.md
```

Result: no output; both exited 0.

## Planned Final Commands

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m unittest \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_daemon_reloads_registry_each_tick \
  plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent
```

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_agent_routes.py -q
```

```bash
python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent status --json
python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json
```

```bash
rg -n "/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py|live-worked --from-hook" \
  /Users/wilycastle/.codex/hooks.json \
  /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap \
  /Users/wilycastle/Code/projects/wily-plugin/wily-board
```
