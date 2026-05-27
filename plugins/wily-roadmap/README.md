# Wily Roadmap

Wily Roadmap v3 is a local-first Project + flat goal-sized Task manager for
agentic coding sessions.

## Commands

From the plugin root:

```bash
./wily status
./wily next
./wily claim T01
./wily go T01
./wily done T01
./wily watch --once
./wily workspace status
./wily agent check
```

The launcher delegates to `scripts/wily.py` and keeps the current working
directory as the target repository. It does not modify shell startup files,
install aliases, touch PATH, contact remotes, or perform destructive actions by
itself.

## State

Wily v3 stores durable project state under `.wily/`:

- `project.md`
- `tasks.yaml`
- `actors.yaml`
- `tasks/<id>/progress.jsonl`
- `tasks/<id>/result.md`
- `archive/` for legacy snapshots

`wily init commit` also creates or updates concise Wily guidance in root
`AGENTS.md` and `CLAUDE.md`, preserving existing project-specific instructions.

## Custom Workflow

`wily go <id>` prints goal text for
`custom-workflow-skillset:plan-goal-runner`. Wily does not invoke external
runners directly.

## Hybrid Harness Workflow

Use the bundled `wily-hybrid-execute` Pi skill when a task should run through pi
`hybrid_run` instead of custom-workflow. The workflow claims the Wily task,
emits the `wily go` goal block, runs hybrid-harness with Wily acceptance and
scope as the source of truth, and records checkpoint progress explicitly with
`wily cp <task-id> start|done <cp-name>`.

If checkpoint calls were missed but a handoff status exists, recover with
`wily cp <task-id> import-status .wily/handoffs/<task-id>/status.md`. Mark the
task done only after hybrid-harness and required verification pass; land or push
only after explicit user approval.

## Workspace Manifest

Use `wily workspace` from a parent coordination directory when you want one
read-only view across multiple child Wily repos. The parent file can be
`wily-workspace.yaml` or `.wily-workspace.yaml`.

```yaml
schema: wily-workspace-v1
title: Wily Plugin Workspace
repos:
  - id: wily-roadmap
    path: ./wily-roadmap
  - id: wily-board
    path: ./wily-board
```

The manifest is not a source of truth; each child repo keeps its own
`.wily/tasks.yaml`. `wily workspace init` writes only the manifest and does not create parent `.wily/`.

Manifest-only mode provides read-only aggregate views. These views do not
claim, start, block, or complete child repo tasks, and missing or invalid child
repos are reported as per-repo errors. Parent-owned coordination mode is
separate: a parent `.wily/coordination.yaml` plus parent `.wily/tasks.yaml`
means the parent owns tasks while registered child Git repos own task files.
Manifest-only commands do not claim, start, block, or complete child repo tasks.
When both exist, `.wily/coordination.yaml` takes precedence for lifecycle
commands; `wily-workspace.yaml` remains a manifest-only view.

Coordination tasks can use repo-qualified scope such as `parent:docs/**` or
`wily-roadmap:src/**`, plus structured `{repo, path}` scope entries.
`wily claim` stores a `claim_snapshot` with each registered repo's branch, sha,
dirty files, and fingerprints. JSON project views expose `active_mode`.

In parent-owned coordination mode, `wily land --dry-run` is the preflight
surface. It reports parent ledger changes separately, blocks parent artifacts
when the parent is not Git, blocks out-of-scope or mixed files, supports
`--include-mixed` and `--include <repo:path>`, creates local-only child repo
commits after preflight, and `--push is rejected`.

Useful commands:

```bash
wily workspace init --repo wily-roadmap=./wily-roadmap --repo wily-board=./wily-board --title "Wily Plugin Workspace"
wily workspace show-config --json
wily workspace status --json
wily workspace next
wily workspace watch --once
```

## Parent-Owned Coordination Mode

Use parent-owned coordination mode when a parent directory owns the Wily task
ledger but one or more registered child Git repos contain the work. Add
`.wily/coordination.yaml` next to the parent `.wily/tasks.yaml`:

```yaml
schema: wily-coordination-v1
title: Parent Project
visibility:
  kind: collab
  owner: R-W-LAB
parent:
  id: parent
  path: .
repos:
  - id: roadmap
    path: ./wily-roadmap
  - id: board
    path: ./wily-board
```

`visibility` controls how Wily Board surfaces the parent workstream for logged-in
users. Use `kind: collab` for shared workspaces. Use `kind: personal` with a
GitHub `owner` for a parent coordination workspace that should be default-visible
only to that user. Existing manifests without `visibility` default to
`{kind: collab, owner: R-W-LAB}`.

Mode precedence is explicit: `.wily/coordination.yaml takes precedence` as
parent-owned coordination mode; `wily-workspace.yaml` and
`.wily-workspace.yaml` remain manifest-only read-only aggregate views and do not
create parent `.wily/`.

Parent-owned coordination mode uses repo-qualified scope such as
`parent:docs/**`, `roadmap:src/**`, or structured `{repo, path}` entries. Plain
legacy scope strings are treated as parent scope for compatibility.

