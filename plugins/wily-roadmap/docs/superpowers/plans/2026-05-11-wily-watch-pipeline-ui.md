# Wily Watch Vertical Pipeline UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `$wily-watch` pane renderer with a `git log --graph`-style vertical pipeline view that shows the whole roadmap at a glance and degrades cleanly when the structure or pane size won't allow the rail.

**Architecture:** A new pure module `scripts/wily_watch_ui.py` exposes `render_watch(root, *, interval, rich, size=None) -> str`. It loads the roadmap via the existing `wily_state_summary`, builds an internal list of styled lines (`list[list[tuple[str, str]]]` — text + Rich style), and serializes them either to Rich-styled ANSI (recording `rich.console.Console` + `export_text`) or to plain text. `scripts/wily.py`'s `watch_output()` calls it; the old `ascii_watch_output` / `rich_watch_output` / `status_overview` are deleted. The Codex-facing `wily_state_summary.summarize_roadmap` is untouched.

**Tech Stack:** Python 3 stdlib; `rich` (optional, already in `requirements-watch.txt`, installed into `.venv-watch` by `$wily-watch --install-ui`); `unittest` for tests.

**Reference:** Spec at `docs/superpowers/specs/2026-05-11-wily-watch-pipeline-ui-design.md`.

**Notes / minor deviations from the spec:**
- The fallback to the flat stage list triggers when the structure is not pipeline-renderable **or** `width < 28`. Width `< 24` always wins and produces the one-line form.
- "Pipeline-renderable" is detected from stage groups (simpler than per-edge analysis): (1) every stage-1 phase has no deps; (2) every phase in stage `S≥2` depends on exactly the set of ids in stage `S-1`; (3) no two consecutive stages both have size > 1.

---

## File structure

- **Create `scripts/wily_watch_ui.py`** — the whole renderer. One responsibility: turn a repo path into the watch text block. ~250–300 lines.
- **Create `tests/test_wily_watch_ui.py`** — direct unit tests of `wily_watch_ui` (imports the module; fast, covers all branches).
- **Modify `scripts/wily.py`** — `watch_output()` delegates to `wily_watch_ui.render_watch`; delete `ascii_watch_output`, `rich_watch_output`, `status_overview`; keep the "Rich UI is not installed" preamble. Nothing else changes (CLI parsing, tmux pane command, refresh loop all stay).
- **Modify `tests/test_wily_cli.py`** — rewrite the four `watch ... --once` content assertions for the new output; the tmux/`--install-ui`/no-tmux tests are unchanged.
- **Modify `skills/wily-watch/SKILL.md`** — reword the "Behavior" bullets to describe the vertical pipeline view; drop the now-inaccurate `Phase 흐름:` line.

---

## Task 1: Scaffold `wily_watch_ui.py` — constants, `_truncate`, `_emit`, stub `render_watch`

**Files:**
- Create: `scripts/wily_watch_ui.py`
- Create: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test**

`tests/test_wily_watch_ui.py`:

```python
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wily_watch_ui  # noqa: E402


class TruncateAndEmitTest(unittest.TestCase):
    def test_truncate_short_string_unchanged(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abc", 10), "abc")

    def test_truncate_long_string_gets_ellipsis(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abcdefgh", 5), "abcd…")

    def test_truncate_tiny_limit(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abcdef", 1), "…")
        self.assertEqual(wily_watch_ui._truncate("abcdef", 0), "")

    def test_emit_plain_joins_spans_and_strips_trailing_space(self) -> None:
        lines = [[(" hello", ""), ("   ", "")], [(" world", "bold")]]
        self.assertEqual(wily_watch_ui._emit(lines, rich=False, width=20), " hello\n world")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wily_watch_ui'`.

- [ ] **Step 3: Write `scripts/wily_watch_ui.py`**

```python
#!/usr/bin/env python3
"""Render the Wily roadmap watch pane as a vertical pipeline."""

from __future__ import annotations

import re
import shutil
from io import StringIO
from pathlib import Path
from typing import Any

import wily_state_summary

Phase = dict[str, Any]
Span = tuple[str, str]   # (text, rich style; "" = no style)
Line = list[Span]

GLYPHS = {
    "done": "●", "ready": "▶", "in_progress": "◐", "needs_review": "◆",
    "blocked": "✗", "pending": "○", "superseded": "⊘",
}
GLYPHS_ASCII = {
    "done": "*", "ready": ">", "in_progress": "~", "needs_review": "?",
    "blocked": "x", "pending": "o", "superseded": "-",
}
STYLES = {
    "done": "green dim", "ready": "bold cyan", "in_progress": "bold yellow",
    "needs_review": "magenta", "blocked": "bold red", "pending": "dim",
    "superseded": "dim",
}
RAIL = {"link": "│", "branch": "├──", "merge": "▼", "fold": "▾",
        "full": "█", "empty": "░", "lo": "▕", "ro": "▏", "dep": "⟂", "refresh": "⟳"}
RAIL_ASCII = {"link": "|", "branch": "+--", "merge": "v", "fold": "v",
              "full": "#", "empty": "-", "lo": "[", "ro": "]", "dep": "needs", "refresh": "~"}

CHROME_ROWS = 5            # header, progress, top rule, bottom rule, footer
MIN_WIDTH_ONELINE = 24     # below this: single-line form
MIN_WIDTH_RAIL = 28        # below this: flat fallback instead of the rail


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit == 1:
        return "…"
    return text[: limit - 1].rstrip() + "…"


def _emit(lines: list[Line], *, rich: bool, width: int) -> str:
    if not rich:
        return "\n".join("".join(t for t, _ in line).rstrip() for line in lines)
    from rich.console import Console, Group
    from rich.text import Text

    texts = []
    for line in lines:
        rendered = Text(no_wrap=True, overflow="crop")
        for text, style in line:
            rendered.append(text, style=style or None)
        texts.append(rendered)
    console = Console(file=StringIO(), record=True, width=width,
                      force_terminal=True, color_system="truecolor")
    console.print(Group(*texts))
    return console.export_text(styles=True).rstrip("\n")


def render_watch(root: Path, *, interval: float, rich: bool,
                 size: tuple[int, int] | None = None) -> str:
    cols, rows = size if size is not None else tuple(shutil.get_terminal_size((80, 24)))
    return ""   # filled in by later tasks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: scaffold pipeline UI module"
```

