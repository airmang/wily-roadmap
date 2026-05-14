---
description: Mark a Wily phase done and verify its session
argument-hint: '<phase-id>'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-complete` skill to finish the requested phase.

Approval is required before flipping a phase to `done`. The skill verifies the phase's session (verification commands, handoff notes) before invoking `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py complete <phase-id>`. Do not remove or rewrite completed history.

Phase id (required):

$ARGUMENTS
