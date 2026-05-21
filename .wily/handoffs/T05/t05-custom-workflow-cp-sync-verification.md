# T05 Custom Workflow CP Sync Verification

## 2026-05-18T15:02:48Z - Baseline focused unittest suite

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 33 tests passed.

## 2026-05-18T15:07:39Z - Targeted cp tests

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_cp_command_records_progress_for_watch plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_cp_import_status_converts_custom_workflow_board_idempotently plugins.wily-roadmap.tests.v3.test_v3_surface.V3SurfaceTest.test_custom_workflow_checkpoint_contract_uses_wily_cp
```

Result: exit 0, 3 tests passed after initial RED failure for missing `wily cp` surface.

## 2026-05-18T15:07:39Z - Focused unittest suite

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 36 tests passed.

## 2026-05-18T15:07:39Z - Python compile

Command:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily/progress.py plugins/wily-roadmap/scripts/wily/cli/cp.py plugins/wily-roadmap/scripts/wily/cli/go.py
```

Result: exit 0.

## 2026-05-18T15:07:39Z - Watch smoke while T05 in progress

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Result: output rendered with T04 `체크포인트 [#####] 5/5` and T05 `체크포인트 [##-] 2/3 현재:implementation`; exit 1 because T05 remains in progress.

## 2026-05-18T15:12:06Z - Review fix targeted tests

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_cp_command_appends_distinct_notes_for_same_checkpoint plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_cp_cli_dispatch_records_progress
```

Result: exit 0, 2 tests passed.

## 2026-05-18T15:12:06Z - Focused unittest suite after review fix

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 38 tests passed.

## 2026-05-18T15:12:06Z - Watch smoke after review fix

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Result: output rendered with T04 `체크포인트 [#####] 5/5` and T05 `체크포인트 [###-] 3/4 현재:final-verification`; exit 1 because T05 remains in progress.

## 2026-05-18T15:13:12Z - Final focused unittest suite after T05 done

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 38 tests passed.

## 2026-05-18T15:13:12Z - Final ASCII watch smoke after T05 done

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Result: exit 0, output rendered with progress `5/5 · 100%`, T04 `체크포인트 [#####] 5/5`, and T05 `체크포인트 [####] 4/4`.