---

## Task 2: `_phase_status`, `_unmet_deps`, `_node_line`

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_wily_watch_ui.py`:

```python
class NodeLineTest(unittest.TestCase):
    def _phases(self):
        return [
            {"id": "01", "title": "Settle Korean response-style update", "status": "done", "depends_on": []},
            {"id": "02", "title": "Harden command skill consistency", "status": "in_progress", "depends_on": ["01"]},
            {"id": "04-1", "title": "Improve init roadmap authoring", "status": "pending", "depends_on": ["03"]},
            {"id": "03", "title": "Korean stage-based DAG status output", "status": "done", "depends_on": ["02"]},
        ]

    def test_status_ready_when_deps_done(self) -> None:
        phases = self._phases()
        # 04-1 depends on 03 (done) -> executable -> "ready"
        self.assertEqual(wily_watch_ui._phase_status(phases[2], {"04-1"}), "ready")

    def test_status_from_field_otherwise(self) -> None:
        phases = self._phases()
        self.assertEqual(wily_watch_ui._phase_status(phases[1], set()), "in_progress")

    def test_unmet_deps_lists_non_done(self) -> None:
        phases = self._phases()
        by_id = {str(p["id"]): p for p in phases}
        self.assertEqual(wily_watch_ui._unmet_deps({"depends_on": ["01", "02"]}, by_id), ["02"])
        self.assertEqual(wily_watch_ui._unmet_deps({"depends_on": ["01"]}, by_id), [])

    def test_node_line_plain_done(self) -> None:
        phases = self._phases()
        by_id = {str(p["id"]): p for p in phases}
        line = wily_watch_ui._node_line(phases[0], set(), by_id, prefix=" ", id_width=4, width=60, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertTrue(text.startswith(" * 01"))
        self.assertTrue(text.endswith("Settle Korean response-style update"))

    def test_node_line_pending_shows_unmet_deps(self) -> None:
        phases = self._phases()
        by_id = {str(p["id"]): p for p in phases}
        # mark 03 not done so 04-1 has a genuinely unmet dependency
        by_id["03"]["status"] = "pending"
        line = wily_watch_ui._node_line(phases[2], set(), by_id, prefix=" +--", id_width=4, width=80, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertTrue(text.startswith(" +--o 04-1  Improve init roadmap authoring"))
        self.assertIn("needs 03", text)

    def test_node_line_truncates_title(self) -> None:
        phases = self._phases()
        by_id = {str(p["id"]): p for p in phases}
        line = wily_watch_ui._node_line(phases[0], set(), by_id, prefix=" ", id_width=2, width=20, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertLessEqual(len(text), 20)
        self.assertTrue(text.endswith("…"))
```

> Note: `_node_line`'s `prefix` already includes the leading space. For a fan-out member `prefix=" +--"`, the glyph follows immediately → ` +--o 04-1` (the ascii `ready` glyph is `>`, giving ` +--> ...`; here the status is `pending`, so the glyph is `o`). For a plain node `prefix=" "` → ` * 01`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.NodeLineTest -v`
Expected: FAIL — `AttributeError: module 'wily_watch_ui' has no attribute '_phase_status'`.

- [ ] **Step 3: Implement** — add to `scripts/wily_watch_ui.py` (after `_emit`):

```python
def _phase_index(phases: list[Phase]) -> dict[str, Phase]:
    return {str(p.get("id")): p for p in phases if p.get("id") is not None}


def _phase_status(phase: Phase, ready_ids: set[str]) -> str:
    if str(phase.get("id")) in ready_ids:
        return "ready"
    return str(phase.get("status", "pending"))


def _unmet_deps(phase: Phase, by_id: dict[str, Phase]) -> list[str]:
    out = []
    for dep in phase.get("depends_on") or []:
        target = by_id.get(str(dep))
        if target is None or target.get("status") != "done":
            out.append(str(dep))
    return out


def _node_line(phase: Phase, ready_ids: set[str], by_id: dict[str, Phase], *,
               prefix: str, id_width: int, width: int, ascii_: bool) -> Line:
    status = _phase_status(phase, ready_ids)
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    glyph = glyphs.get(status, "?")
    style = STYLES.get(status, "")
    pid = str(phase.get("id", "?"))
    title = str(phase.get("title", "Untitled phase"))

    head = f"{prefix}{glyph} {pid.ljust(id_width)}  "
    dep_text = ""
    if status in {"pending", "blocked"}:
        unmet = _unmet_deps(phase, by_id)
        if unmet:
            marker = RAIL_ASCII["dep"] if ascii_ else RAIL["dep"]
            dep_text = f"   {marker} " + " ".join(unmet)
    avail = max(4, width - len(head) - len(dep_text))
    title = _truncate(title, avail)
    line: Line = [(prefix, "dim"), (glyph, style), (f" {pid.ljust(id_width)}  ", style), (title, "")]
    if dep_text:
        line.append((dep_text, "dim"))
    return line
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: phase status + node line rendering"
```

---

## Task 3: `_RoadmapView` + `_load`

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append:

```python
def _write_roadmap(project: Path, body: str) -> None:
    state = project / ".wily"
    state.mkdir(parents=True, exist_ok=True)
    (state / "roadmap.yaml").write_text(body, encoding="utf-8")


class LoadTest(unittest.TestCase):
    def test_load_none_without_wily_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            view = wily_watch_ui._load(Path(tmp))
            self.assertIsNone(view.roadmap)
            self.assertFalse(view.has_state)

    def test_load_none_roadmap_when_state_exists_without_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".wily").mkdir()
            view = wily_watch_ui._load(Path(tmp))
            self.assertTrue(view.has_state)
            self.assertIsNone(view.roadmap)

    def test_load_parses_phases_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_roadmap(Path(tmp), "\n".join([
                'roadmap_version: 2',
                'phases:',
                '  - id: "01"',
                '    title: "A"',
                '    status: "done"',
                '    depends_on: []',
                '  - id: "02"',
                '    title: "B"',
                '    status: "pending"',
                '    depends_on: ["01"]',
            ]))
            view = wily_watch_ui._load(Path(tmp))
            self.assertEqual(view.version, 2)
            self.assertEqual(len(view.phases), 2)
            self.assertEqual(view.done, 1)
            self.assertEqual(view.total, 2)
            self.assertEqual({str(p["id"]) for p in view.ready}, {"02"})  # deps done
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.LoadTest -v`
Expected: FAIL — `AttributeError: module 'wily_watch_ui' has no attribute '_load'`.

- [ ] **Step 3: Implement** — add to `scripts/wily_watch_ui.py`:

```python
from dataclasses import dataclass, field


@dataclass
class _RoadmapView:
    root: Path
    has_state: bool
    roadmap: dict[str, Any] | None
    phases: list[Phase] = field(default_factory=list)
    ready: list[Phase] = field(default_factory=list)
    by_id: dict[str, Phase] = field(default_factory=dict)

    @property
    def version(self) -> Any:
        return (self.roadmap or {}).get("roadmap_version", "unknown")

    @property
    def ready_ids(self) -> set[str]:
        return {str(p.get("id")) for p in self.ready}

    @property
    def total(self) -> int:
        return len(self.phases)

    @property
    def done(self) -> int:
        return sum(1 for p in self.phases if p.get("status") == "done")


def _load(root: Path) -> _RoadmapView:
    state_dir = root / ".wily"
    roadmap_path = state_dir / "roadmap.yaml"
    if not roadmap_path.exists():
        return _RoadmapView(root=root, has_state=state_dir.exists(), roadmap=None)
    roadmap = wily_state_summary.parse_roadmap(wily_state_summary.read_text(roadmap_path))
    phases = roadmap.get("phases") or []
    ready = wily_state_summary.executable_phases(phases)
    return _RoadmapView(root=root, has_state=True, roadmap=roadmap,
                        phases=phases, ready=ready, by_id=_phase_index(phases))
```

(Move the `from dataclasses import ...` line up to the other imports at the top of the file when implementing.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: roadmap view loader"
```

---

## Task 4: `_pipeline_renderable` + `_graph_lines`

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append:

```python
class GraphTest(unittest.TestCase):
    linear = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "ready", "depends_on": ["02"]},
    ]
    fan = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "done", "depends_on": ["02"]},
        {"id": "04-1", "title": "D1", "status": "pending", "depends_on": ["03"]},
        {"id": "04-2", "title": "D2", "status": "pending", "depends_on": ["03"]},
        {"id": "05", "title": "E", "status": "pending", "depends_on": ["04-1", "04-2"]},
    ]
    skip = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "done", "depends_on": ["02"]},
        {"id": "05", "title": "E", "status": "pending", "depends_on": ["03", "01"]},
    ]
    two_wide = [
        {"id": "a1", "title": "A1", "status": "done", "depends_on": []},
        {"id": "a2", "title": "A2", "status": "done", "depends_on": []},
        {"id": "b1", "title": "B1", "status": "pending", "depends_on": ["a1", "a2"]},
        {"id": "b2", "title": "B2", "status": "pending", "depends_on": ["a1", "a2"]},
    ]

    def test_renderable_true_for_linear_and_fan(self) -> None:
        self.assertTrue(wily_watch_ui._pipeline_renderable(self.linear))
        self.assertTrue(wily_watch_ui._pipeline_renderable(self.fan))

    def test_not_renderable_for_skip_level_or_consecutive_wide(self) -> None:
        self.assertFalse(wily_watch_ui._pipeline_renderable(self.skip))
        self.assertFalse(wily_watch_ui._pipeline_renderable(self.two_wide))

    def test_graph_lines_linear_uses_link_rail(self) -> None:
        lines = wily_watch_ui._graph_lines(self.linear, set(), width=60, ascii_=True)
        rendered = ["".join(t for t, _ in line) for line in lines]
        self.assertEqual(rendered[0], " * 01  A")
        self.assertEqual(rendered[1], " |")
        self.assertEqual(rendered[2], " * 02  B")
        self.assertEqual(rendered[3], " |")
        self.assertTrue(rendered[4].startswith(" > 03  C"))

    def test_graph_lines_fan_uses_branch_and_merge(self) -> None:
        lines = wily_watch_ui._graph_lines(self.fan, set(), width=70, ascii_=True)
        rendered = ["".join(t for t, _ in line) for line in lines]
        self.assertTrue(any(r.startswith(" +--o 04-1") and r.endswith("D1") for r in rendered))
        self.assertTrue(any(r.startswith(" +--o 04-2") and r.endswith("D2") for r in rendered))
        self.assertIn(" v", rendered)
        self.assertTrue(any(r.lstrip().startswith("o 05") and "needs 04-1 04-2" in r for r in rendered))
