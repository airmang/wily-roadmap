"""Pure renderer for `wily status` and `wily watch`."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from shutil import get_terminal_size
import sys
import unicodedata

from ..models import Actor, Task, TaskStatus
from ..observation import CommitInfo, guess_task_id, match_actor
from ..progress import CpSummary
from .watch_layout import WatchLayoutConfig
from .watch_activity import build_activity_lines

STATUS_META = {
    TaskStatus.DONE: ("●", "완료", "green dim"),
    TaskStatus.IN_PROGRESS: ("◐", "진행 중", "bold yellow"),
    TaskStatus.READY: ("▶", "대기", "bold cyan"),
    TaskStatus.BLOCKED: ("✗", "차단", "bold red"),
}
STATUS_META_ASCII = {
    TaskStatus.DONE: ("*", "완료", ""),
    TaskStatus.IN_PROGRESS: ("~", "진행 중", ""),
    TaskStatus.READY: (">", "대기", ""),
    TaskStatus.BLOCKED: ("x", "차단", ""),
}
STATUS_DISPLAY = {
    TaskStatus.DONE: "완료",
    TaskStatus.IN_PROGRESS: "진행 중",
    TaskStatus.READY: "대기",
    TaskStatus.BLOCKED: "차단",
}
STATUS_PRIORITY = {
    TaskStatus.IN_PROGRESS: 0,
    TaskStatus.BLOCKED: 1,
    TaskStatus.READY: 2,
    TaskStatus.DONE: 3,
}


@dataclass
class WatchRow:
    task_id: str
    glyph: str
    status_label: str
    style: str
    actor_display: str
    title: str
    cp_gauge: str = ""
    cp_timeline: str = ""
    blocker: str | None = None
    dependency_text: str | None = None
    parallel_lane: str | None = None
    priority: int | None = None
    parallel_text: str | None = None
    capacity_text: str | None = None
    conflict_text: str | None = None
    meta_text: str | None = None
    guessed_text: str | None = None


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def _display_width(text: str) -> int:
    total = 0
    for char in text:
        total += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return total


def _meta_for_task(task: Task) -> str | None:
    if task.status == TaskStatus.DONE and task.done_at:
        return f"[완료: {task.done_at}]"
    if task.status == TaskStatus.IN_PROGRESS and task.claim_at:
        return f"[시작: {task.claim_at}]"
    if task.depends_on:
        pending = [d for d in task.depends_on]
        if pending:
            return f"[의존: {','.join(pending)}]"
    return None


def _dependency_text_for_task(task: Task, task_map: dict[str, Task]) -> str | None:
    if not task.depends_on:
        return None
    pending = []
    for dep_id in task.depends_on:
        dep = task_map.get(dep_id)
        if dep is None:
            pending.append(f"{dep_id} (누락)")
        elif dep.status != TaskStatus.DONE:
            pending.append(f"{dep_id} ({STATUS_DISPLAY[dep.status]})")
    if pending:
        return f"대기 중: {', '.join(pending)}"
    return None


def _dependencies_satisfied(task: Task, task_map: dict[str, Task]) -> bool:
    return all((dep := task_map.get(dep_id)) and dep.status == TaskStatus.DONE for dep_id in task.depends_on)


def _parallel_text_for_task(task: Task) -> str | None:
    lane = task.parallel_lane or "기본"
    parts = [f"레인 {lane}"]
    if task.priority is not None:
        parts.append(f"우선순위 {task.priority}")
    if task.capacity_hint is not None:
        parts.append(f"필요 여력 {task.capacity_hint}")
    if not task.parallel_lane and task.priority is None and task.capacity_hint is None:
        return None
    return "병렬: " + " · ".join(parts)


def _capacity_text_for_task(
    task: Task,
    *,
    actor_map: dict[str, Actor],
    active_counts: dict[str, int],
) -> str | None:
    actor_id = task.assignee or task.actor
    if not actor_id:
        return None
    actor = actor_map.get(actor_id)
    capacity = actor.capacity if actor else 1
    capacity = max(capacity, 1)
    used = active_counts.get(actor_id, 0)
    label = "작업자 여력"
    if used >= capacity:
        return f"{label}: {actor_id} {used}/{capacity} (여력 없음)"
    return f"{label}: {actor_id} {used}/{capacity}"


def _scope_conflict_text(task: Task, tasks: list[Task]) -> str | None:
    if task.status != TaskStatus.READY or not task.scope:
        return None
    conflicts = []
    for other in tasks:
        if other.id == task.id or other.status != TaskStatus.IN_PROGRESS or not other.scope:
            continue
        if _scopes_overlap(task.scope, other.scope):
            conflicts.append(other.id)
    if not conflicts:
        return None
    return f"충돌 가능: {', '.join(conflicts)} (scope 겹침)"


def _scopes_overlap(left: list[str], right: list[str]) -> bool:
    for left_item in left:
        for right_item in right:
            if _scope_items_overlap(left_item, right_item):
                return True
    return False


def _scope_items_overlap(left: str, right: str) -> bool:
    left_base = _scope_base(left)
    right_base = _scope_base(right)
    if not left_base or not right_base:
        return False
    return (
        left_base == right_base
        or left_base.startswith(right_base.rstrip("/") + "/")
        or right_base.startswith(left_base.rstrip("/") + "/")
    )


def _scope_base(value: str) -> str:
    cleaned = value.strip()
    if "*" in cleaned:
        cleaned = cleaned.split("*", 1)[0].rstrip("/")
    return cleaned.rstrip("/")


def build_grouped_rows(
    tasks: list[Task],
    *,
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    ascii_mode: bool = False,
    show_timeline: bool = False,
) -> dict[TaskStatus, list[WatchRow]]:
    meta = STATUS_META_ASCII if ascii_mode else STATUS_META
    task_map = {t.id: t for t in tasks}
    actor_map = {actor.id: actor for actor in actors}
    active_counts: dict[str, int] = {}
    for task in tasks:
        if task.status == TaskStatus.IN_PROGRESS and task.actor:
            active_counts[task.actor] = active_counts.get(task.actor, 0) + 1
    grouped: dict[TaskStatus, list[WatchRow]] = {
        TaskStatus.IN_PROGRESS: [],
        TaskStatus.BLOCKED: [],
        TaskStatus.READY: [],
        TaskStatus.DONE: [],
    }
    for task in tasks:
        cp = cp_summaries.get(task.id)
        gauge = ""
        timeline = ""
        if cp and cp.total:
            full, empty = ("#", "-") if ascii_mode else ("█", "░")
            left, right = ("[", "]") if ascii_mode else ("▕", "▏")
            blocks = full * cp.done + empty * max(cp.total - cp.done, 0)
            current = f" 현재:{cp.current_cp}" if cp.current_cp else ""
            gauge = f"{left}{blocks}{right} {cp.done}/{cp.total}{current}"
            if show_timeline and cp.cp_names:
                if ascii_mode:
                    timeline_parts = []
                    for name in cp.cp_names:
                        if timeline_parts:
                            timeline_parts.append(">")
                        done_set = {e.cp for e in []}
                        is_done = name in done_set
                        is_current = cp.current_cp == name
                        if is_done:
                            timeline_parts.append(f"[{name}]")
                        elif is_current:
                            timeline_parts.append(f"{{{name}}}")
                        else:
                            timeline_parts.append(name)
                    timeline = " ".join(timeline_parts)
                else:
                    timeline_parts = []
                    for name in cp.cp_names:
                        if timeline_parts:
                            timeline_parts.append(" › ")
                        is_current = cp.current_cp == name
                        if is_current:
                            timeline_parts.append(name)
                        else:
                            timeline_parts.append(name)
                    timeline = "".join(timeline_parts)
                    if cp.current_cp and cp.current_cp in cp.cp_names:
                        idx = cp.cp_names.index(cp.current_cp)
                        timeline += f"  ↑ {cp.current_cp}"
        glyph, status_label, style = meta[task.status]
        row = WatchRow(
            task_id=task.id,
            glyph=glyph,
            status_label=status_label,
            style=style,
            actor_display=task.actor or task.assignee or "—",
            title=task.title,
            cp_gauge=gauge,
            cp_timeline=timeline,
            blocker=task.blocker,
            dependency_text=_dependency_text_for_task(task, task_map),
            parallel_lane=task.parallel_lane,
            priority=task.priority,
            parallel_text=_parallel_text_for_task(task) if task.status == TaskStatus.READY and _dependencies_satisfied(task, task_map) else None,
            capacity_text=_capacity_text_for_task(task, actor_map=actor_map, active_counts=active_counts)
            if task.status == TaskStatus.READY and _dependencies_satisfied(task, task_map)
            else None,
            conflict_text=_scope_conflict_text(task, tasks),
            meta_text=_meta_for_task(task),
        )
        grouped[task.status].append(row)
    for commit in observed_commits:
        if commit.trailers.get("Wily-Task"):
            continue
        actor = match_actor(actors, email=commit.author_email, name=commit.author_name)
        guessed = guess_task_id(tasks, commit.files)
        row = WatchRow(
            task_id="-",
            glyph=">" if ascii_mode else "⏵",
            status_label="관찰",
            style="dim",
            actor_display=actor.id if actor else "알 수 없음",
            title=commit.subject,
            guessed_text=f"추정 태스크: {guessed} (트레일러 없음)" if guessed else "범위 일치 없음",
        )
        grouped.setdefault(TaskStatus.READY, []).append(row)
    return grouped


def rich_available() -> bool:
    try:
        import rich.console  # noqa: F401
    except ImportError:
        _add_watch_venv_site_packages()
        try:
            import rich.console  # noqa: F401
        except ImportError:
            return False
    return True


def _add_watch_venv_site_packages() -> None:
    candidates = [Path.cwd() / ".venv-watch"]
    candidates.extend(parent / ".venv-watch" for parent in Path(__file__).resolve().parents)
    for venv in candidates:
        lib_dir = venv / "lib"
        if not lib_dir.exists():
            continue
        for site_packages in lib_dir.glob("python*/site-packages"):
            site_path = str(site_packages)
            if site_path not in sys.path:
                sys.path.insert(0, site_path)


def render_watch(
    *,
    project_title: str,
    tasks: list[Task],
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    mode: str,
    ui: str = "auto",
    compact: bool = False,
    show_timeline: bool = False,
    show_log: bool = True,
) -> str:
    if ui not in {"auto", "rich", "ascii"}:
        raise ValueError(f"unknown watch ui: {ui}")
    ascii_mode = ui == "ascii"
    rich_requested = ui in {"auto", "rich"} and not ascii_mode
    rich_enabled = rich_requested and rich_available()
    term_width = max(72, min(get_terminal_size((96, 24)).columns, 160))
    layout = WatchLayoutConfig(
        width=term_width,
        ascii_mode=ascii_mode,
        compact=compact,
        show_observed=show_log,
        show_checkpoint_timeline=show_timeline,
    )
    lines = _styled_lines(
        project_title=project_title,
        tasks=tasks,
        actors=actors,
        observed_commits=observed_commits,
        cp_summaries=cp_summaries,
        mode=mode,
        ascii_mode=ascii_mode,
        layout=layout,
        show_timeline=show_timeline,
        show_log=show_log,
    )
    body = _render_rich(lines) if rich_enabled else "\n".join(text for text, _style in lines)
    if ui == "rich" and not rich_enabled:
        return "\n".join(
            [
                "Rich UI is not installed.",
                "Run: python3 -m pip install -r plugins/wily-roadmap/requirements-watch.txt",
                "Fallback: using plain watch UI.",
                body,
            ]
        )
    return body


def _header_lines(
    project_title: str,
    mode: str,
    *,
    ascii_mode: bool,
    width: int,
) -> list[tuple[str, str]]:
    rule = "-" if ascii_mode else "─"
    return [
        (f"Wily Roadmap v3  {project_title or '(제목 없음)'}", "bold"),
        (rule * width, "dim"),
    ]


def _summary_lines(
    tasks: list[Task],
    mode: str,
    *,
    ascii_mode: bool,
    width: int,
) -> list[tuple[str, str]]:
    rule = "-" if ascii_mode else "─"
    left, right = ("[", "]") if ascii_mode else ("▕", "▏")
    full, empty = ("#", "-") if ascii_mode else ("█", "░")
    done = sum(1 for task in tasks if task.status == TaskStatus.DONE)
    total = len(tasks)
    blocked = sum(1 for task in tasks if task.status == TaskStatus.BLOCKED)
    active = sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS)
    done_ids = {task.id for task in tasks if task.status == TaskStatus.DONE}
    parallel_ready = sum(
        1 for task in tasks if task.status == TaskStatus.READY and all(dep_id in done_ids for dep_id in task.depends_on)
    )
    bar_width = max(10, min(width // 3, 28))
    filled = int(round((done / total) * bar_width)) if total else 0
    bar = full * filled + empty * max(bar_width - filled, 0)
    pct = int(round((done / total) * 100)) if total else 0
    kpi_parts = []
    if blocked or active:
        kpi_parts.extend([f"차단 {blocked}", f"진행 {active}"])
    if parallel_ready:
        kpi_parts.append(f"병렬 가능 {parallel_ready}")
    kpi = "  ".join(kpi_parts)
    progress = f"진행률 {left}{bar}{right}  {done}/{total} · {pct}%"
    if kpi:
        progress += f"   {kpi}"
    return [
        (progress, "green" if done == total and total else "cyan"),
        (f"모드 {_mode_label(mode)}", "dim"),
        (rule * width, "dim"),
    ]


def _mode_label(mode: str) -> str:
    return {"solo": "단독", "shared": "공유", "collab": "협업"}.get(mode, mode)


def _task_group_lines(
    grouped: dict[TaskStatus, list[WatchRow]],
    *,
    ascii_mode: bool,
    width: int,
    compact: bool,
    show_timeline: bool,
) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    group_labels = {
        TaskStatus.IN_PROGRESS: "진행 중",
        TaskStatus.BLOCKED: "차단",
        TaskStatus.READY: "대기",
        TaskStatus.DONE: "완료",
    }
    for status in [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.READY, TaskStatus.DONE]:
        rows = grouped.get(status, [])
        if not rows:
            continue
        sections = [(group_labels[status], rows)]
        if status == TaskStatus.READY:
            ready_rows = [row for row in rows if not row.dependency_text and not row.guessed_text]
            waiting_rows = [row for row in rows if row.dependency_text]
            observed_rows = [row for row in rows if row.guessed_text]
            sections = []
            if ready_rows:
                sections.append(("병렬 가능", _sort_parallel_rows(ready_rows)))
            if waiting_rows:
                sections.append(("의존 대기", waiting_rows))
            if observed_rows:
                sections.append(("관찰", observed_rows))
        for label, section_rows in sections:
            lines.extend(
                _task_section_lines(
                    label,
                    section_rows,
                    ascii_mode=ascii_mode,
                    width=width,
                    compact=compact,
                    show_timeline=show_timeline,
                )
            )
    return lines


def _sort_parallel_rows(rows: list[WatchRow]) -> list[WatchRow]:
    def key(row: WatchRow) -> tuple[int, str, str]:
        priority = row.priority if row.priority is not None else 999
        return (priority, row.parallel_text or "", row.task_id)

    return sorted(rows, key=key)


def _task_section_lines(
    label: str,
    rows: list[WatchRow],
    *,
    ascii_mode: bool,
    width: int,
    compact: bool,
    show_timeline: bool,
) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    rule = "-" if ascii_mode else "─"
    max_title_width = max(20, width - 40)
    if not compact:
        prefix = f"{rule}{rule} {label} "
        fill = rule * max(0, width - _display_width(prefix) - 1)
        header_text = f"{prefix}{fill}"
        lines.append((header_text[:width], "dim"))
    for index, row in enumerate(rows):
        branch = "\\-" if ascii_mode and index == len(rows) - 1 else "+-" if ascii_mode else "└─" if index == len(rows) - 1 else "├─"
        title = _truncate(row.title, max_title_width)
        meta = row.meta_text or ""
        line = f"{branch} {row.glyph} {row.task_id:<5} {row.status_label:<12} {row.actor_display:<10} {title}"
        if meta and not compact:
            remaining = width - len(line) - 1
            if remaining > 10:
                line += " " + meta[:remaining]
        lines.append((line, row.style))
        detail_texts = [row.parallel_text, row.capacity_text, row.conflict_text]
        for detail in [item for item in detail_texts if item]:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            style = "red" if detail.startswith("충돌 가능") else "cyan"
            lines.append((f"{rail}    {detail}", style))
        if row.cp_gauge:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            cp_line = f"{rail}    체크포인트 {row.cp_gauge}"
            if row.cp_timeline and show_timeline:
                remaining = width - len(cp_line) - 2
                if remaining > 10:
                    cp_line += "  " + row.cp_timeline[:remaining]
            lines.append((cp_line, "green"))
        if row.blocker:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            blocker_prefix = "! " if ascii_mode else ""
            lines.append((f"{rail}    {blocker_prefix}차단 사유: {row.blocker}", "red"))
        if row.dependency_text:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            lines.append((f"{rail}    {row.dependency_text}", "yellow"))
        if row.guessed_text:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            child = "\\-" if ascii_mode else "└─"
            lines.append((f"{rail}    {child} {row.guessed_text}", "dim"))
    return lines


def _observed_lines(
    observed_commits: list[CommitInfo],
    *,
    ascii_mode: bool,
    width: int,
    compact: bool,
    show_log: bool,
) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    if not show_log:
        return lines
    if not observed_commits:
        return lines
    rule = "-" if ascii_mode else "─"
    if not compact:
        lines.append((rule * width, "dim"))
        lines.append((f"관찰됨  분기 이후 커밋 {len(observed_commits)}개", "dim"))
    else:
        lines.append((f"관찰된 커밋 {len(observed_commits)}개", "dim"))
        return lines
    for commit in observed_commits[:10]:
        sha = commit.sha[:7]
        line = f"{'>' if ascii_mode else '⏵'} {sha}  {commit.author_email:<20}  \"{commit.subject[:40]}\""
        lines.append((line, "dim"))
    return lines


def _styled_lines(
    *,
    project_title: str,
    tasks: list[Task],
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    mode: str,
    ascii_mode: bool,
    layout: WatchLayoutConfig,
    show_timeline: bool,
    show_log: bool,
) -> list[tuple[str, str]]:
    width = layout.width
    lines: list[tuple[str, str]] = []
    lines.extend(_header_lines(project_title, mode, ascii_mode=ascii_mode, width=width))
    lines.extend(_summary_lines(tasks, mode, ascii_mode=ascii_mode, width=width))
    grouped = build_grouped_rows(
        tasks,
        actors=actors,
        observed_commits=observed_commits,
        cp_summaries=cp_summaries,
        ascii_mode=ascii_mode,
        show_timeline=show_timeline,
    )
    task_lines = _task_group_lines(
        grouped,
        ascii_mode=ascii_mode,
        width=layout.task_pane_width if layout.show_activity_panel else width,
        compact=layout.compact,
        show_timeline=show_timeline,
    )
    if layout.show_activity_panel:
        activity_lines = build_activity_lines(
            actors, tasks, cp_summaries, ascii_mode=ascii_mode, width=layout.activity_pane_width
        )
        lines.extend(_merge_panels(task_lines, activity_lines, width))
    else:
        lines.extend(task_lines)
    lines.extend(_observed_lines(observed_commits, ascii_mode=ascii_mode, width=width, compact=layout.compact, show_log=show_log))
    return lines


def _merge_panels(
    left: list[tuple[str, str]],
    right: list[tuple[str, str]],
    width: int,
) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    max_left = 0
    for text, _ in left:
        max_left = max(max_left, len(text))
    left_width = min(max_left + 2, width // 2)
    right_start = left_width + 1
    for i in range(max(len(left), len(right))):
        left_text = left[i][0] if i < len(left) else ""
        right_text = right[i][0] if i < len(right) else ""
        left_style = left[i][1] if i < len(left) else ""
        right_style = right[i][1] if i < len(right) else ""
        pad = left_width - len(left_text)
        combined = left_text + " " * max(1, pad) + right_text
        if right_text and left_text:
            merged.append((combined, f"{left_style};{right_style}" if left_style and right_style else (left_style or right_style)))
        elif left_text:
            merged.append((left_text, left_style))
        else:
            merged.append((" " * right_start + right_text, right_style))
    return merged


def _render_rich(lines: list[tuple[str, str]]) -> str:
    from rich.console import Console

    sink = StringIO()
    console = Console(
        file=sink,
        record=True,
        force_terminal=True,
        color_system="truecolor",
        width=get_terminal_size((96, 24)).columns,
    )
    for text, style in lines:
        console.print(text, style=style or None)
    return console.export_text(styles=True).rstrip("\n")
