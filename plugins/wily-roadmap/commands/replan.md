---
description: Revise the future Wily roadmap and increment its version
argument-hint: '[reason or summary of change]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-replan` skill to revise the future roadmap without rewriting completed history.

Only `pending` / `ready` / `blocked` phases may be reshaped. Completed phases stay intact; replaced or obsoleted phases must be marked `superseded` rather than deleted. Record the change in `revisions/` and invoke `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py replan <reason>` to bump the roadmap version.

Revision reason or summary (may be empty):

$ARGUMENTS
