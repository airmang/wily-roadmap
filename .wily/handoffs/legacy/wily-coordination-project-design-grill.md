# Design Grill: Wily Parent-Owned Coordination Project

Date: 2026-05-21
Source context: follow-up from `/Users/wilycastle/Code/projects/hwpx` P6 landing failure.

## Problem

The existing `wily workspace` implementation does not match the desired multi-repo coordination model.

Current implemented model:
- `wily-workspace.yaml` / `.wily-workspace.yaml` is manifest-only.
- Parent directory should not have `.wily/`.
- Each child repo keeps its own `.wily/tasks.yaml`.
- Workspace commands are read-only aggregate `status`, `next`, and `watch`.
- `claim`, `done`, `cp`, and `land` still assume a single Wily project rooted in a Git repo.

Desired model:
- Parent coordination directory owns `.wily/tasks.yaml`.
- A task can span multiple child repos.
- Parent `.wily` is the task lifecycle source of truth.
- Child repos are work targets.
- `land` can create one local commit per task-scoped touched repo.

The concrete failing case:
- `/Users/wilycastle/Code/projects/hwpx` has parent `.wily/tasks.yaml`.
- Its child repos are `python-hwpx`, `hwpx-mcp-server`, and `hwpx-skill`.
- Parent is not a Git repo.
- P6 produced parent-scoped artifacts under `.wily/baselines`, `.wily/reports`, and `agent-handoffs`.
- `wily claim P6` failed because it tried `git rev-parse HEAD` at the parent.
- `wily land P6` could not commit because the source-of-truth parent is not a Git repo.

## Resolved Model

Use **Parent-Owned Coordination Project + Multi-Commit Land**.

### Source Of Truth

Decision: parent-owned `.wily`.

- Parent `.wily/tasks.yaml` is the source of truth.
- Child repos do not need their own Wily tasks for a parent-owned coordination task.
- Child repos are registered as coordination targets.
- A task may touch parent artifacts and multiple child repos.

Rejected alternative:
- Manifest-only child-owned workspace is still useful, but it is a different mode. It should remain read-only aggregate behavior.

### Modes

Decision: dual mode.

1. Manifest-only workspace mode:
   - Config files: `wily-workspace.yaml` or `.wily-workspace.yaml`.
   - No parent `.wily/`.
   - Existing read-only aggregate behavior remains.

2. Parent-owned coordination mode:
   - Config file: `.wily/coordination.yaml`.
   - Parent `.wily/tasks.yaml` is source of truth.
   - `claim`, `done`, `cp`, `status`, `next`, and `watch` operate against parent tasks.
   - Child repos are used for scope resolution, diff classification, and `land`.

3. If both configs exist:
   - `.wily/coordination.yaml` takes precedence.
   - `wily-workspace.yaml` remains view/import compatibility.
   - CLI should show the active mode clearly.

## Configuration

Use `.wily/coordination.yaml` for parent-owned mode.

Example:

```yaml
schema: wily-coordination-v1
title: HWPX Stack
parent:
  id: parent
  path: .
repos:
  - id: python-hwpx
    path: python-hwpx
    role: library
  - id: hwpx-mcp-server
    path: hwpx-mcp-server
    role: mcp
  - id: hwpx-skill
    path: hwpx-skill
    role: skill
land:
  policy: preflight-then-commit
  commit_unit: task-scoped-touched-repo
  push: never
```

## Scope Model

Decision: hybrid compatibility.

Accepted YAML forms:

```yaml
scope:
  - parent:.wily/baselines/P6-template-formfit-baseline
  - parent:agent-handoffs/p6-template-formfit-baseline-status.md
  - hwpx-mcp-server:src/hwpx_mcp_server
  - python-hwpx:tests/template_automation
  - repo: hwpx-skill
    path: examples/08_mcp_template_formfit.md
```

Internal normalized representation:

```json
{
  "repo": "hwpx-mcp-server",
  "path": "src/hwpx_mcp_server"
}
```

Rules:
- `repo_id:path` is explicit repo scope.
- `parent:path` is parent coordination scope.
- Structured `{repo, path}` is accepted.
- Existing plain path remains supported for backward compatibility.
- In coordination mode, plain path should warn because ownership is ambiguous.
- Repo ids come from `.wily/coordination.yaml`.

## Claim Snapshot

Decision: record a repo snapshot map, not a single `claim_sha`.

Use a new field, preserving old single-repo compatibility:

```yaml
claim_snapshot:
  parent:
    sha: abc123
    branch: main
    dirty: true
    changed:
      - .wily/tasks.yaml
      - agent-handoffs/foo.md
  hwpx-mcp-server:
    sha: 789abc
    branch: codex/hwpx-proposal-tools
    dirty: true
    changed:
      - src/hwpx_mcp_server/server.py
      - tests/test_quality_generation_pipeline.py
```

Rules:
- Existing `claim_sha: <sha>` remains valid in single-repo mode.
- Coordination mode uses `claim_snapshot` first.
- Snapshot includes parent and all registered child repos by default.
- Dirty repos are allowed.
- Dirty state and changed files are recorded at claim time.

## Dirty Policy

Decision: allow dirty repos at claim time, but record them.

