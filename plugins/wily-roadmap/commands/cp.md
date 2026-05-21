Run the `wily-cp` skill with arguments: $ARGUMENTS.

Use `wily cp <task-id> start <cp-name>`, `wily cp <task-id> done <cp-name>`, `wily cp <task-id> note <cp-name> --note <text>`, or `wily cp <task-id> import-status .wily/handoffs/<task-id>/status.md` to write Wily checkpoint events into `.wily/tasks/<id>/progress.jsonl`.

Parent-owned coordination mode uses the parent `.wily/tasks.yaml` when
`.wily/coordination.yaml` exists. `wily cp import-status` imports into the
parent task progress ledger; status-style JSON exposes `active_mode`.

In parent-owned coordination mode, `.wily/coordination.yaml` keeps checkpoint
events on the parent task ledger. `wily cp import-status` imports status-board
events into the parent `.wily/tasks/<id>/progress.jsonl`; status-style JSON
views expose `active_mode`.
