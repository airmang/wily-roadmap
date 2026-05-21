Run the `wily-done` skill with arguments: $ARGUMENTS

Scope drift reconciliation:
- By default, `wily done <id>` blocks when files changed since `claim_sha` are outside the task scope.
- Use `--add-scope` to add those files to the current task before marking it done.
- Use `--stub-drift` to create or reuse a `drift: <summary>` helper task and then mark the current task done.

Parent-owned coordination mode: with `.wily/coordination.yaml`, `wily done`
uses `claim_snapshot` fingerprints instead of parent `claim_sha` to report
repo-qualified scope changes such as `repo:src/file.py`; JSON includes
`active_mode`.

In parent-owned coordination mode, `.wily/coordination.yaml` makes `wily done`
compare current child repo dirty fingerprints against the task `claim_snapshot`.
Changed files are reported with repo-qualified scope such as `roadmap:src/app.py`;
status-style JSON views expose `active_mode`.
