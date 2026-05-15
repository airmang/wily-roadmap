#!/usr/bin/env python3
"""Render the Wily roadmap watch pane as a vertical pipeline."""

from __future__ import annotations

import re
import shutil
import unicodedata
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
    stages = roadmap.get("stages") or []
    if stages:
        stages = wily_state_summary.enrich_stages_with_local_state(root, stages)
    phases = stages if stages else roadmap.get("phases") or []
    ready = wily_state_summary.executable_stages(stages) if stages else wily_state_summary.executable_phases(phases)
    return _RoadmapView(
        root=root,
        has_state=True,
        roadmap=roadmap,
        phases=phases,
        ready=ready,
        by_id=_phase_index(phases),
    )


def _char_width(char: str) -> int:
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1


def _display_width(text: str) -> int:
    return sum(_char_width(char) for char in text)


def _take_start(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    width = 0
    chars = []
    for char in text:
        char_width = _char_width(char)
        if width + char_width > limit:
            break
        chars.append(char)
        width += char_width
    return "".join(chars)


def _take_end(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    width = 0
    chars = []
    for char in reversed(text):
        char_width = _char_width(char)
        if width + char_width > limit:
            break
        chars.append(char)
        width += char_width
    return "".join(reversed(chars))


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if _display_width(text) <= limit:
        return text
    if limit == 1:
        return "…"
    return f"{_take_start(text, limit - 1)}…"


def _fit_title(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if _display_width(text) <= limit:
        return text
    if limit == 1:
        return "…"

    available = limit - 1
    prefix_len = available // 2
    suffix_len = available - prefix_len
    return f"{_take_start(text, prefix_len)}…{_take_end(text, suffix_len)}"


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


def _runner_status_from_text(text: str) -> str | None:
    for line in text.splitlines():
        match = re.match(r"\s*status:\s*`?([A-Za-z0-9_-]+)`?", line)
        if match:
            return match.group(1)
        match = re.match(r"\s*-\s*Recommended Wily status:\s*`?([A-Za-z0-9_-]+)`?", line)
        if match:
            return match.group(1)
    return None


def _runner_status_detail(root: Path | None, phase: Phase) -> str:
    if root is None:
        return ""
    current = phase.get("current_session")
    if not current:
        return ""
    session = root / ".wily" / str(current)
    runner_dir = session / "runner"
    if not runner_dir.exists():
        return ""
    for name in ("status-board.md", "progress.md", "verification.md", "archive-summary.md"):
        path = runner_dir / name
        if not path.exists():
            continue
        status = _runner_status_from_text(path.read_text(encoding="utf-8"))
        if status:
            return f"runner {status}"
    return "runner active"


def _first_phase_text(phase: Phase, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = phase.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _phase_assignment_detail(phase: Phase) -> str:
    owner = _first_phase_text(phase, ("owner", "assignee", "assigned_to"))
    task = _first_phase_text(phase, ("task", "assignment"))
    parts: list[str] = []
    if owner:
        parts.append(owner if owner.startswith("@") else f"@{owner}")
    if task:
        parts.append(f"task {task}")
    return "   ".join(parts)


def _crop_line(line: Line, width: int) -> Line:
    remaining = max(0, width)
    cropped: Line = []
    for text, style in line:
        if remaining <= 0:
            break
        cropped_text = _take_start(text, remaining)
        cropped.append((cropped_text, style))
        remaining -= _display_width(cropped_text)
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


def _footer_line(root: Path, *, width: int, ascii_: bool, interactive: bool = False, expand_done: bool = False) -> Line:
    sep = " - " if ascii_ else " · "
    if interactive:
        toggle = "left-click/d collapse done" if expand_done else "left-click/d expand done"
        scroll = f"{sep}wheel scroll" if expand_done else ""
        text = (
            f" {toggle}{sep}right-click menu{scroll}{sep}r refresh{sep}q quit"
            f"{sep}git: {_git_state(root, ascii_)}{sep}{root.name}"
        )
    else:
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
    runner_detail: str = "",
) -> Line:
    status = _phase_status(phase, ready_ids)
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    glyph = glyphs.get(status, glyphs["pending"])
    style = STYLES.get(status, "")
    pid = str(phase.get("id", "?"))
    title = str(phase.get("title", "Untitled phase"))
    id_text = f" {pid.ljust(id_width)}  "
    unmet = dependency_ids if dependency_ids is not None else _unmet_deps(phase, by_id)
    detail_parts = []
    if unmet:
        marker = dependency_marker or "needs"
        detail_parts.append(f"{marker} " + " ".join(unmet))
    assignment_detail = _phase_assignment_detail(phase)
    if assignment_detail:
        detail_parts.append(assignment_detail)
    child_phases = phase.get("phases") or []
    if child_phases:
        phase_word = "phase" if len(child_phases) == 1 else "phases"
        lane_count = sum(len(child.get("lanes") or []) for child in child_phases if isinstance(child, dict))
        detail_parts.append(f"{len(child_phases)} {phase_word}")
        if lane_count:
            detail_parts.append(f"{lane_count} lanes")
    if runner_detail:
        detail_parts.append(runner_detail)
    detail_text = f"   {'   '.join(detail_parts)}" if detail_parts else ""

    fixed_width = _display_width(prefix) + _display_width(glyph) + _display_width(id_text)
    available_width = max(0, width - fixed_width)
    detail_budget = 0
    if detail_text and available_width > 0:
        detail_budget = min(_display_width(detail_text), max(0, available_width // 3))
    title_width = max(0, available_width - detail_budget)
    title = _fit_title(title, title_width)
    detail_width = max(0, width - fixed_width - _display_width(title))
    detail_text = _truncate(detail_text, detail_width)

    line: Line = [
        (prefix, "dim"),
        (glyph, style),
        (id_text, style),
        (title, ""),
    ]
    if detail_text:
        line.append((detail_text, "dim"))
    return _crop_line(line, width)


def _flat_lines2(
    phases: list[Phase],
    ready_ids: set[str],
    *,
    width: int,
    ascii_: bool,
    root: Path | None = None,
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
                    runner_detail=_runner_status_detail(root, phase),
                )
            )
            kinds.append("done" if phase.get("status") == "done" else "node")
            child_lines, child_kinds = _child_phase_lines(phase, width=width, ascii_=ascii_)
            lines.extend(child_lines)
            kinds.extend(child_kinds)

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
    root: Path | None = None,
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
                dependency_marker = "deps"
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
                    runner_detail=_runner_status_detail(root, phase),
                )
            )
            kinds.append("done" if phase.get("status") == "done" else "node")
            child_lines, child_kinds = _child_phase_lines(phase, width=width, ascii_=ascii_)
            lines.extend(child_lines)
            kinds.extend(child_kinds)
        previous_wide = stage_wide

    return lines, kinds


def _graph_lines(phases: list[Phase], ready_ids: set[str], *, width: int, ascii_: bool) -> list[Line]:
    lines, _kinds = _graph_lines2(phases, ready_ids, width=width, ascii_=ascii_)
    return lines


def _summary_line(done_count: int, stage_count: int, ascii_: bool, *, unit: str = "phase") -> Line:
    glyphs = GLYPHS_ASCII if ascii_ else GLYPHS
    rails = RAIL_ASCII if ascii_ else RAIL
    if unit == "stage":
        stage_word = "stage" if done_count == 1 else "stages"
        return [(f" {glyphs['done']} {done_count} {stage_word} done {rails['fold']}", "green dim")]
    phase_word = "phase" if done_count == 1 else "phases"
    stage_word = "stage" if stage_count == 1 else "stages"
    return [(f" {glyphs['done']} {done_count} {phase_word} done across {stage_count} {stage_word} {rails['fold']}", "green dim")]


def _child_phase_lines(stage: Phase, *, width: int, ascii_: bool) -> tuple[list[Line], list[str]]:
    children = stage.get("phases") or []
    if not children or not isinstance(children, list):
        return [], []
    by_id = _phase_index(children)
    ready_ids = {str(phase.get("id", "?")) for phase in wily_state_summary.executable_phases(children)}
    id_width = _id_width(children)
    prefix = "   " if ascii_ else "   "
    lines: list[Line] = []
    kinds: list[str] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        lines.append(
            _node_line(
                child,
                ready_ids,
                by_id,
                prefix=prefix,
                id_width=id_width,
                width=width,
                ascii_=ascii_,
            )
        )
        kinds.append("child-done" if child.get("status") == "done" else "child-node")
    return lines, kinds


def _future_stage_summary_line(num: int, stage: list[Phase], width: int, ascii_: bool) -> Line:
    unfinished = sum(1 for phase in stage if phase.get("status") != "done")
    count = unfinished if unfinished else len(stage)
    phase_word = "phase" if count == 1 else "phases"
    text = f" Stage {num} - {count} {phase_word} pending"
    return _crop_line([(text, "dim")], width)


def _collapse_leading_done(
    lines: list[Line],
    kinds: list[str],
    *,
    ascii_: bool,
    stage_mode: bool = False,
) -> tuple[list[Line], list[str]]:
    if not lines or not kinds or len(lines) != len(kinds):
        return lines, kinds

    if kinds[0] == "header":
        index = 0
        done_count = 0
        stage_count = 0
        while index < len(kinds) and kinds[index] == "header":
            next_header = index + 1
            while next_header < len(kinds) and kinds[next_header] != "header":
                next_header += 1

            stage_kinds = kinds[index + 1 : next_header]
            done_kinds = {"done", "child-done"} if stage_mode else {"done"}
            if not stage_kinds or any(kind not in done_kinds for kind in stage_kinds):
                break

            done_count += 1 if stage_mode else len(stage_kinds)
            stage_count += 1
            index = next_header

        if done_count < 2:
            return lines, kinds
        return [_summary_line(done_count, stage_count, ascii_, unit="stage" if stage_mode else "phase")] + lines[index:], ["done"] + kinds[index:]

    index = 0
    done_count = 0
    stage_count = 0
    previous_was_done = False
    while index < len(kinds):
        kind = kinds[index]
        if kind == "done":
            done_count += 1
            if not previous_was_done:
                stage_count += 1
            previous_was_done = True
            index += 1
        elif stage_mode and kind == "child-done" and done_count > 0:
            index += 1
        elif kind in {"link", "merge"} and done_count > 0:
            previous_was_done = False
            index += 1
        else:
            break

    if done_count < 2:
        return lines, kinds
    return [_summary_line(done_count, stage_count, ascii_, unit="stage" if stage_mode else "phase")] + lines[index:], ["done"] + kinds[index:]


def _preserve_unfinished_lines(lines: list[Line], kinds: list[str]) -> tuple[list[Line], list[str]]:
    if not lines or not kinds or len(lines) != len(kinds) or kinds[0] != "done":
        return lines, kinds
    kept_lines = [lines[0]]
    kept_kinds = [kinds[0]]
    for line, kind in zip(lines[1:], kinds[1:]):
        if kind in {"node", "child-node"}:
            kept_lines.append(line)
            kept_kinds.append(kind)
    return kept_lines, kept_kinds


def _frontier_stage_index(stages: list[list[Phase]], ready_ids: set[str]) -> int | None:
    for index, stage in enumerate(stages):
        if all(phase.get("status") == "done" for phase in stage):
            continue
        if any(str(phase.get("id", "?")) in ready_ids for phase in stage):
            return index

    for index, stage in enumerate(stages):
        if any(phase.get("status") != "done" for phase in stage):
            return index
    return None


def _trim_frontier_compact_lines(lines: list[Line], kinds: list[str], max_rows: int) -> list[Line]:
    if len(lines) <= max_rows:
        return lines
    if max_rows <= 0:
        return []

    frontier_indexes = [index for index, kind in enumerate(kinds) if kind in {"frontier-header", "frontier-node"}]
    if not frontier_indexes:
        return lines[:max_rows]

    frontier_lines = [lines[index] for index in frontier_indexes]
    if len(frontier_lines) >= max_rows:
        if max_rows == 1:
            node_indexes = [index for index in frontier_indexes if kinds[index] == "frontier-node"]
            return [lines[node_indexes[0]]] if node_indexes else [frontier_lines[0]]
        return frontier_lines[:max_rows]

    kept: list[Line] = []
    if kinds and kinds[0] == "done" and max_rows > len(frontier_lines):
        kept.append(lines[0])

    remaining = max_rows - len(kept)
    if remaining <= 0:
        return kept
    kept.extend(frontier_lines[:remaining])
    remaining = max_rows - len(kept)
    if remaining <= 0:
        return kept

    future_lines = [line for line, kind in zip(lines, kinds) if kind == "future-summary"]
    kept.extend(future_lines[:remaining])
    return kept


def _compact_frontier_lines(
    view: _RoadmapView,
    *,
    width: int,
    max_rows: int,
    ascii_: bool,
) -> list[Line]:
    stages = _ordered_stages(view.phases)
    frontier_index = _frontier_stage_index(stages, view.ready_ids)
    if frontier_index is None:
        return []

    by_id = _phase_index(view.phases)
    id_width = _id_width(view.phases)
    lines: list[Line] = []
    kinds: list[str] = []
    done_prefix = stages[:frontier_index]
    done_count = sum(len(stage) for stage in done_prefix if all(phase.get("status") == "done" for phase in stage))
    if done_count:
        lines.append(_summary_line(done_count, len(done_prefix), ascii_))
        kinds.append("done")

    frontier = stages[frontier_index]
    lines.append(_stage_header(frontier_index + 1, len(frontier), width, ascii_))
    kinds.append("frontier-header")
    for phase in frontier:
        lines.append(
            _node_line(
                phase,
                view.ready_ids,
                by_id,
                prefix=" ",
                id_width=id_width,
                width=width,
                ascii_=ascii_,
                runner_detail=_runner_status_detail(view.root, phase),
            )
        )
        kinds.append("frontier-node")

    for num, stage in enumerate(stages[frontier_index + 1 :], start=frontier_index + 2):
        lines.append(_future_stage_summary_line(num, stage, width, ascii_))
        kinds.append("future-summary")

    return _trim_frontier_compact_lines(lines, kinds, max_rows)


def _one_line(view: _RoadmapView, root: Path, ascii_: bool) -> str:
    sep = " - " if ascii_ else " · "
    if view.roadmap is None:
        return f" Wily{sep}no roadmap"
    return f" Wily v{view.version}{sep}{view.done}/{view.total} done"


def _body_lines(
    view: _RoadmapView,
    *,
    width: int,
    max_rows: int | None,
    ascii_: bool,
    expand_done: bool = False,
    scroll_offset: int = 0,
) -> list[Line]:
    if not view.phases:
        return [[(" (no phases yet)", "dim")]]

    if _pipeline_renderable(view.phases) and width >= MIN_WIDTH_RAIL:
        lines, kinds = _graph_lines2(view.phases, view.ready_ids, width=width, ascii_=ascii_, root=view.root)
    else:
        lines, kinds = _flat_lines2(view.phases, view.ready_ids, width=width, ascii_=ascii_, root=view.root)

    if not expand_done and max_rows is not None and len(lines) > max_rows:
        lines, kinds = _collapse_leading_done(lines, kinds, ascii_=ascii_, stage_mode=bool((view.roadmap or {}).get("stages")))

    if not expand_done and max_rows is not None and len(lines) > max_rows:
        if max_rows == 1:
            compact = _compact_frontier_lines(view, width=width, max_rows=max_rows, ascii_=ascii_)
            return compact or lines[:1]
        if kinds and kinds[0] == "done":
            preserved_lines, preserved_kinds = _preserve_unfinished_lines(lines, kinds)
            if len(preserved_lines) <= max_rows or len(preserved_lines) < len(lines):
                return preserved_lines
        compact = _compact_frontier_lines(view, width=width, max_rows=max_rows, ascii_=ascii_)
        if compact:
            return compact
        if kinds and kinds[0] == "done":
            return [lines[0]] + lines[-(max_rows - 1) :]
        return lines[-max_rows:]

    if expand_done and max_rows is not None and len(lines) > max_rows:
        offset = clamp_scroll_offset(scroll_offset, total_rows=len(lines), visible_rows=max_rows)
        return lines[offset : offset + max_rows]

    return lines


def clamp_scroll_offset(offset: int, *, total_rows: int, visible_rows: int) -> int:
    max_offset = max(0, total_rows - max(1, visible_rows))
    return min(max(0, offset), max_offset)


def rendered_body_row_count(
    root: Path,
    *,
    width: int,
    rich: bool,
    expand_done: bool,
) -> int:
    view = _load(root)
    return len(
        _body_lines(
            view,
            width=width,
            max_rows=None,
            ascii_=not rich,
            expand_done=expand_done,
        )
    )


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
    expand_done: bool = False,
    interactive: bool = False,
    scroll_offset: int = 0,
) -> str:
    cols, rows = size if size is not None else shutil.get_terminal_size((80, 24))
    ascii_ = not rich
    view = _load(root)

    if cols < MIN_WIDTH_ONELINE:
        return _emit([_crop_line([(_one_line(view, root, ascii_), "bold")], cols)], rich=rich, width=cols)

    if view.roadmap is None:
        lines = [
            _crop_line([(_one_line(view, root, ascii_), "bold")], cols),
            _crop_line([(" run $wily-init to start", "dim")], cols),
            _rule_line(cols, ascii_),
            _footer_line(root, width=cols, ascii_=ascii_, interactive=interactive, expand_done=expand_done),
        ]
        return _emit(lines, rich=rich, width=cols)

    max_rows = max(1, rows - CHROME_ROWS) if rows else None
    body = _body_lines(
        view,
        width=cols,
        max_rows=max_rows,
        ascii_=ascii_,
        expand_done=expand_done,
        scroll_offset=scroll_offset,
    )
    lines = [
        _header_line(version=view.version, interval=interval, width=cols, ascii_=ascii_),
        _progress_line(done=view.done, total=view.total, width=cols, ascii_=ascii_),
        _rule_line(cols, ascii_),
        *body,
        _rule_line(cols, ascii_),
        _footer_line(root, width=cols, ascii_=ascii_, interactive=interactive, expand_done=expand_done),
    ]
    return _emit(lines, rich=rich, width=cols)
