#!/usr/bin/env python3
"""Render the Wily roadmap watch pane as a vertical pipeline."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Any

import wily_state_summary


Phase = dict[str, Any]
Span = tuple[str, str]
Line = list[Span]

GLYPHS = {
    "done": "●",
    "ready": "▶",
    "in_progress": "◐",
    "needs_review": "◆",
    "blocked": "✗",
    "pending": "○",
    "superseded": "⊘",
}
GLYPHS_ASCII = {
    "done": "*",
    "ready": ">",
    "in_progress": "~",
    "needs_review": "?",
    "blocked": "x",
    "pending": "o",
    "superseded": "-",
}
STYLES = {
    "done": "green dim",
    "ready": "bold cyan",
    "in_progress": "bold yellow",
    "needs_review": "magenta",
    "blocked": "bold red",
    "pending": "dim",
    "superseded": "dim",
}
RAIL = {
    "link": "│",
    "branch": "├──",
    "merge": "▼",
    "fold": "▾",
    "full": "█",
    "empty": "░",
    "lo": "▕",
    "ro": "▏",
    "dep": "⟂",
    "refresh": "⟳",
}
RAIL_ASCII = {
    "link": "|",
    "branch": "+--",
    "merge": "v",
    "fold": "v",
    "full": "#",
    "empty": "-",
    "lo": "[",
    "ro": "]",
    "dep": "needs",
    "refresh": "~",
}
CHROME_ROWS = 5
MIN_WIDTH_ONELINE = 24
MIN_WIDTH_RAIL = 28


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
        return {str(phase.get("id", "?")) for phase in self.ready}

    @property
    def total(self) -> int:
        return len(self.phases)

    @property
    def done(self) -> int:
        return sum(1 for phase in self.phases if phase.get("status") == "done")


def _load(root: Path) -> _RoadmapView:
    state_dir = root / ".wily"
    roadmap_path = state_dir / "roadmap.yaml"
    if not roadmap_path.exists():
        return _RoadmapView(root=root, has_state=state_dir.exists(), roadmap=None)

    roadmap = wily_state_summary.parse_roadmap(wily_state_summary.read_text(roadmap_path))
    phases = roadmap.get("phases") or []
    ready = wily_state_summary.executable_phases(phases)
    return _RoadmapView(
        root=root,
        has_state=True,
        roadmap=roadmap,
        phases=phases,
        ready=ready,
        by_id=_phase_index(phases),
    )


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit == 1:
        return "…"
    return f"{text[: limit - 1]}…"


def _phase_index(phases: list[Phase]) -> dict[str, Phase]:
    return {str(phase.get("id", "?")): phase for phase in phases}


def _ordered_stages(phases: list[Phase]) -> list[list[Phase]]:
    grouped = wily_state_summary.stage_groups(phases)
    return [grouped[stage] for stage in sorted(grouped)]


def _pipeline_renderable(phases: list[Phase]) -> bool:
    if not phases:
        return False

    stages = _ordered_stages(phases)
    previous_ids: set[str] = set()
    previous_wide = False

    for index, stage in enumerate(stages):
        stage_wide = len(stage) > 1
        if previous_wide and stage_wide:
            return False

        if index == 0:
            if any(phase.get("depends_on") or [] for phase in stage):
                return False
        else:
            for phase in stage:
                dependencies = {str(dep) for dep in phase.get("depends_on") or []}
                if dependencies != previous_ids:
                    return False

        previous_ids = {str(phase.get("id", "?")) for phase in stage}
        previous_wide = stage_wide

    return True


def _id_width(phases: list[Phase]) -> int:
    return max((len(str(phase.get("id", "?"))) for phase in phases), default=2)


def _stage_header(num: int, count: int, width: int, ascii_: bool) -> Line:
    label = f" Stage {num}"
    if count > 1:
        label += " - parallel" if ascii_ else " · parallel"
    fill = "-" if ascii_ else "─"
    text = f"{label} "
    if len(text) < width:
        text += fill * (width - len(text))
    return _crop_line([(text, "dim")], width)


def _phase_status(phase: Phase, ready_ids: set[str]) -> str:
    pid = str(phase.get("id", "?"))
    if pid in ready_ids:
        return "ready"
    return str(phase.get("status") or "pending")


def _unmet_deps(phase: Phase, by_id: dict[str, Phase]) -> list[str]:
    unmet = []
    for dep in phase.get("depends_on") or []:
        dep_id = str(dep)
        target = by_id.get(dep_id)
        if target is None or target.get("status") != "done":
            unmet.append(dep_id)
    return unmet


def _crop_line(line: Line, width: int) -> Line:
    remaining = max(0, width)
    cropped: Line = []
    for text, style in line:
        if remaining <= 0:
            break
        cropped_text = text[:remaining]
        cropped.append((cropped_text, style))
        remaining -= len(cropped_text)
    return cropped


def _rule_line(width: int, ascii_: bool) -> Line:
    fill = "-" if ascii_ else "─"
    return _crop_line([(f" {fill * max(0, width - 1)}", "dim")], width)


def _header_line(*, version: Any, interval: float, width: int, ascii_: bool) -> Line:
    rails = RAIL_ASCII if ascii_ else RAIL
    sep = " - " if ascii_ else " · "
    left = f" Wily Roadmap{sep}v{version}"
    right = f"{rails['refresh']} {interval:g}s "

    if len(left) + len(right) > width:
        return _crop_line([(left, "bold"), (right, "dim")], width)

    padding = " " * (width - len(left) - len(right))
    return [(left, "bold"), (padding, ""), (right, "dim")]


def _progress_line(*, done: int, total: int, width: int, ascii_: bool) -> Line:
    rails = RAIL_ASCII if ascii_ else RAIL
    ratio = done / total if total else 0.0
    pct = round(ratio * 100)
    sep = " - " if ascii_ else " · "
    label = f" {done}/{total}{sep}{pct}%"
    bar_w = max(10, min(28, width // 3))
    max_bar_w = max(0, width - len(rails["lo"]) - len(rails["ro"]) - len(label))
    if len(rails["lo"]) + bar_w + len(rails["ro"]) + len(label) > width:
        bar_w = max_bar_w
    filled = min(bar_w, max(0, round(bar_w * ratio)))
    empty = max(0, bar_w - filled)

    return _crop_line(
        [
            (rails["lo"], "dim"),
            (rails["full"] * filled, "green"),
            (rails["empty"] * empty, "dim"),
            (rails["ro"], "dim"),
            (label, ""),
        ],
        width,
    )


def _git_state(root: Path, ascii_: bool) -> str:
    raw = wily_state_summary.git_status(root)
    if raw == "not a git repo":
        return "-" if ascii_ else "—"
    match = re.match(r"(\d+) changed", raw)
    if match:
        changed = int(match.group(1))
        return "clean" if changed == 0 else f"{changed} changed"
    return raw


def _footer_line(root: Path, *, width: int, ascii_: bool) -> Line:
    sep = " - " if ascii_ else " · "
    text = f" git: {_git_state(root, ascii_)}{sep}{root.name}{sep}^C to stop"
    return _crop_line([(text, "dim")], width)


def _node_line(
    phase: Phase,
    ready_ids: set[str],
    by_id: dict[str, Phase],
    *,
    prefix: str,
    id_width: int,
    width: int,
    ascii_: bool,
    dependency_ids: list[str] | None = None,
    dependency_marker: str | None = None,
) -> Line:
    status = _phase_status(phase, ready_ids)
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    rails = RAIL_ASCII if ascii_ else RAIL
    glyph = glyphs.get(status, glyphs["pending"])
    style = STYLES.get(status, "")
    pid = str(phase.get("id", "?"))
    title = str(phase.get("title", "Untitled phase"))
    id_text = f" {pid.ljust(id_width)}  "
    unmet = dependency_ids if dependency_ids is not None else _unmet_deps(phase, by_id)
    dep_text = ""
    if unmet:
        marker = dependency_marker or rails["dep"]
        dep_text = f"   {marker} " + " ".join(unmet)

    title_width = max(0, width - len(prefix) - len(glyph) - len(id_text) - len(dep_text))
    title = _truncate(title, title_width)
    dep_width = max(0, width - len(prefix) - len(glyph) - len(id_text) - len(title))
    dep_text = _truncate(dep_text, dep_width)

    line: Line = [
        (prefix, "dim"),
        (glyph, style),
        (id_text, style),
        (title, ""),
    ]
    if dep_text:
        line.append((dep_text, "dim"))
    return _crop_line(line, width)


def _flat_lines2(
    phases: list[Phase],
    ready_ids: set[str],
    *,
    width: int,
    ascii_: bool,
) -> tuple[list[Line], list[str]]:
    by_id = _phase_index(phases)
    id_width = _id_width(phases)
    lines: list[Line] = []
    kinds: list[str] = []

    for num, stage in enumerate(_ordered_stages(phases), start=1):
        lines.append(_stage_header(num, len(stage), width, ascii_))
        kinds.append("header")
        for phase in stage:
            lines.append(
                _node_line(
                    phase,
                    ready_ids,
                    by_id,
                    prefix=" ",
                    id_width=id_width,
                    width=width,
                    ascii_=ascii_,
                )
            )
            kinds.append("done" if phase.get("status") == "done" else "node")

    return lines, kinds


def _flat_lines(phases: list[Phase], ready_ids: set[str], *, width: int, ascii_: bool) -> list[Line]:
    lines, _kinds = _flat_lines2(phases, ready_ids, width=width, ascii_=ascii_)
    return lines


def _graph_lines2(
    phases: list[Phase],
    ready_ids: set[str],
    *,
    width: int,
    ascii_: bool,
) -> tuple[list[Line], list[str]]:
    rails = RAIL_ASCII if ascii_ else RAIL
    by_id = _phase_index(phases)
    id_width = _id_width(phases)
    stages = _ordered_stages(phases)
    lines: list[Line] = []
    kinds: list[str] = []
    previous_wide = False

    for index, stage in enumerate(stages):
        stage_wide = len(stage) > 1
        if index > 0:
            if previous_wide and not stage_wide:
                lines.append([(f" {rails['merge']}", "dim")])
                kinds.append("merge")
            elif not previous_wide and not stage_wide:
                lines.append([(f" {rails['link']}", "dim")])
                kinds.append("link")

        prefix = f" {rails['branch']}" if stage_wide else " "
        for phase in stage:
            dependency_ids = None
            dependency_marker = None
            if previous_wide and not stage_wide:
                dependency_ids = [str(dep) for dep in phase.get("depends_on") or []]
                dependency_marker = "deps" if ascii_ else RAIL["dep"]
            lines.append(
                _node_line(
                    phase,
                    ready_ids,
                    by_id,
                    prefix=prefix,
                    id_width=id_width,
                    width=width,
                    ascii_=ascii_,
                    dependency_ids=dependency_ids,
                    dependency_marker=dependency_marker,
                )
            )
            kinds.append("done" if phase.get("status") == "done" else "node")
        previous_wide = stage_wide

    return lines, kinds


def _graph_lines(phases: list[Phase], ready_ids: set[str], *, width: int, ascii_: bool) -> list[Line]:
    lines, _kinds = _graph_lines2(phases, ready_ids, width=width, ascii_=ascii_)
    return lines


def _summary_line(done_count: int, ascii_: bool) -> Line:
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    rails = RAIL_ASCII if ascii_ else RAIL
    return [(f" {glyphs['done']} {done_count} phases done {rails['fold']}", "green dim")]


def _collapse_leading_done(lines: list[Line], kinds: list[str], *, ascii_: bool) -> tuple[list[Line], list[str]]:
    if not lines or not kinds or len(lines) != len(kinds):
        return lines, kinds

    if kinds[0] == "header":
        index = 0
        done_count = 0
        while index < len(kinds) and kinds[index] == "header":
            next_header = index + 1
            while next_header < len(kinds) and kinds[next_header] != "header":
                next_header += 1

            stage_kinds = kinds[index + 1 : next_header]
            if not stage_kinds or any(kind != "done" for kind in stage_kinds):
                break

            done_count += len(stage_kinds)
            index = next_header

        if done_count < 2:
            return lines, kinds
        return [_summary_line(done_count, ascii_)] + lines[index:], ["done"] + kinds[index:]

    index = 0
    done_count = 0
    while index < len(kinds):
        kind = kinds[index]
        if kind == "done":
            done_count += 1
            index += 1
        elif kind in {"link", "merge"} and done_count > 0:
            index += 1
        else:
            break

    if done_count < 2:
        return lines, kinds
    return [_summary_line(done_count, ascii_)] + lines[index:], ["done"] + kinds[index:]


def _emit(lines: list[Line], *, rich: bool, width: int) -> str:
    if not rich:
        return "\n".join("".join(text for text, _style in line).rstrip() for line in lines)

    from rich.console import Console, Group
    from rich.text import Text

    rendered_lines = []
    for line in lines:
        text = Text(no_wrap=True, overflow="crop")
        for content, style in line:
            text.append(content, style=style or None)
        rendered_lines.append(text)

    output = StringIO()
    console = Console(
        file=output,
        record=True,
        width=width,
        force_terminal=True,
        color_system="truecolor",
    )
    console.print(Group(*rendered_lines))
    return console.export_text(styles=True).rstrip("\n")


def render_watch(
    root: Path,
    *,
    interval: float,
    rich: bool,
    size: tuple[int, int] | None = None,
) -> str:
    return ""
