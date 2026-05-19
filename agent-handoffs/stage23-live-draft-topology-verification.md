# Stage 23 Live Draft Topology Verification

Verification evidence will be appended as commands are run.

## Checkpoint 1

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_emits_board_live_draft_when_configured plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_warns_when_board_live_config_missing plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_warns_when_board_live_draft_send_fails
```

Result: `Ran 3 tests ... OK`.

## Checkpoint 2

```sh
uv run pytest tests/test_db.py::test_upsert_live_draft_stage_decomposition tests/test_db.py::test_replace_repo_state_clears_matching_live_draft_when_durable_phases_arrive tests/test_db.py::test_replace_repo_state_keeps_live_draft_when_stage_has_no_durable_phases -q
uv run pytest tests/test_live_events.py::test_live_event_accepts_stage_decomposition_draft tests/test_live_events.py::test_live_event_rejects_stage_decomposition_draft_without_phases tests/test_live_events.py::test_live_event_rejects_stage_decomposition_draft_phase_without_title -q
```

Result: `3 passed`; `3 passed`.

## Checkpoint 3

```sh
uv run pytest tests/test_web_routes.py::test_repo_detail_renders_live_draft_phase_rows tests/test_web_routes.py::test_repo_detail_prefers_durable_phases_over_live_draft_rows tests/test_web_routes.py::test_board_renders_live_draft_follow_up -q
```

Result: `3 passed, 3 warnings`.

## Checkpoint 4

```sh
uv run pytest tests/test_db.py::test_upsert_live_draft_stage_decomposition tests/test_db.py::test_replace_repo_state_clears_matching_live_draft_when_durable_phases_arrive tests/test_db.py::test_replace_repo_state_keeps_live_draft_when_stage_has_no_durable_phases tests/test_live_events.py::test_live_event_accepts_stage_decomposition_draft tests/test_live_events.py::test_live_event_rejects_stage_decomposition_draft_without_phases tests/test_live_events.py::test_live_event_rejects_stage_decomposition_draft_phase_without_title tests/test_web_routes.py::test_repo_detail_renders_live_draft_phase_rows tests/test_web_routes.py::test_repo_detail_prefers_durable_phases_over_live_draft_rows tests/test_web_routes.py::test_board_renders_live_draft_follow_up tests/test_operations_doc.py -q
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_emits_board_live_draft_when_configured plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_warns_when_board_live_config_missing plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_from_json_warns_when_board_live_draft_send_fails
```

Result: `10 passed, 3 warnings`; `Ran 3 tests ... OK`.

## Final Verification

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest
```

Result: `Ran 89 tests in 5.943s ... OK`.

```sh
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
```

Result: `69 passed, 26 warnings in 1.73s`.

```sh
python3 plugins/wily-roadmap/scripts/wily.py status
python3 plugins/wily-roadmap/scripts/wily.py next
rg -n "id: \"s23\"|status: \"done\"|depends_on: \\[\"s23\"\\]" .wily/roadmap.yaml .wily/stages/s23-wily-board-live-draft-topology-overlay/stage.yaml
```

Result:

- `wily status` exits 0 and shows Stage 21 as the current next Stage.
- `wily next` reports `Next stage: s21 - Wily Board UI redesign`, `Depends on: s23`.
- grep evidence shows `.wily/roadmap.yaml` has `s23` with `status: "done"` and `s21` depends on `s23`.
- grep evidence shows `23-1` through `23-5` all have `status: "done"`.
