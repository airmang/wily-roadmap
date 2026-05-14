# Wily Watch — Vertical Pipeline UI Design

## Purpose

`$wily-watch` shows a continuously refreshing, read-only view of the `.wily` roadmap, intended to live in a side pane while doing CLI work. The current renderer (`ascii_watch_output` / `rich_watch_output` in `scripts/wily.py`) stacks a heavy header, a verbose `Stage N:` flow with `의존:` / `^--` / `|` noise, and a bottom block that repeats the same phases — it scans poorly and isn't pleasant to leave open.

This redesign replaces the watch renderer with a **vertical pipeline**: a single-column, `git log --graph`-style view where the graph *is* the list. Each phase is one line carrying its status glyph, id, title, and unmet dependencies; the left rail shows the dependency structure. It targets a narrow, tall pane (the existing default `tmux split-window -h`), shows the whole roadmap at a glance, and degrades cleanly when the structure or the pane won't allow the rail.

Scope: the **watch UI only**. The Codex-facing `wily_state_summary.summarize_roadmap` output and `phase_flow_lines` / `phase_node_line` / `phase_detail_lines` are unrelated and stay as they are. No new CLI flags; the pane command (`split-window -h`, `--here`, `--once`, `--interval`, `--ui`, `--install-ui`) is unchanged.

## Layout

Top to bottom, no surrounding box — just two thin dim rules framing the graph:

```
 Wily Roadmap · v2                       ⟳ 2s
 ▕████████████░░░░░░░░░░░░▏  3/6 · 50%
 ─────────────────────────────────────────────
 ● 01    Settle Korean response-style update
 │
 ● 02    Harden command skill consistency
 │
 ● 03    Korean stage-based DAG status output
 ├──▶ 04-1  Improve init roadmap authoring
 ├──▶ 04-2  Harden lifecycle status CLI
 ▼
 ○ 05    Plugin discovery & release polish   ⟂ 04-1 04-2
 ─────────────────────────────────────────────
 git: 20 changed · wily-roadmap · ^C to stop
```

Chrome is 5 rows (header line, progress line, two rules, footer line). Everything else is the graph.

## Status glyphs and styles

| status | glyph (rich) | rich style | glyph (ascii) |
|---|---|---|---|
| done | `●` | green dim | `*` |
| ready (executable: `ready`, or `pending` with all deps `done`) | `▶` | bold cyan | `>` |
| in_progress | `◐` | bold yellow | `~` |
| needs_review | `◆` | magenta | `?` |
| blocked | `✗` | bold red | `x` |
| pending | `○` | dim | `o` |
| superseded | `⊘` | dim | `-` |

"Ready" overrides "pending": a `pending` phase whose dependencies are all `done` renders as `▶` (matches the existing `wily_state_summary.executable_phases` logic).

Rail glyphs (rich → ascii): `│` → `|`, `├──` → `+--`, `▼` → `v`, `▾` → `v`. Bar: `█` → `#`, `░` → `-`, `▕`/`▏` → `[`/`]`. Rule `─` → `-`. `⟳` → `~`. Ellipsis `…` → `...`. The existing three-line "Rich UI is not installed / Run: $wily-watch --install-ui / Fallback: using ASCII watch UI." preamble is preserved when rich was requested (`--ui rich` or `auto`) but unavailable.

## The vertical pipeline graph

### Row order

Topological: compute stage numbers via `wily_state_summary.phase_stage_map`, then order phases by `(stage, original index)`.

### When the rail is drawn

The fancy rail is drawn only when the roadmap decomposes into an alternating sequence of **single phase → group (≥1) → single phase → …**, where:

- the first stage is a single phase (or, if not, multiple roots are tolerated — see below);
- every member of a group has `depends_on` exactly equal to `[id of the preceding single phase]`;
- the single phase following a group has `depends_on` exactly equal to the set of ids of that group.

A group of size 1 is just a linear link. This matches roadmaps produced by `wily init` (a backbone with occasional parallel splits/merges). Anything else — many-to-many between stages, skip-level edges, disconnected sub-DAGs — is **not pipeline-renderable** and uses the flat-list fallback (below).

