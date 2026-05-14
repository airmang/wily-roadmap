---
description: Summarize current Wily roadmap progress
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

Run the `wily-status` skill to summarize the current Wily roadmap.

This is read-only. Do not create sessions, change phase status, revise roadmap files, or implement phases. Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py status` to render the deterministic state summary, then report ready, in-progress, and blocked work concisely.
