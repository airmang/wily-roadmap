Run the `wily-workspace` skill with arguments: $ARGUMENTS.

Supports `init`, `show-config`, `status`, `next`, and `watch`.

The workspace manifest can be `wily-workspace.yaml` or `.wily-workspace.yaml`.
The manifest is not a source of truth; child repos keep their own `.wily/tasks.yaml`.

`wily workspace status` and `wily workspace next` are read-only aggregate views
and do not claim, start, block, or complete child repo tasks. Missing or invalid
child repos are reported as per-repo errors.

`wily workspace init` writes only the manifest and does not create parent `.wily/`.

Mode precedence: `wily-workspace.yaml` / `.wily-workspace.yaml` is
manifest-only mode and the manifest is not a source of truth. If parent
`.wily/coordination.yaml` exists, parent-owned coordination mode takes
precedence for lifecycle commands; parent tasks may use repo-qualified scope,
`claim_snapshot`, and JSON `active_mode`.

Mode precedence:
- `.wily/coordination.yaml` takes precedence as parent-owned coordination mode.
- `wily-workspace.yaml` and `.wily-workspace.yaml` remain manifest-only views.

Parent-owned coordination mode is not manifest-only: the parent `.wily/tasks.yaml`
owns tasks, child repos are registered work targets, repo-qualified scope uses
forms like `parent:docs/**`, `roadmap:src/**`, or `{repo, path}`, and
status-style JSON exposes `active_mode`.
