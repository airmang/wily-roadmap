# Agent Compatibility

Wily is maintained as a Codex-discoverable plugin, but its workflow contract is agent-neutral.

## Command Entry Points

Use the `$wily-*` text commands as user-facing entrypoints.

In Codex, plugin discovery can map those commands to Wily skills under `skills/`.

In Claude Code, the same triggers are exposed as slash commands under `commands/*.md` (e.g. `/wily:init`, `/wily:status`, `/wily:watch`). Slash commands inherit the Claude plugin's namespace, so the Claude plugin is named `wily` (the Codex plugin keeps its formal `wily-roadmap` identity). The slash commands are thin shims that route to the matching skill under `skills/wily-*/SKILL.md`, which remains the source of truth for behavior. All slash commands are `disable-model-invocation: true` — only the user typing the command triggers them. Read the matching SKILL.md if slash command discovery is not available.

## Helper Invocation

Run `python3 <plugin-root>/scripts/wily.py <command>` for deterministic local state operations.

The helper script owns file creation, roadmap state transitions, session directories, and watch/status rendering. The active agent still owns repository inspection, user approval, phase design, planner selection, implementation, verification, and concise reporting.

## Boundaries

Keep Wily local-first and approval-first in every agent environment.

Do not push, open pull requests, merge, install remote integrations, delete user work, or run destructive commands unless the user explicitly approves that specific action.

Keep `.codex-plugin/plugin.json` and `skills/` compatible with Codex plugin discovery even when adding Claude Code guidance. Keep `.claude-plugin/plugin.json` and `commands/` compatible with Claude Code plugin discovery in parallel.
