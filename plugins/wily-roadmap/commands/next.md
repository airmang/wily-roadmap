Run the `wily-next` skill with arguments: $ARGUMENTS

Parent-owned coordination mode: with `.wily/coordination.yaml`, `wily next`
reads the parent task list and JSON wraps the selected task with `active_mode`.
Commands run inside a registered child repo with its own `.wily/` use that
child-local project.

In parent-owned coordination mode, `.wily/coordination.yaml` keeps `wily next`
on the parent task ledger. JSON output includes `active_mode` and a parent task
payload. Commands run inside a registered child repo with its own `.wily/` use
that child-local project instead.
