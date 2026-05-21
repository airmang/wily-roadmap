# wily-agent

Use `wily agent` to install and manage the bundled Wily Board v3 sync daemon.
As of 2026-05-20, the local `wily-board` repo is deleted for a fresh rebuild;
login/register flows require a rebuilt Board URL.

In Codex, users can ask through the plugin command without knowing the plugin
filesystem path:

```text
$wily-agent status
$wily-agent install
$wily-agent start
```

Codex should resolve the plugin root and run the internal helper command.

Common commands:

```bash
wily agent check
wily agent login <one-time-code> --url https://board.example --actor wily
wily agent register --repo OWNER/REPO
wily agent install
wily agent start
wily agent status
wily agent stop
wily agent run --once --offline-ok
wily agent unregister
```

The daemon is local-first and best-effort. It publishes Board v3 snapshots and
heartbeats when logged in to a rebuilt Board. Missing config, Board downtime,
invalid tokens, the current Board rebuild gap, or legacy signature errors must
not fail normal Wily task commands.

The daemon treats registered repositories as read-only while syncing. Each
snapshot includes status-board recovery metadata from task-related Custom
Workflow boards, but daemon snapshot/heartbeat publishing must not backfill or
modify `.wily/tasks/*/progress.jsonl`. To write checkpoint backfill events, run
`wily cp <task-id> import-status <status-path>` explicitly.

Snapshots also include local sync-health fields for the last successful push,
last failure reason, and pending snapshot marker.

Board v3 snapshot payloads use `board_v3_snapshot_v1`. Each snapshot includes
current task, current checkpoint, checkpoint timeline, task list, dependencies,
actor, and R-W-LAB remote-derived project id. All snapshots include
`active_mode`; parent coordination snapshots use optional coordination fields
such as `task_roadmap` and `claim_snapshot_summary`.
