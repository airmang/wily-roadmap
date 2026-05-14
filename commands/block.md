---
description: Mark a Wily phase blocked and record the reason
argument-hint: '<phase-id> [reason]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-block` skill to record a blocked phase with its reason.

The skill captures the blocking reason on the session and roadmap, then invokes `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py block <phase-id> <reason>`. If the user did not supply a reason, ask once before writing.

Arguments (phase id, then free-form reason):

$ARGUMENTS