Multiple roots (stage 1 has ≥2 phases): rendered as consecutive plain node lines, then continue with the alternating pattern from there if it holds; otherwise fall back.

### Rail rendering (rich/unicode form)

- **Root node:** ` ● 01    <title>` — node line, no connector before it.
- **Linear successor** (group of 1 depending on the single previous node): a connector line ` │`, then the node line ` <glyph> <id>    <title>`.
- **Fan-out group** (≥2 members depending on the single previous node): each member on its own line as ` ├──<glyph> <id>  <title>`. (The first `├` visually attaches to the previous node; all members use `├──` uniformly.)
- **Fan-in node** (the single node depending on all members of the immediately preceding fan-out group): a connector line ` ▼`, then the node line.

### Node line format

```
 <glyph> <id><pad>  <title…>[   ⟂ <unmet-dep ids>]
```

- `<id>` left-padded to the width of the widest id so titles align.
- `<title…>` truncated with `…` to fit the terminal width after the rail prefix, glyph, id, and spacing.
- `⟂ <ids>` lists only dependencies that are **not** `done` (the ones still blocking). Shown for `pending` and `blocked` phases; omitted for `done`, `ready`, `in_progress` (their deps are satisfied or irrelevant). If the line plus `⟂ …` overflows the width, the deps move to a continuation line indented under the title.

### Done collapsing (height adaptation)

`available_rows = size.lines − 5` (the chrome). `--once` / non-tty uses `shutil.get_terminal_size((80, 24))` like everything else, so it is deterministic.

- If the rendered rows fit `available_rows`: render everything (default — the user wants the full roadmap visible).
- Otherwise: collapse the **leading run of consecutive `done` phases** into one dim line ` ● <n> phases done ▾` (and drop the `│` connectors among them). Non-done phases are always shown in full. If it still overflows after that, allow tmux to clip the top — no further heroics.

(An always-collapse-done mode could be a flag later; out of scope now.)

## Fallback: flat stage list

Used when the structure is not pipeline-renderable, **or** the width is too small for a sensible rail (< ~28 cols). Same node-line format, no rail, `Stage N` dim rules as separators (` · parallel` suffix when the stage has > 1 phase):

```
 Stage 1 ──────────────────────────────
 ● 01   Settle Korean response-style update
 Stage 2 ──────────────────────────────
 ● 02   Harden command skill consistency
 Stage 3 ──────────────────────────────
 ● 03   Korean stage-based DAG status output
 Stage 4 · parallel ───────────────────
 ▶ 04-1  Improve init roadmap authoring
 ▶ 04-2  Harden lifecycle status CLI
 Stage 5 ──────────────────────────────
 ○ 05   Plugin discovery & release polish   ⟂ 04-1 04-2
```

Done collapsing applies the same way (collapse a leading run of all-done stages into ` ● <n> phases done ▾`).

## Header, progress, footer

- **Header line:** left `Wily Roadmap · v<roadmap_version>`; right, padded to the terminal width, `⟳ <interval>s` (interval formatted compactly: `2s`, `1.5s`). No `goal` line (it lives in `project.md`).
- **Progress line:** ` ▕<bar>▏  <done>/<total> · <pct>%`. Bar width = `clamp(width // 3, 10, 28)`, drawn with `█` (filled, green) and `░` (empty, dim) — a plain styled string, no `rich.progress` machinery. `pct` rounded to nearest integer. No `next →` (the first `▶` glyph in the graph already marks it).
- **Rules:** ` ─` × width, dim — one below the progress line, one above the footer.
- **Footer line:** ` git: <state> · <repo-basename> · ^C to stop`, dim. `<state>` is `<n> changed`, `clean`, or `—` when not a git repo (reuse `wily_state_summary.git_status`, condensed). `<repo-basename>` is `root.name`. ` · ^C to stop` is always appended (small, no separate row).

## Edge and error cases (all through one `render` entry point)

