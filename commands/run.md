---
description: Prepare a reference-only external workflow handoff without marking the phase done
argument-hint: '<phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-run` skill to prepare a reference-only external workflow handoff for the requested phase.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]` to prepare handoff artifacts. It must not mark the phase `done`; verified completion remains a later `/wily:complete <phase-id>` action. Keep remote and destructive actions approval-first in every autonomy mode.

Phase id and options:

$ARGUMENTS
