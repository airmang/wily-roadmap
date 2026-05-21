Run the `wily-claim` skill with arguments: $ARGUMENTS

Parent-owned coordination mode: when `.wily/coordination.yaml` exists,
`wily claim <id>` claims the parent task without requiring the parent to be a
Git repo. It records `claim_snapshot` with each registered repo's branch, sha,
dirty files, and fingerprints. Repo-qualified scope such as `repo:src/**` is
preserved.

In parent-owned coordination mode, `.wily/coordination.yaml` makes the parent
`.wily/tasks.yaml` the task source of truth while registered child repos provide
work targets. `wily claim` records a `claim_snapshot` instead of a parent
`claim_sha`; each repo snapshot includes `branch`, `sha`, dirty files, and
fingerprints for dirty or untracked files. JSON output exposes the same task
data; status-style views expose `active_mode`.
