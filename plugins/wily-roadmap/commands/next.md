---
description: Show the next ready Wily roadmap phase
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

Run the `wily-next` skill to surface the next executable phase.

This is read-only. Do not create sessions, change phase status, revise roadmap files, or implement phases. Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py next` to compute the ready phase, then report its id, title, dependencies, recommended planner, and the `$wily-start <phase-id>` (or `/wily:start <phase-id>`) follow-up the user can run.
