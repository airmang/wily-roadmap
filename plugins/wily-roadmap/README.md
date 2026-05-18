# Wily Roadmap

Wily Roadmap v3 is a local-first Project + flat goal-sized Task manager for
agentic coding sessions.

## Commands

From the plugin root:

```bash
./wily status
./wily next
./wily claim T01
./wily go T01
./wily done T01
./wily watch --once
```

The launcher delegates to `scripts/wily.py` and keeps the current working
directory as the target repository. It does not modify shell startup files,
install aliases, touch PATH, contact remotes, or perform destructive actions by
itself.

## State

Wily v3 stores durable project state under `.wily/`:

- `project.md`
- `tasks.yaml`
- `actors.yaml`
- `tasks/<id>/progress.jsonl`
- `tasks/<id>/result.md`
- `archive/` for legacy snapshots

`wily init commit` also creates or updates concise Wily guidance in root
`AGENTS.md` and `CLAUDE.md`, preserving existing project-specific instructions.

## Custom Workflow

`wily go <id>` prints goal text for
`custom-workflow-skillset:plan-goal-runner`. Wily does not invoke external
runners directly.

## Safety

Wily behavior stays local-first. Remote or destructive work requires explicit
user approval. `wily land` asks before pushing unless the user separately handles
the push.
