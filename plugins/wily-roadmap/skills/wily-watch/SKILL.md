---
name: wily-watch
description: Use when the user types $wily-watch for a continuously refreshing Wily v3 project pane.
---

# Wily Watch

Render a live task snapshot, including actor lane, blocker text, cp progress, parallel-ready lanes, dependency waiting, advisory scope conflict warnings, and worker capacity.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py watch [--once|--here|--interval N] [--ui auto|rich|ascii] [--compact] [--show-timeline] [--hide-log]
```

## Behavior

- Read-only: does not mutate `.wily/`.
- `--once` prints one snapshot and exits.
- In tmux, `wily watch` opens a right-side pane and runs the live view there.
- `--here` runs the live view in the current terminal.
- `--ui auto` uses Rich styling when available, including repo-local `.venv-watch`; `--ui ascii` forces plain ASCII.
- `--compact` forces single-column compact layout even in wide terminals.
- `--show-timeline` expands checkpoint bars into named checkpoint timelines (e.g. `plan › design › [verify] › deploy`).
- `--hide-log` suppresses the observed commits log panel.
- In a terminal wider than 120 cols, the watch pane shows a Tasks (left) + Activity (right) side-by-side layout.
- Task rows include metadata when space allows: `done` timestamps, `claimed` timestamps, and pending `depends_on` chains.
- Ready tasks with satisfied dependencies are shown under `병렬 가능`; ready tasks with unfinished dependencies are shown under `의존 대기`.
- Parallel hints use optional task metadata: `parallel_lane`, `priority`, and `capacity_hint`.
- Scope overlap is advisory only. Phrase it as `scope conflict` / `충돌 가능`, never as an automatic safety guarantee.
- Worker capacity is displayed as `작업자 여력` and should be treated as a scheduling signal, not a lock.
- Parent-owned coordination mode is active when `.wily/coordination.yaml`
  exists. Watch renders the parent task list, JSON includes `active_mode`, and
  repo-qualified scope keeps child repo paths unambiguous.
- `watch --json` forwards status-style JSON including `active_mode`.
- In parent-owned coordination mode, `.wily/coordination.yaml` makes watch render
  the parent task ledger while child repos stay work targets.

## Korean UI

- Prefer Korean labels for visible watch UI, including `병렬 가능`, `의존 대기`, `작업자 여력`, and `충돌 가능`.
- Keep ASCII fallback readable without relying on emoji or box-drawing glyphs.
- When adding warnings, use recommendation language; do not claim that watch prevents merge conflicts or enforces exclusive access.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Do not echo internal helper commands in normal user-facing responses.
