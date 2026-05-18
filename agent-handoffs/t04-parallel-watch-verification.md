# T04 Parallel Watch Verification

Verification evidence will be appended during checkpoints.

## 2026-05-18T14:49:06Z - Focused unittest suite

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 31 tests passed.

## 2026-05-18T14:53:03Z - Reviewer regression tests

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_watch_renderer_treats_missing_dependencies_as_waiting plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_watch_renderer_does_not_treat_capacity_hint_as_actor_capacity
```

Result: exit 0, 2 tests passed.

## 2026-05-18T14:53:03Z - Final focused unittest suite

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 33 tests passed.

## 2026-05-18T14:53:03Z - Python compile

Command:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily/models.py plugins/wily-roadmap/scripts/wily/ui/watch_render.py plugins/wily-roadmap/scripts/wily/ui/watch_activity.py
```

Result: exit 0.

## 2026-05-18T14:53:03Z - ASCII watch smoke

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Result: output rendered; exit 1 because Wily status returns 1 while T04 is still in progress.

## 2026-05-18T14:55:21Z - Final focused unittest suite after T04 done

Command:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core plugins.wily-roadmap.tests.v3.test_v3_surface
```

Result: exit 0, 33 tests passed.

## 2026-05-18T14:55:21Z - Final ASCII watch smoke after T04 done

Command:

```bash
python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii
```

Result: exit 0, output rendered with progress `4/4 · 100%`.