```

> Note: `_graph_lines` returns the body lines only (no header/footer/rules). ASCII `ready` glyph is `>`, `pending` is `o`, `done` is `*`. For `04-1`/`04-2` whose status is `pending` and dep `03` is `done`, they are executable → would be `ready` if `ready_ids` included them; here `ready_ids` is `set()` so they render `pending` (`o`). The first member of a fan-out attaches to `+--` → ` +--o 04-1` (or ` +--> 04-1` when the phase is in `ready_ids`).

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.GraphTest -v`
Expected: FAIL — `AttributeError: ... '_pipeline_renderable'`.

- [ ] **Step 3: Implement** — add to `scripts/wily_watch_ui.py`:

```python
def _ordered_stages(phases: list[Phase]) -> list[list[Phase]]:
    grouped = wily_state_summary.stage_groups(phases)
    return [grouped[k] for k in sorted(grouped)]


def _pipeline_renderable(phases: list[Phase]) -> bool:
    if not phases:
        return False
    stages = _ordered_stages(phases)
    for i, stage in enumerate(stages):
        if i == 0:
            if any(p.get("depends_on") for p in stage):
                return False
            continue
        prev_ids = {str(p.get("id")) for p in stages[i - 1]}
        for p in stage:
            if {str(d) for d in (p.get("depends_on") or [])} != prev_ids:
                return False
        if len(stage) > 1 and len(stages[i - 1]) > 1:
            return False
    return True


def _id_width(phases: list[Phase]) -> int:
    return max((len(str(p.get("id"))) for p in phases), default=2)


def _graph_lines(phases: list[Phase], ready_ids: set[str], *, width: int, ascii_: bool) -> list[Line]:
    rail = RAIL_ASCII if ascii_ else RAIL
    by_id = _phase_index(phases)
    idw = _id_width(phases)
    stages = _ordered_stages(phases)
    lines: list[Line] = []
    for i, stage in enumerate(stages):
        wide = len(stage) > 1
        prev_wide = i > 0 and len(stages[i - 1]) > 1
        if i == 0:
            for p in stage:
                lines.append(_node_line(p, ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_))
        elif wide:
            for p in stage:
                lines.append(_node_line(p, ready_ids, by_id, prefix=f" {rail['branch']}", id_width=idw, width=width, ascii_=ascii_))
        elif prev_wide:
            lines.append([(f" {rail['merge']}", "dim")])
            lines.append(_node_line(stage[0], ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_))
        else:
            lines.append([(f" {rail['link']}", "dim")])
            lines.append(_node_line(stage[0], ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_))
    return lines
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: vertical pipeline graph rendering"
```

