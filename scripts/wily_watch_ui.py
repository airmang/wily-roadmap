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