- **No `.wily/`:** ` Wily — no roadmap` + ` run $wily-init to start` (dim) + footer git line. No progress bar, no graph.
- **`.wily/` exists, no `roadmap.yaml`:** same, message ` .wily found, no roadmap.yaml`.
- **`roadmap.yaml` parses to 0 phases:** header + ` ▕░░░░▏  0/0` + ` (no phases yet)` (dim) + footer.
- **Width < ~24 cols:** one line — ` Wily v<ver> · <done>/<total> done` (+ git appended if it still fits).
- **Roadmap with `superseded` phases:** they appear inline with the `⊘` glyph in their stage position like any other status; no special section.

## Code structure

- **New module `scripts/wily_watch_ui.py`:**
  - `STATUS_GLYPHS` / `STATUS_GLYPHS_ASCII`, rail-glyph maps.
  - `render_watch(root: Path, *, interval: float, rich: bool, size: os.terminal_size | tuple[int, int] | None = None) -> str` — returns the full text block, with Rich ANSI styles when `rich=True`, plain text otherwise. `size` defaults to `shutil.get_terminal_size((80, 24))`; injectable for tests.
  - Internal helpers, each producing a list of styled lines (a small internal `Line` of `(text, style)` spans so there is one code path, serialized to a recording `rich.console.Console(...).export_text(styles=True)` when `rich`, or joined plain otherwise): `_load`, `_pipeline_segments` (returns `None` when not pipeline-renderable), `_graph_lines`, `_flat_lines`, `_collapse_leading_done`, `_header_line`, `_progress_line`, `_rule`, `_footer_line`, `_node_line`, `_truncate`.
  - Reuses `wily_state_summary`: `executable_phases`, `phase_stage_map`, `stage_groups`, `status_counts`, `phase_index`, `phases_with_status`, `git_status`. No changes to `wily_state_summary`.
- **`scripts/wily.py`:**
  - Replace `ascii_watch_output` and `rich_watch_output` with calls to `wily_watch_ui.render_watch`. `watch_output(root, interval, ui)` becomes: `rich = ui != "ascii" and rich_available()`; `body = render_watch(root, interval=interval, rich=rich)`; prepend the existing "Rich not installed" three-line preamble when `ui` in `{"auto", "rich"}` and `not rich`. Delete the now-dead `status_overview` helper (its logic moves into `wily_watch_ui`).
  - `tmux_watch_command`, `command_watch`, `command_watch_pane`, `command_install_watch_ui`, the `--here` refresh loop, and all CLI parsing are unchanged.
- **`skills/wily-watch/SKILL.md`:** small wording update — describe the vertical pipeline view; drop the now-inaccurate "ASCII `Phase 흐름:`" line. No behavior changes.

## Testing (`tests/test_wily_cli.py`)

Drive everything through `wily.py watch --once --ui ascii` (deterministic, no ANSI) with a temp `.wily/roadmap.yaml`; control size via `COLUMNS` / `LINES` env (honored by `shutil.get_terminal_size`).

1. **Linear** (A→B→C): output has `|` rail connectors, glyphs and titles in topological order, no `+--`.
2. **Fan-out + fan-in** (the current 6-phase shape): has `+--` lines for `04-1` and `04-2`, a `v` connector before `05`, and `⟂ 04-1 04-2` on the `05` line.
3. **Complex DAG** (e.g. `05` also depends on `02` — a skip-level edge): falls back to the flat list — `Stage 1` header present, no `+--` rail.
4. **Narrow** (`COLUMNS=20`): the one-line form.
5. **Height-constrained** (`LINES=8`, several leading `done` phases): leading-done collapse line (`* N phases done`) present; every non-done phase still present.
6. **No `.wily/`:** "no roadmap" message, exit 0.
7. **0 phases:** "(no phases yet)".
8. **Rich smoke** (`--ui rich`, `pytest.importorskip("rich")`): non-empty, contains every phase id once styles are stripped.

Reconcile/replace any existing watch assertions in `tests/test_wily_cli.py` that reference the old `Phase 흐름:` / `Stage N:` headers or `[01 완료]` bracket format — those strings go away.

## Out of scope / possible follow-ups

- `--collapse-done` flag to always collapse the leading done run.
- A `goal` line in the header.
- A horizontal "strip" layout (`--layout strip`) for wide short panes.
- Showing `current_session` / attempt counts per phase.
- Coloring the git footer by clean vs dirty.