---

## Task 5: `_flat_lines` (fallback stage list)

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append:

```python
class FlatTest(unittest.TestCase):
    def test_flat_lines_have_stage_headers_and_parallel_suffix(self) -> None:
        lines = wily_watch_ui._flat_lines(GraphTest.fan, set(), width=70, ascii_=True)
        rendered = ["".join(t for t, _ in line) for line in lines]
        self.assertTrue(rendered[0].startswith(" Stage 1 "))
        self.assertTrue(any(r.startswith(" Stage 4 ") and "parallel" in r for r in rendered))
        self.assertTrue(any(r.startswith(" * 01") and r.endswith("A") for r in rendered))
        self.assertTrue(any(r.lstrip().startswith("o 05") and "needs 04-1 04-2" in r for r in rendered))
        self.assertFalse(any(r.lstrip().startswith("+--") for r in rendered))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.FlatTest -v`
Expected: FAIL — `AttributeError: ... '_flat_lines'`.

- [ ] **Step 3: Implement** — add to `scripts/wily_watch_ui.py`:

```python
def _stage_header(num: int, count: int, width: int, ascii_: bool) -> Line:
    label = f" Stage {num}"
    if count > 1:
        label += " · parallel" if not ascii_ else " - parallel"
    fill = "-" if ascii_ else "─"
    pad = max(1, width - len(label) - 1)
    return [(label + " ", "dim"), (fill * pad, "dim")]


def _flat_lines(phases: list[Phase], ready_ids: set[str], *, width: int, ascii_: bool) -> list[Line]:
    by_id = _phase_index(phases)
    idw = _id_width(phases)
    lines: list[Line] = []
    for offset, stage in enumerate(_ordered_stages(phases)):
        lines.append(_stage_header(offset + 1, len(stage), width, ascii_))
        for p in stage:
            lines.append(_node_line(p, ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_))
    return lines
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: flat stage-list fallback"
```

---

## Task 6: header, progress, rule, footer

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append:

```python
class ChromeTest(unittest.TestCase):
    def test_header_left_and_right_within_width(self) -> None:
        line = wily_watch_ui._header_line(version=2, interval=2.0, width=40, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertEqual(len(text), 40)
        self.assertTrue(text.startswith(" Wily Roadmap"))
        self.assertIn("v2", text)
        self.assertTrue(text.rstrip().endswith("~ 2s"))

    def test_progress_bar_half_full(self) -> None:
        line = wily_watch_ui._progress_line(done=3, total=6, width=40, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertIn("3/6", text)
        self.assertIn("50%", text)
        self.assertIn("#", text)
        self.assertIn("-", text)

    def test_progress_zero_total(self) -> None:
        line = wily_watch_ui._progress_line(done=0, total=0, width=40, ascii_=True)
        text = "".join(t for t, _ in line)
        self.assertIn("0/0", text)
        self.assertIn("0%", text)

    def test_footer_clean_and_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            line = wily_watch_ui._footer_line(Path(tmp), width=60, ascii_=True)
            text = "".join(t for t, _ in line)
            self.assertIn("git:", text)
            self.assertIn(Path(tmp).name, text)
            self.assertIn("^C to stop", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.ChromeTest -v`
Expected: FAIL — `AttributeError: ... '_header_line'`.

- [ ] **Step 3: Implement** — add to `scripts/wily_watch_ui.py`:

