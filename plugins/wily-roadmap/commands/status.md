Run the `wily-status` skill with arguments: $ARGUMENTS.

Supports `--json` and `--ui auto|rich|ascii`.

Parent-owned coordination mode: with `.wily/coordination.yaml`, `wily status`
renders the parent task list and JSON includes `active_mode`. Manifest-only
workspace views remain under `wily workspace status`.

Status-style JSON includes `active_mode`. In parent-owned coordination mode,
`.wily/coordination.yaml` means the parent `.wily/tasks.yaml` is shown even when
the parent is not a Git repo; registered child repos remain work targets.
