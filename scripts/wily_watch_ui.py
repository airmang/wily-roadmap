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


def _node_line(
    phase: Phase,
    ready_ids: set[str],
    by_id: dict[str, Phase],
    *,
    prefix: str,
    id_width: int,
    width: int,
    ascii_: bool,
) -> Line:
    status = _phase_status(phase, ready_ids)
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    rails = RAIL_ASCII if ascii_ else RAIL
    glyph = glyphs.get(status, glyphs["pending"])
    style = STYLES.get(status, "")
    pid = str(phase.get("id", "?"))
    title = str(phase.get("title", "Untitled phase"))
    id_text = f" {pid.ljust(id_width)}  "
    unmet = _unmet_deps(phase, by_id)
    dep_text = ""
    if unmet:
        dep_text = f"   {rails['dep']} " + " ".join(unmet)

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