```python
def _rule_line(width: int, ascii_: bool) -> Line:
    ch = "-" if ascii_ else "─"
    return [(" " + ch * max(1, width - 1), "dim")]


def _header_line(*, version: Any, interval: float, width: int, ascii_: bool) -> Line:
    refresh = (RAIL_ASCII if ascii_ else RAIL)["refresh"]
    sep = " - " if ascii_ else " · "
    left = f" Wily Roadmap{sep}v{version}"
    right = f"{refresh} {interval:g}s "
    pad = max(1, width - len(left) - len(right))
    return [(left, "bold"), (" " * pad, ""), (right, "dim")]


def _progress_line(*, done: int, total: int, width: int, ascii_: bool) -> Line:
    g = RAIL_ASCII if ascii_ else RAIL
    bar_w = max(10, min(28, width // 3))
    ratio = (done / total) if total else 0.0
    filled = round(bar_w * ratio)
    bar = g["full"] * filled + g["empty"] * (bar_w - filled)
    pct = round(ratio * 100)
    return [
        (" " + g["lo"], "dim"),
        (g["full"] * filled, "green"),
        (g["empty"] * (bar_w - filled), "dim"),
        (g["ro"], "dim"),
        (f"  {done}/{total} · {pct}%" if not ascii_ else f"  {done}/{total} - {pct}%", "bold"),
    ]


def _git_state(root: Path, ascii_: bool) -> str:
    raw = wily_state_summary.git_status(root)
    if raw == "not a git repo":
        return "-" if ascii_ else "—"
    m = re.match(r"(\d+) changed", raw)
    if m:
        n = int(m.group(1))
        return "clean" if n == 0 else f"{n} changed"
    return raw


def _footer_line(root: Path, *, width: int, ascii_: bool) -> Line:
    sep = " - " if ascii_ else " · "
    text = f" git: {_git_state(root, ascii_)}{sep}{root.name}{sep}^C to stop"
    return [(_truncate(text, width), "dim")]
```

> The `bar` local in `_progress_line` is unused once spans are split — drop it when implementing; it's shown here only to clarify the fill math. The colored-bar span list above is the real return value.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: header, progress bar, footer"
```

---

## Task 7: `_collapse_leading_done`

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

This operates on the rendered body line list and replaces a leading run of done-node lines (each optionally followed by a `link` connector) — or, in the flat layout, leading fully-done stages — with one `● N phases done ▾` line. We tag node lines with their status so the collapser can recognize them: `_node_line` already puts the glyph as its own span; the collapser checks the first span's text (`prefix`) and the glyph span. Simpler and robust: have `_graph_lines` / `_flat_lines` return `(lines, kinds)` where `kinds[i]` is one of `"done"`, `"node"`, `"link"`, `"merge"`, `"header"`. Refactor those two functions to also return the parallel `kinds` list.

- [ ] **Step 1: Write the failing test** — append:

```python
class CollapseTest(unittest.TestCase):
    def test_collapse_leading_done_in_graph(self) -> None:
        lines, kinds = wily_watch_ui._graph_lines2(GraphTest.fan, set(), width=70, ascii_=True)
        c_lines, c_kinds = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        rendered = ["".join(t for t, _ in line) for line in c_lines]
        self.assertTrue(rendered[0].lstrip().startswith("* 3 phases done"))
        # non-done phases survive
        self.assertTrue(any("04-1" in r for r in rendered))
        self.assertTrue(any("04-2" in r for r in rendered))
        self.assertTrue(any(r.startswith(" o 05  E") for r in rendered))
        self.assertNotIn("done", c_kinds[1:])  # only the summary line carries "done"

    def test_collapse_noop_when_nothing_done(self) -> None:
        phases = [
            {"id": "01", "title": "A", "status": "pending", "depends_on": []},
            {"id": "02", "title": "B", "status": "pending", "depends_on": ["01"]},
        ]
        lines, kinds = wily_watch_ui._graph_lines2(phases, set(), width=40, ascii_=True)
        c_lines, _ = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        self.assertEqual(len(c_lines), len(lines))

    def test_collapse_leading_done_in_flat(self) -> None:
        lines, kinds = wily_watch_ui._flat_lines2(GraphTest.fan, set(), width=70, ascii_=True)
        c_lines, _ = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        rendered = ["".join(t for t, _ in line) for line in c_lines]
        self.assertTrue(rendered[0].lstrip().startswith("* 3 phases done"))
        self.assertTrue(any(r.startswith(" Stage 4 ") for r in rendered))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.CollapseTest -v`
Expected: FAIL — `AttributeError: ... '_graph_lines2'`.

- [ ] **Step 3: Implement** — in `scripts/wily_watch_ui.py`:

1. Rename the body-builders to also return `kinds`. Replace `_graph_lines` with `_graph_lines2` and `_flat_lines` with `_flat_lines2`:

```python
def _graph_lines2(phases, ready_ids, *, width, ascii_):
    rail = RAIL_ASCII if ascii_ else RAIL
    by_id = _phase_index(phases)
    idw = _id_width(phases)
    stages = _ordered_stages(phases)
    lines: list[Line] = []
    kinds: list[str] = []

    def _push(line: Line, kind: str) -> None:
        lines.append(line)
        kinds.append(kind)

    for i, stage in enumerate(stages):
        wide = len(stage) > 1
        prev_wide = i > 0 and len(stages[i - 1]) > 1
        if i == 0:
            for p in stage:
                _push(_node_line(p, ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_),
                      "done" if p.get("status") == "done" else "node")
        elif wide:
            for p in stage:
                _push(_node_line(p, ready_ids, by_id, prefix=f" {rail['branch']}", id_width=idw, width=width, ascii_=ascii_),
                      "done" if p.get("status") == "done" else "node")
        elif prev_wide:
            _push([(f" {rail['merge']}", "dim")], "merge")
            _push(_node_line(stage[0], ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_),
                  "done" if stage[0].get("status") == "done" else "node")
        else:
            _push([(f" {rail['link']}", "dim")], "link")
            _push(_node_line(stage[0], ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_),
                  "done" if stage[0].get("status") == "done" else "node")
    return lines, kinds


def _flat_lines2(phases, ready_ids, *, width, ascii_):
    by_id = _phase_index(phases)
    idw = _id_width(phases)
    lines: list[Line] = []
    kinds: list[str] = []
    for offset, stage in enumerate(_ordered_stages(phases)):
        lines.append(_stage_header(offset + 1, len(stage), width, ascii_))
        kinds.append("header")
        for p in stage:
            lines.append(_node_line(p, ready_ids, by_id, prefix=" ", id_width=idw, width=width, ascii_=ascii_))
            kinds.append("done" if p.get("status") == "done" else "node")
    return lines, kinds
