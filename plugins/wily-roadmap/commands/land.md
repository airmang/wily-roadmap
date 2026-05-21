Run the `wily-land` skill with arguments: $ARGUMENTS

Use `--include-ledger-closure` when the task landing commit must also include Wily ledger closure metadata that falls outside the task's normal scope, especially `.wily/tasks.yaml` and `.wily/tasks/<id>/result.md`.

Parent-owned coordination mode: when `.wily/coordination.yaml` exists, use
`wily land --dry-run <id>` first. Preflight uses `claim_snapshot` and
repo-qualified scope, reports parent ledger changes separately, blocks
out-of-scope and mixed files, supports `--include-mixed` and
`--include <repo:path>`, creates local-only per-child-repo commits after
preflight, and `--push is rejected`.

In parent-owned coordination mode, `.wily/coordination.yaml` enables local-only
multi-repo land. Use `wily land --dry-run <id>` to inspect preflight before any
staging. Preflight reports parent ledger changes separately, blocks parent
task artifacts when the parent is not Git, blocks out-of-scope child changes,
and classifies `pre_existing_dirty`, `task_candidate_changes`, and
`mixed_files` from `claim_snapshot` fingerprints. Mixed files block by default;
use `--include-mixed` or `--include <repo:path>` only when the mixed file should
belong to this task. `--push is rejected` in coordination mode; coordination
land is local-only and creates one local commit per touched registered child
repo with `Wily-Task: <id>`. In coordination mode, `--force` only bypasses the
done-status gate; it does not include out-of-scope or mixed files. Use
`--include-mixed` or `--include <repo:path>` for mixed files that belong to the
task.
