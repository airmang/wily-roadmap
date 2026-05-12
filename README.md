# Wily Roadmap

Wily is a local-first roadmap workflow plugin for agentic coding sessions.

## Repo-Local Zsh Command

From the repository root, run Wily with the checked-in zsh launcher:

```bash
./wily status
./wily next
./wily watch
./wily watch --once --ui ascii
```

The launcher delegates to `scripts/wily.py` and keeps the current working directory as the target repository. It does not modify shell startup files, install aliases, touch PATH, contact remotes, or perform destructive actions by itself.

Use `python3 scripts/wily.py <command>` when a Python-only invocation is preferred.

Wily behavior stays local-first: remote or destructive work requires explicit user approval.