In parent-owned coordination mode, parent `.wily/tasks.yaml` owns tasks and
child repos own work files. Board-facing agent snapshots still use
`board_v3_snapshot_v1`. Every snapshot includes top-level `active_mode`;
coordination is expressed as optional `coordination` fields instead of a new
payload type. Those optional fields include `task_roadmap`, normalized `scope`,
`target_repos`, `claim_snapshot_summary`, `changed_file_count`,
`changed_files_sample`, `visibility`, and display hints such as
`child_default_visibility` so Board can nest registered child repos under the
parent owner.

`wily claim` in coordination mode records a `claim_snapshot` instead of a fake
parent `claim_sha`. The snapshot includes each repo's branch, sha, dirty files,
and fingerprints for dirty or untracked files. `wily done` and `wily land`
compare later changes against those fingerprints.

`wily status --json` and `wily watch --json` include `active_mode`. `wily next
--json` includes `active_mode` in coordination mode. Commands run inside a
registered child repo that has its own `.wily/` use the child-local project.

`wily land --dry-run <id>` is the coordination preflight surface. It reports
parent ledger changes separately, blocks parent task artifacts when the parent
is not Git, blocks out-of-scope child changes before staging, and classifies
`pre_existing_dirty`, `task_candidate_changes`, and `mixed_files`. Mixed files
block by default; use `--include-mixed` or `--include <repo:path>` only when the
mixed file belongs to the task. `--push is rejected` in coordination mode:
coordination land is local-only and creates one local commit per touched
registered child repo with `Wily-Task: <id>`. In coordination mode, `--force` only bypasses the done-status gate; it does not include out-of-scope or mixed files.

## Wily Agent

The plugin includes the official bundled `wily-agent` daemon for Wily Board v3.
It watches registered `.wily` repositories, builds local-first task snapshots,
and sends best-effort snapshots and heartbeats to Wily Board when local config
is present. In the current coordination workspace, `wily-board` is expected to
be a separate sibling repository; Board sync is available once an approved Board
URL and machine registration are configured.

Wily Roadmap's repo-local `.wily/` ledger remains authoritative. Board v3 is a cache/reflection fed by `wily-agent` snapshots and heartbeats; Board state must not replace the Wily task lifecycle source of truth.

See [docs/board-coordination-ops.md](docs/board-coordination-ops.md) for the
coordination production evidence contract: OAuth is browser-only, machine
tokens are agent-only, raw secrets never enter evidence, snapshots and
heartbeats are best-effort local-first signals, and production-affecting actions
remain approval-first.

Agent snapshots use `board_v3_snapshot_v1`. Each snapshot includes `active_mode`,
current task, current checkpoint, checkpoint timeline, task list, dependencies,
actor, R-W-LAB remote-derived project id, stable checkout identity, branch/local
path, status-board recovery metadata, and local sync-health. The checkout
identity is a deterministic `checkout_<hash>` of the resolved git worktree path
and is sent as both `checkout_id` and `worktree_id` for Board display; it is not
part of `project_id`, so same-remote checkouts still converge to one Board
project. Heartbeats repeat the checkout id, branch, and local path so Board can
show active and stale checkouts using server ingest time. Parent coordination snapshots add optional `coordination`
fields with `task_roadmap`, `target_repos`, `claim_snapshot_summary`,
`changed_file_count`, `changed_files_sample`, `visibility`, and
`child_default_visibility`.

Typical onboarding:

```bash
wily agent check
wily agent login <one-time-code> --url https://board.example --actor wily
wily agent register --repo OWNER/REPO
wily agent install
wily agent start
wily agent status
```

For foreground smoke tests or development:

```bash
wily agent run --once --offline-ok
```

`wily agent stop` stops the macOS launchd daemon. `wily agent configure --secret`
remains available for legacy signed `/api/live/events` compatibility, but the
Board v3 path uses the token from `wily agent login` after the rebuilt Board
exists. Missing agent config, Board downtime, invalid tokens, or the current
Board rebuild gap are best-effort agent failures; normal Wily task commands
continue to use local `.wily/` state.

`live-*` commands are not a Wily Board v3 reflection mechanism. Stale local
hooks may still call `live-worked --from-hook`; v3 keeps that form as a no-op so
old Codex or Claude hook configuration does not break tool use while you remove
it. Do not re-point stale `live-*` hooks to this moved plugin path.

Custom Workflow does not update Wily checkpoints by itself. Use `wily cp
<task-id> start <cp-name>`, `wily cp <task-id> done <cp-name>`, or `wily cp
<task-id> import-status .wily/handoffs/<task-id>/status.md` to update the local
checkpoint ledger that `wily-agent` includes in snapshots.

## Safety

Wily behavior stays local-first. Remote or destructive work requires explicit
user approval. In single-repo mode, `wily land` asks before pushing unless the
user separately handles the push. In parent-owned coordination mode, `wily land`
is local-only and does not push.
