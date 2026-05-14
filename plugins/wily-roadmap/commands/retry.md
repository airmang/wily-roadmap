---
description: Create the next Wily retry attempt for a phase, preserving previous sessions
argument-hint: '<phase-id>'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-retry` skill to start a new attempt for the requested phase.

The previous session is preserved as history; the new attempt becomes the current session. Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py retry <phase-id>` to create the attempt. Do not delete or rewrite previous session directories.

Phase id (required):

$ARGUMENTS
