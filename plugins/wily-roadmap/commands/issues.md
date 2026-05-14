---
description: Inspect optional GitHub issue linkage and propose roadmap connections
argument-hint: '[--add-to-roadmap]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-issues` skill to inspect GitHub issue linkage for this repository.

By default this is read-only — list linked and unlinked open issues via `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py issues`. Only run with `--add-to-roadmap` (and explicit user approval) when the user wants to fold issues into the roadmap. Remote calls require approval per Wily's local-first policy.

Flags (may be empty):

$ARGUMENTS
