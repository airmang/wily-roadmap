---
description: Initialize Wily roadmap state for the current repository
argument-hint: '[final goal]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-init` skill to initialize Wily roadmap state in this repository.

If a final goal is supplied below, combine it with a repository scan when authoring the roadmap. If no goal is supplied, scan the repository first, summarize the current implementation baseline, and ask the user for the intended final outcome before creating any roadmap files.

The helper script is at `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py init`. The skill owns repository inspection, user approval, phase design, and planner selection.

User-supplied goal (may be empty):

$ARGUMENTS