```

Replace the old `_graph_lines` / `_flat_lines` with thin wrappers (so the Task 4/5 tests keep passing):

```python
def _graph_lines(phases, ready_ids, *, width, ascii_):
    return _graph_lines2(phases, ready_ids, width=width, ascii_=ascii_)[0]


def _flat_lines(phases, ready_ids, *, width, ascii_):
    return _flat_lines2(phases, ready_ids, width=width, ascii_=ascii_)[0]
```

2. Add the collapser:

```python
def _collapse_leading_done(lines: list[Line], kinds: list[str], *, ascii_: bool):
    fold = (RAIL_ASCII if ascii_ else RAIL)["fold"]
    glyph = (GLYPHS_ASCII if ascii_ else GLYPHS)["done"]
    # Walk the prefix: accept runs of (done [link|header]?)*; for flat, a "header"
    # immediately followed only by "done" nodes counts; stop at the first surviving phase.
    i = 0
    done_count = 0
    n = len(kinds)
    while i < n:
        if kinds[i] == "done":
            done_count += 1
            i += 1
            if i < n and kinds[i] in ("link", "merge"):
                i += 1
            continue
        if kinds[i] == "header":
            # peek: is the whole stage done?
            j = i + 1
            stage_all_done = True
            seen = False
            while j < n and kinds[j] in ("done", "node"):
                seen = True
                if kinds[j] == "node":
                    stage_all_done = False
                j += 1
            if seen and stage_all_done:
                done_count += sum(1 for k in range(i + 1, j) if kinds[k] == "done")
                i = j
                continue
        break
    if done_count < 2:
        return lines, kinds
    summary: Line = [(f" {glyph} {done_count} phases done {fold}", "green dim")]
    return [summary] + lines[i:], ["done"] + kinds[i:]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: collapse leading done phases"
```

---

## Task 8: `render_watch` — assemble everything

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write the failing test** — append:

```python
class RenderWatchTest(unittest.TestCase):
    def _make(self, project: Path, body: str) -> None:
        _write_roadmap(project, body)

    FAN_YAML = "\n".join([
        'roadmap_version: 2',
        'phases:',
        '  - id: "01"',
        '    title: "Settle Korean response-style update"',
        '    status: "done"',
        '    depends_on: []',
        '  - id: "02"',
        '    title: "Harden command skill consistency"',
        '    status: "done"',
        '    depends_on: ["01"]',
        '  - id: "03"',
        '    title: "Korean stage-based DAG status output"',
        '    status: "done"',
        '    depends_on: ["02"]',
        '  - id: "04-1"',
        '    title: "Improve init roadmap authoring"',
        '    status: "pending"',
        '    depends_on: ["03"]',
        '  - id: "04-2"',
        '    title: "Harden lifecycle status CLI"',
        '    status: "pending"',
        '    depends_on: ["03"]',
        '  - id: "05"',
        '    title: "Plugin discovery and release polish"',
        '    status: "pending"',
        '    depends_on: ["04-1", "04-2"]',
    ])

    def test_full_render_plain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            lines = out.splitlines()
            self.assertIn("Wily Roadmap", out)
            self.assertIn("3/6", out)
            self.assertIn("50%", out)
            self.assertTrue(any(l.lstrip().startswith("+--> 04-1") for l in lines))
            self.assertTrue(any(l.lstrip().startswith("+--> 04-2") for l in lines))
            self.assertTrue(any(l.strip() == "v" for l in lines))   # fan-in connector
            self.assertIn("needs 04-1 04-2", out)
            self.assertIn("git:", out)

    def test_render_collapses_when_short(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 8))
            self.assertIn("3 phases done", out)
            self.assertIn("04-1", out)
            self.assertIn("04-2", out)
            self.assertIn("05", out)

    def test_render_falls_back_to_flat_for_skip_dag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), "\n".join([
                'roadmap_version: 1',
                'phases:',
                '  - id: "01"',
                '    title: "A"',
                '    status: "done"',
                '    depends_on: []',
                '  - id: "02"',
                '    title: "B"',
                '    status: "done"',
                '    depends_on: ["01"]',
                '  - id: "03"',
                '    title: "C"',
                '    status: "pending"',
                '    depends_on: ["02", "01"]',
            ]))
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("Stage 1", out)
            self.assertFalse(any(l.lstrip().startswith("+--") for l in out.splitlines()))

    def test_render_narrow_one_liner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(18, 24))
            self.assertEqual(len(out.splitlines()), 1)
            self.assertIn("Wily", out)
            self.assertIn("3/6", out)

    def test_render_no_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("no roadmap", out)
            self.assertIn("$wily-init", out)
            self.assertIn("git:", out)

    def test_render_zero_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), "roadmap_version: 3\nphases: []\n")
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("0/0", out)
            self.assertIn("no phases yet", out)

    def test_render_rich_smoke(self) -> None:
        try:
            import rich  # noqa: F401
        except ImportError:
            self.skipTest("rich not installed")
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=True, size=(70, 24))
            import re as _re
            plain = _re.sub(r"\x1b\[[0-9;]*m", "", out)
            for pid in ("01", "02", "03", "04-1", "04-2", "05"):
                self.assertIn(pid, plain)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.RenderWatchTest -v`
Expected: FAIL — assertions on the empty string returned by the stub.

- [ ] **Step 3: Implement** — replace the stub `render_watch` in `scripts/wily_watch_ui.py`:

```python
def _one_line(view: _RoadmapView, root: Path, ascii_: bool) -> str:
    sep = " - " if ascii_ else " · "
    if view.roadmap is None:
        return f" Wily{sep}no roadmap"
    return f" Wily v{view.version}{sep}{view.done}/{view.total} done"


