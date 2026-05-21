---
name: wily-agent
description: Use when logging in, installing, configuring, checking, starting, stopping, or debugging the bundled Wily Roadmap Board sync daemon.
---

# Wily Agent

Manage the local `wily-agent` daemon bundled with Wily Roadmap. It watches
registered `.wily` repositories and sends best-effort Board v3 snapshots and
heartbeats to Wily Board when a rebuilt Board URL is configured. As of
2026-05-20, the local `wily-board` repo is deleted for a fresh rebuild, so
missing/unreachable Board service is an expected best-effort condition.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py agent <login|install|configure|register|unregister|start|stop|status|check|run|dev>
```

## Codex Command Usage

Users may invoke this skill through Codex plugin commands such as:

- `$wily-agent status`
- `$wily-agent login <one-time-code> --url https://rnwlab.duckdns.org --actor <actor-id>`
- `$wily-agent register --repo OWNER/REPO`
- `$wily-agent install`
- `$wily-agent start`
- `$wily-agent run --once --json`

When the user asks through `$wily-agent`, run the internal command from this
plugin directly. Do not ask the user to find the plugin root or manually type
`<plugin-root>/wily`. The skill exists so Codex can resolve the plugin root and
perform the local daemon action on the user's behalf.

## Behavior

- `login` exchanges a Board one-time code for a local machine token.
- `install` writes the macOS launchd plist.
- `configure` writes local Board URL, repo, actor, legacy secret, token, and interval config.
- `register` adds the current `.wily` repo to the local registry.
- `unregister` removes the current `.wily` repo from the local registry.
- `start` and `stop` manage the launchd daemon.
- `status` prints install, config, registry, and daemon state.
- `check` runs a smoke check and stays best-effort when not configured.
- `run` and `dev` run the foreground daemon path for debugging.
- Foreground and launchd runs publish Board v3 snapshots, heartbeats,
  status-board recovery metadata, and local sync-health state.
- Snapshot payloads use `board_v3_snapshot_v1`. Each snapshot includes current
  task, current checkpoint, checkpoint timeline, task list, dependencies, actor,
  and R-W-LAB remote-derived project id.
- Board display fields include current task, current checkpoint, checkpoint
  timeline, task list, dependencies, actor, R-W-LAB, and project id.
- All snapshots include `active_mode`; parent coordination snapshots use
  optional coordination fields such as `task_roadmap` and
  `claim_snapshot_summary`.

## Guardrails

- Keep the flow local-first and approval-first.
- Do not expose secrets in responses.
- Do not run production Board calls unless the user explicitly configured them.
- During the Board rebuild gap, prefer local/offline checks over login/register
  flows that require a live Board URL.
- Prefer `wily agent run --once --offline-ok` for smoke checks.
- For install/start/status requests, execute the command directly and report the result.

## Response Style

- Use Korean when the user is speaking Korean.
- Report concise status and the next action.
- Mention launchd and foreground paths when explaining installation.
