---
description: Check, migrate, or update the Wily plugin install
argument-hint: '[--check|--migrate|--yes]'
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Run the `wily-update` skill to check, migrate, or update the Wily plugin install.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py update [--check|--migrate|--yes]`. Keep remote actions approval-first. Zip-based installs must be migrated into a sibling git-managed install instead of patched in place. Git-managed installs must update only through a clean working tree and fast-forward-only pull.
