Run the `wily-watch` skill with arguments: $ARGUMENTS.

Supports `--once`, `--here`, `--interval N`, and `--ui auto|rich|ascii`.

Inside tmux, `wily watch` opens a right-side live pane by default.

Korean UI guidance: watch output should keep user-visible labels in Korean, including `병렬 가능`, `의존 대기`, `작업자 여력`, and advisory `scope conflict` text such as `충돌 가능`.

Parent-owned coordination mode: with `.wily/coordination.yaml`, `wily watch`
uses the parent task list, includes `active_mode` in JSON, and still treats
scope conflict text as advisory. Repo-qualified scope keeps child repo paths
unambiguous.

`watch --json` forwards status-style JSON including `active_mode`. In
parent-owned coordination mode, `.wily/coordination.yaml` makes watch render the
parent task ledger while child repos stay work targets.
