---
name: wily-agent
description: Use when logging in, installing, configuring, checking, starting, stopping, or debugging the bundled Wily Roadmap Board sync daemon.
---

# Wily Agent

Manage the local `wily-agent` daemon bundled with Wily Roadmap. It watches
registered `.wily` repositories and sends best-effort Board v3 snapshots and
heartbeats to Wily Board.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py agent <login|install|configure|register|unregister|start|stop|status|check|run|dev>
```

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

## Guardrails

- Keep the flow local-first and approval-first.
- Do not expose secrets in responses.
- Do not run production Board calls unless the user explicitly configured them.
- Prefer `wily agent run --once --offline-ok` for smoke checks.

## Response Style

- Use Korean when the user is speaking Korean.
- Report concise status and the next action.
- Mention launchd and foreground paths when explaining installation.
