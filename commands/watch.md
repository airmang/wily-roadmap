---
description: Open a continuously refreshing Wily roadmap pane (vertical pipeline)
argument-hint: '[--here|--once|--ui rich|ascii|auto|--interval <seconds>|--install-ui]'
disable-model-invocation: true
allowed-tools: Bash, Read
---

Run the `wily-watch` skill to show a continuously refreshing `.wily` roadmap view.

This is read-only. Do not create sessions, change phase status, revise roadmap files, or implement phases. In tmux, open a split pane via `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py watch`; outside tmux, use the current interactive terminal as the live dashboard. In Codex app, prefer a side terminal running `./wily watch`. Pass the user's flags through verbatim.

User-supplied flags (may be empty):

$ARGUMENTS
