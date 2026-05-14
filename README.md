# Wily Roadmap

Wily is a local-first roadmap workflow plugin for agentic coding sessions.

## Install and Update

For first-time sharing, Wily can be sent as a zip bootstrap package. A zip install works locally, but it cannot pull future updates in place because it has no git metadata.

After installing a bootstrap zip, migrate once to a managed GitHub install:

```bash
./wily update --migrate
```

The migration creates a sibling `wily-roadmap-managed` directory and leaves the original zip directory unchanged.

For an install that is already git-managed, check for updates with:

```bash
./wily update --check
```

Apply an available update only when the working tree is clean:

```bash
./wily update --yes
```

Updates are explicit and approval-first. Wily does not check for updates in the background, does not patch zip installs in place, and only applies fast-forward git updates.

## Repo-Local Zsh Command

From the repository root, run Wily with the checked-in zsh launcher:

```bash
./wily status
./wily next
./wily watch
./wily watch --once --ui ascii
./wily update --check
```

`./wily watch` is the live roadmap dashboard. Inside tmux it opens a right-side split pane and targets the current `TMUX_PANE` when tmux exposes it. Outside tmux, including when working beside Codex app, run it in a side terminal and it will use that terminal directly.

For the styled Rich dashboard, install the optional watch UI dependency once:

```bash
./wily watch --install-ui
```

The launcher delegates to `scripts/wily.py` and keeps the current working directory as the target repository. It does not modify shell startup files, install aliases, touch PATH, contact remotes, or perform destructive actions by itself.

Use `python3 scripts/wily.py <command>` when a Python-only invocation is preferred.

Wily behavior stays local-first: remote or destructive work requires explicit user approval.
