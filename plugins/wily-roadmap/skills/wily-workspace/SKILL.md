---
name: wily-workspace
description: Use when the user asks for $wily-workspace or wants manifest-only multi-repo Wily status from a parent coordination directory.
---

# Wily Workspace

Show or create a parent workspace manifest for multiple child Wily repos.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py workspace <init|show-config|status|next|watch> [args]
```

## Behavior

- The manifest can be `wily-workspace.yaml` or `.wily-workspace.yaml`.
- The manifest is not a source of truth; each child repo keeps its own `.wily/tasks.yaml`.
- `wily workspace init` writes only the manifest and does not create parent `.wily/`.
- `wily workspace status` and `wily workspace next` are read-only aggregate views
  and do not claim, start, block, or complete child repo tasks.
- `wily workspace status` shows per-repo progress, active tasks, ready tasks, blocked tasks, and per-repo errors.
- `wily workspace next` aggregates ready tasks without claiming them.
- `wily workspace watch --once` prints one aggregate snapshot; without `--once`, it redraws when child `.wily/.touch` files change.
- Missing or invalid child repos should be reported as per-repo errors, not as a reason to create parent Wily state.
- Mode precedence: `.wily/coordination.yaml takes precedence` as parent-owned
  coordination mode; `wily-workspace.yaml` and `.wily-workspace.yaml` remain
  manifest-only views.
- Parent-owned coordination mode is not manifest-only. The parent `.wily/tasks.yaml`
  owns tasks, child repos are work targets, repo-qualified scope uses
  `parent:docs/**`, `roadmap:src/**`, or `{repo, path}`, and status-style JSON
  exposes `active_mode`.
- `wily-workspace.yaml` / `.wily-workspace.yaml` is manifest-only mode.
- Parent-owned coordination mode is separate and active when
  `.wily/coordination.yaml` exists; that file takes precedence for lifecycle
  commands.
- Coordination mode parent tasks may use repo-qualified scope, `claim_snapshot`,
  and JSON `active_mode`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the requested workspace output or concise answer.
- Avoid implying that the parent manifest owns task status.
- Do not echo internal helper commands in normal user-facing responses.