def _body_lines(view: _RoadmapView, *, width: int, max_rows: int | None, ascii_: bool) -> list[Line]:
    phases = view.phases
    if not phases:
        return [[(" (no phases yet)", "dim")]]
    if _pipeline_renderable(phases) and width >= MIN_WIDTH_RAIL:
        lines, kinds = _graph_lines2(phases, view.ready_ids, width=width, ascii_=ascii_)
    else:
        lines, kinds = _flat_lines2(phases, view.ready_ids, width=width, ascii_=ascii_)
    if max_rows is not None and len(lines) > max_rows:
        lines, kinds = _collapse_leading_done(lines, kinds, ascii_=ascii_)
    return lines


def render_watch(root: Path, *, interval: float, rich: bool,
                 size: tuple[int, int] | None = None) -> str:
    cols, rows = size if size is not None else tuple(shutil.get_terminal_size((80, 24)))
    ascii_ = not rich
    view = _load(root)

    if cols < MIN_WIDTH_ONELINE:
        return _emit([[(_one_line(view, root, ascii_), "")]], rich=rich, width=cols)

    if view.roadmap is None:
        if view.has_state:
            msg = " .wily found, no roadmap.yaml"
        else:
            msg = " Wily - no roadmap" if ascii_ else " Wily — no roadmap"
        lines: list[Line] = [
            [(msg, "bold")],
            [(" run $wily-init to start", "dim")],
            _footer_line(root, width=cols, ascii_=ascii_),
        ]
        return _emit(lines, rich=rich, width=cols)

    max_rows = max(1, rows - CHROME_ROWS) if rows else None
    body = _body_lines(view, width=cols, max_rows=max_rows, ascii_=ascii_)
    out: list[Line] = [
        _header_line(version=view.version, interval=interval, width=cols, ascii_=ascii_),
        _progress_line(done=view.done, total=view.total, width=cols, ascii_=ascii_),
        _rule_line(cols, ascii_),
        *body,
        _rule_line(cols, ascii_),
        _footer_line(root, width=cols, ascii_=ascii_),
    ]
    return _emit(out, rich=rich, width=cols)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS (rich smoke test SKIPs in this environment — that's fine).

- [ ] **Step 5: Commit**

```bash
git add scripts/wily_watch_ui.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: assemble render_watch"
```

---

## Task 9: Wire `render_watch` into `scripts/wily.py`

**Files:**
- Modify: `scripts/wily.py` — replace `ascii_watch_output` (≈549-594), `rich_watch_output` (≈597-675), `watch_output` (≈678-703), and delete `status_overview` (≈541-546). Add `import wily_watch_ui` near `import wily_state_summary`.
- Test: existing `tests/test_wily_watch_ui.py` + (next task) `tests/test_wily_cli.py`.

- [ ] **Step 1: Write the failing test**

Run the current CLI watch test to confirm it still references the old output (it will be rewritten in Task 10, but right now it is the canary):

Run: `python3 -m unittest tests.test_wily_cli.WilyCliTest.test_watch_prints_polished_pane_preview_once_with_once_flag -v`
Expected: currently PASS (old strings). After Step 3 it FAILS (old strings gone). Task 10 fixes it.

Also add a quick integration check to `tests/test_wily_watch_ui.py` (subprocess via `wily.py`) so this task has its own green signal:

```python
class CliWiringTest(unittest.TestCase):
    def test_watch_once_ascii_uses_new_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_roadmap(Path(tmp), RenderWatchTest.FAN_YAML)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "wily.py"), "watch", "--once", "--ui", "ascii"],
                cwd=tmp, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                env={**os.environ, "COLUMNS": "80", "LINES": "30"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("3/6", result.stdout)
            self.assertNotIn("Phase 흐름:", result.stdout)
            self.assertNotIn("Repo: ", result.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_wily_watch_ui.CliWiringTest -v`
Expected: FAIL — output still contains `Phase 흐름:` / `Repo: ` (old renderer).

- [ ] **Step 3: Implement**

In `scripts/wily.py`:

1. Near `import wily_state_summary` (line 17) add: `import wily_watch_ui`.
2. Delete `status_overview` (lines ≈541-546).
3. Delete `ascii_watch_output` and `rich_watch_output` entirely.
4. Replace `watch_output` with:

```python
def watch_output(root: Path, interval: float = 2.0, ui: str = "auto") -> str:
    use_rich = ui != "ascii" and rich_available()
    body = wily_watch_ui.render_watch(root, interval=interval, rich=use_rich)
    if not use_rich and ui in {"auto", "rich"} and not rich_available():
        return "\n".join([
            "Rich UI is not installed.",
            "Run: $wily-watch --install-ui",
            "Fallback: using ASCII watch UI.",
            "",
            body,
        ])
    return body
```

> `StringIO` import in `wily.py` was only used by `rich_watch_output`; remove the now-unused `from io import StringIO` if nothing else uses it. (`shutil` is still used elsewhere — keep it.) Run `python3 -c "import ast,sys; ast.parse(open('scripts/wily.py').read())"` to confirm the file still parses; then grep for `StringIO`/`status_overview`/`ascii_watch_output`/`rich_watch_output` to confirm no dangling references remain.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests.test_wily_watch_ui -v`
Expected: PASS (incl. `CliWiringTest`).

Run: `python3 -m unittest discover -s tests -v`
Expected: the four `WilyCliTest.test_watch_*` content tests now FAIL (old strings) — fixed in Task 10. All other tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/wily.py tests/test_wily_watch_ui.py
git commit -m "wily-watch: route watch_output through pipeline renderer"
```

---

## Task 10: Update `tests/test_wily_cli.py` watch assertions

**Files:**
- Modify: `tests/test_wily_cli.py` — replace the bodies of `test_watch_prints_polished_pane_preview_once_with_once_flag`, `test_watch_ascii_ui_does_not_print_rich_install_hint`, `test_watch_rich_ui_uses_thin_dashboard_not_panels`, `test_watch_auto_ui_prints_rich_install_hint_when_rich_is_missing` (the env-based one only needs its assertions kept — it still works since the preamble text is unchanged). The tmux pane / `--install-ui` tests are untouched.

- [ ] **Step 1: Write the failing test** — replace the four method bodies:

```python
    def test_watch_prints_polished_pane_preview_once_with_once_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project, "watch", "--once", "--ui", "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = result.stdout
            self.assertIn("Wily Roadmap", out)
            self.assertIn("v1", out)
            self.assertIn("0/1", out)
            self.assertIn("0%", out)
            self.assertIn("> 01  First phase", out)   # ascii ready glyph
            self.assertIn("git:", out)
            self.assertNotIn("Phase 흐름:", out)
            self.assertNotIn("Repo: ", out)

    def test_watch_ascii_ui_does_not_print_rich_install_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text("roadmap_version: 1\nphases: []\n", encoding="utf-8")

            result = self.run_wily_with_env(
                project, "watch", "--once", "--ui", "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("no phases yet", result.stdout)
            self.assertNotIn("Rich UI is not installed", result.stdout)

    def test_watch_rich_ui_uses_thin_dashboard_not_panels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project, "watch", "--once", "--ui", "rich",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            if "Rich UI is not installed." in result.stdout:
                self.skipTest("Rich is not installed")
            self.assertEqual(result.returncode, 0, result.stderr)
            plain = strip_ansi(result.stdout)
            self.assertIn("Wily Roadmap", plain)
            self.assertIn("v1", plain)
            self.assertIn("0/1", plain)
            self.assertIn("First phase", plain)
            self.assertNotIn("╭", plain)
            self.assertNotIn("┏", plain)
```

(Leave `test_watch_auto_ui_prints_rich_install_hint_when_rich_is_missing` exactly as it is — the preamble strings are unchanged.)

- [ ] **Step 2: Run test to verify it fails (before applying) / passes (after)**

Run: `python3 -m unittest tests.test_wily_cli.WilyCliTest -v -k watch`
Expected after the edits: all `watch` tests PASS (rich one may SKIP).

- [ ] **Step 3: (no separate implementation — Task 9 already changed the renderer)**

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: ALL tests PASS (rich-dependent tests SKIP in this environment).

- [ ] **Step 5: Commit**

```bash
git add tests/test_wily_cli.py
git commit -m "wily-watch: update CLI tests for pipeline output"
```

---

## Task 11: Update `skills/wily-watch/SKILL.md`

**Files:**
- Modify: `skills/wily-watch/SKILL.md` — the "Behavior" section.

- [ ] **Step 1: Edit the "Behavior" bullets**

Replace the current bullet list under `## Behavior` with:

```markdown
## Behavior

- $wily-watch opens a tmux pane by default (a vertical split on the right).
- Renders a vertical pipeline of the roadmap: header (`Wily Roadmap · vN  ⟳ Ns`), a progress bar (`done/total · pct%`), then one line per phase — `<status glyph> <id>  <title>` with a `git log --graph`-style left rail (`│` linear, `├──` parallel branch, `▼` fan-in) and unmet dependencies marked with `⟂`.
- Falls back to a flat `Stage N` list when the dependency graph is too tangled for the rail, and to a one-line summary when the pane is very narrow.
- When the pane is too short, the leading run of finished phases collapses to a single `● N phases done ▾` line; unfinished phases always stay visible.
- Uses Rich when installed, otherwise an ASCII fallback (`*`/`>`/`~`/`x`/`o` glyphs, `[####----]` bar).
- Adds a footer with git dirty-file count, the repo name, and a `^C to stop` hint.
- Opens a horizontal tmux split (`split-window -h`) when running inside tmux; returns a clear fallback command when tmux is unavailable.
- Run `$wily-watch --install-ui` to install the optional Rich UI dependency.
- Accepts `--ui rich|ascii|auto` for UI selection.
- Accepts `--once` for tests or a one-shot preview.
- Accepts `--interval <seconds>` for refresh cadence.
- Use `--here` only when the user asks to run watch in the current pane.
```

- [ ] **Step 2: Verify the skills manifest still validates**

Run: `python3 -m unittest tests.test_wily_command_skills -v`
Expected: PASS (this test only checks command wiring, not prose — confirms nothing structural broke).

- [ ] **Step 3: Run the whole suite once more**

Run: `python3 -m unittest discover -s tests -v`
Expected: ALL PASS / SKIP.

- [ ] **Step 4: Commit**

```bash
git add skills/wily-watch/SKILL.md
git commit -m "wily-watch: document the vertical pipeline view"
```

---

## Self-review notes (for the implementer)

- The plan keeps both `_graph_lines`/`_flat_lines` (thin wrappers returning `[0]`) so Task 4/5 tests stay valid after Task 7 introduces `_graph_lines2`/`_flat_lines2`. If you prefer, collapse the wrappers away and update those tests instead — either is fine, just be consistent.
- `_progress_line` in Task 6 shows a `bar` local for clarity; the real return value is the span list that splits filled/empty into separately-styled segments. Don't leave the unused local in.
- ASCII glyph for `ready` is `>` — `test_watch_prints_polished_pane_preview_once_with_once_flag` asserts `> 01  First phase` (the phase has `status: "ready"`). Double-check the `id_width` for a single 2-char id is 2, so the spacing is `"01".ljust(2) + "  "` → `"01  "` → ` > 01  First phase`.
- Rich-dependent tests SKIP cleanly when `rich` is absent (the dev environment). If you want to exercise the rich path, run `python3 scripts/wily.py watch --install-ui` first, then re-run the suite.
- After Task 9, grep to confirm no dangling references: `git grep -n "status_overview\|ascii_watch_output\|rich_watch_output" -- scripts/` should return nothing.