Classification at `done` / `land`:
- Files dirty at claim time: `pre_existing_dirty`.
- Files newly changed after claim: `task_candidate_changes`.
- Files dirty at claim and changed again: `mixed_files`.

Safety:
- `mixed_files` are not automatically staged.
- User must explicitly include mixed files, for example with `--include-mixed` or explicit file selection.
- This avoids overwriting or silently absorbing unrelated user work.

## Land Policy

Decision: preflight then commit.

Preflight:
- Classify changes by repo.
- Resolve task scope by normalized repo/path entries.
- Check parent/child repo Git state.
- Check branch and remote metadata where relevant.
- Check untracked/staged/dirty/mixed files.
- Check that every candidate file is task-scoped.
- If anything is ambiguous, stop before creating any commit.

Commit:
- After preflight passes, create one local commit per task-scoped touched repo.
- Parent is treated as repo id `parent`.
- Every commit includes the same trailer:

```text
Wily-Task: <id>
```

Commit unit:
- `task-scoped touched repo` only.
- If a repo has changes but none are task-scoped, do not commit it.
- If out-of-scope changes would be required, block.

Example P6 commits:

```text
parent:
  Complete P6 coordination baseline

hwpx-mcp-server:
  Add P6 form-fit fixture support
```

## Parent Git Policy

Decision: `land` requires a Git repo only when a commit is needed there.

Rules:
- `claim`, `done`, `cp`, `status`, `next`, and `watch` must work even if parent is not a Git repo.
- `land` requires parent Git repo if parent-scoped changes exist.
- Do not auto-run `git init`.
- If parent-scoped changes exist and parent is not Git, block with a clear message:
  - parent coordination artifacts exist,
  - parent is not a Git repo,
  - initialize parent repo or configure a coordination repo before land.
- If only child repos are task-scoped and touched, child repo land may proceed without parent Git.

## Publish Policy

Decision: keep remote work separate for now.

- `wily land` creates local commits only.
- It does not push.
- It does not open PRs.
- Push/PR creation should be separate future work, likely `wily publish <task-id>`.
- Long-term: add a parent bundle report that links all repo PRs for one Wily task.

## Required Implementation Areas

Likely files:
- `plugins/wily-roadmap/scripts/wily/coordination.py`
- `plugins/wily-roadmap/scripts/wily/scope.py`
- `plugins/wily-roadmap/scripts/wily/observation.py`
- `plugins/wily-roadmap/scripts/wily/cli/claim.py`
- `plugins/wily-roadmap/scripts/wily/cli/done.py`
- `plugins/wily-roadmap/scripts/wily/cli/land.py`
- `plugins/wily-roadmap/scripts/wily/cli/status.py`
- `plugins/wily-roadmap/scripts/wily/cli/next.py`
- `plugins/wily-roadmap/scripts/wily/cli/watch.py`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- relevant command docs and skills.

Compatibility constraints:
- Do not break existing single-repo Wily behavior.
- Do not break existing manifest-only `wily workspace` behavior.
- Make active mode explicit in CLI output or JSON.

## Acceptance Scenarios

1. Parent-owned non-Git lifecycle:
   - Directory has `.wily/tasks.yaml` and `.wily/coordination.yaml`.
   - Parent is not a Git repo.
   - `wily claim T1` succeeds and records `claim_snapshot`.
   - `wily done T1` succeeds after verification.

2. Parent-scoped land without parent Git:
   - Task touches `parent:.wily/reports/...`.
   - Parent is not Git.
   - `wily land T1` blocks with a clear parent Git requirement.

3. Child-only land:
   - Task scope includes only `child-repo:src/...`.
   - Parent is not Git.
   - Child repo is Git.
   - `wily land T1` can create the child commit after preflight.

4. Multi-repo land:
   - Task scope includes `parent:agent-handoffs/...`, `wily-roadmap:plugins/...`, and `wily-board:app/...`.
   - Parent and both child repos are Git repos.
   - Preflight passes.
   - `wily land T1` creates one commit per touched scoped repo.

5. Dirty baseline:
   - Child repo is dirty before claim.
   - Claim records dirty file list.
   - Later land classifies pre-existing, new, and mixed files.
   - Mixed files block unless explicitly included.

6. Existing manifest-only workspace:
   - Directory only has `wily-workspace.yaml`.
   - No parent `.wily/`.
   - `wily workspace status/next/watch` continue to work.
   - `claim/done/land` do not treat the parent manifest as task source of truth.

## Open Questions

- Exact `claim_snapshot` YAML migration strategy for old tasks with string `claim_sha`.
- Whether `done` should update old `claim_sha` field for display compatibility.
- Exact CLI flags for mixed files: `--include-mixed`, explicit `--include repo:path`, or both.
- Whether a parent coordination repo can be configured outside the current parent path.
- Whether `wily land --dry-run` should be introduced as the preflight report surface.

## Recommended Next Step

Create a `plan-goal-runner` execution package from this design and implement in `wily-roadmap`.

Suggested slug:
- `wily-parent-coordination-mode`

Suggested first checkpoint:
- Add failing tests for parent-owned non-Git `claim`, coordination scope parsing, and `land` preflight blocking when parent-scoped changes exist without parent Git.
