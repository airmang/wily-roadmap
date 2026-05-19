# Wily Roadmap Marketplace

Git-backed Codex plugin marketplace for `wily-roadmap`.

## wily-roadmap v3

Project + flat goal-sized Task manager. See:

- Spec: `docs/superpowers/specs/2026-05-18-wily-redesign-design.md`
- Plan: `docs/superpowers/plans/2026-05-18-wily-roadmap-v3.md`

Run from this repo:

```bash
./wily watch
./wily next
```

## Install

```bash
codex plugin marketplace add airmang/wily-roadmap
```

Then install or enable `wily-roadmap` from the `Wily Castle` marketplace in Codex.

## Update

```bash
codex plugin marketplace upgrade wily-castle
```

## Layout

```text
.agents/plugins/marketplace.json
plugins/wily-roadmap/
```

The Codex plugin manifest lives at:

```text
plugins/wily-roadmap/.codex-plugin/plugin.json
```

## Repo-Local Command

From this repository root, run the local roadmap dashboard with:

```bash
./wily watch
```

The root launcher delegates to the plugin implementation under `plugins/wily-roadmap/`
and reads the current repository's `.wily/` state.

## v3 Manual Cleanup

After landing v3, remove stale local integration surfaces with explicit approval:

1. Edit `~/.codex/hooks.json` and remove any PostToolUse entry that invokes
   `plugins/wily-roadmap/scripts/wily.py live-worked` or another `live-*`
   command. v3 keeps `live-* --from-hook` non-blocking only so stale local hooks
   do not break Codex while you clean them up. Do not re-point those hooks to
   the moved `/Users/wilycastle/Code/projects/wily-plugin/...` plugin path;
   Wily Board v3 reflection comes from `wily-agent` snapshots and heartbeats.
2. Delete `~/.wily/board.json` if it exists; v3 ignores it.

The old repository workflow at `.github/workflows/wily-board-sync.yml` has been
removed. Current Wily Board v3 integration is local-agent based: `wily-agent`
watches `.wily/`, sends snapshots and heartbeats, and includes checkpoint
progress recorded through `wily cp`.
