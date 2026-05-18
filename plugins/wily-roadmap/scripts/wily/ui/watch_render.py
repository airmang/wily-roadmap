"""Pure renderer for `wily status` and `wily watch`."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from shutil import get_terminal_size
import sys

from ..models import Actor, Task, TaskStatus
from ..observation import CommitInfo, guess_task_id, match_actor
from ..progress import CpSummary

STATUS_META = {
    TaskStatus.DONE: ("●", "done", "green dim"),
    TaskStatus.IN_PROGRESS: ("◐", "in_progress", "bold yellow"),
    TaskStatus.READY: ("▶", "ready", "bold cyan"),
    TaskStatus.BLOCKED: ("✗", "blocked", "bold red"),
}
STATUS_META_ASCII = {
    TaskStatus.DONE: ("*", "done", ""),
    TaskStatus.IN_PROGRESS: ("~", "in_progress", ""),
    TaskStatus.READY: (">", "ready", ""),
    TaskStatus.BLOCKED: ("x", "blocked", ""),
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
    blocker: str | None = None
    guessed_text: str | None = None


def build_rows(
    tasks: list[Task],
    *,
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    ascii_mode: bool = False,
) -> list[WatchRow]:
    rows: list[WatchRow] = []
    meta = STATUS_META_ASCII if ascii_mode else STATUS_META
    for task in tasks:
        cp = cp_summaries.get(task.id)
        gauge = ""
        if cp and cp.total:
            full, empty = ("#", "-") if ascii_mode else ("█", "░")
            left, right = ("[", "]") if ascii_mode else ("▕", "▏")
            blocks = full * cp.done + empty * max(cp.total - cp.done, 0)
            current = f" current:{cp.current_cp}" if cp.current_cp else ""
            gauge = f"{left}{blocks}{right} {cp.done}/{cp.total} cp{current}"
        glyph, status_label, style = meta[task.status]
        rows.append(
            WatchRow(
                task_id=task.id,
                glyph=glyph,
                status_label=status_label,
                style=style,
                actor_display=task.actor or task.assignee or "-",
                title=task.title,
                cp_gauge=gauge,
                blocker=task.blocker,
            )
        )
    for commit in observed_commits:
        if commit.trailers.get("Wily-Task"):
            continue
        actor = match_actor(actors, email=commit.author_email, name=commit.author_name)
        guessed = guess_task_id(tasks, commit.files)
        rows.append(
            WatchRow(
                task_id="-",
                glyph=">" if ascii_mode else "⏵",
                status_label="observed",
                style="dim",
                actor_display=actor.id if actor else "unknown",
                title=commit.subject,
                guessed_text=f"guessed task: {guessed} (no trailer)" if guessed else "no scope match",
            )
        )
    return rows


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
) -> str:
    if ui not in {"auto", "rich", "ascii"}:
        raise ValueError(f"unknown watch ui: {ui}")
    ascii_mode = ui == "ascii"
    rich_requested = ui in {"auto", "rich"} and not ascii_mode
    rich_enabled = rich_requested and rich_available()
    lines = _styled_lines(
        project_title=project_title,
        tasks=tasks,
        actors=actors,
        observed_commits=observed_commits,
        cp_summaries=cp_summaries,
        mode=mode,
        ascii_mode=ascii_mode,
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


def _styled_lines(
    *,
    project_title: str,
    tasks: list[Task],
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    mode: str,
    ascii_mode: bool,
) -> list[tuple[str, str]]:
    width = max(72, min(get_terminal_size((96, 24)).columns, 132))
    rule = "-" if ascii_mode else "─"
    left, right = ("[", "]") if ascii_mode else ("▕", "▏")
    full, empty = ("#", "-") if ascii_mode else ("█", "░")
    done = sum(1 for task in tasks if task.status == TaskStatus.DONE)
    total = len(tasks)
    bar_width = max(10, min(width // 3, 28))
    filled = int(round((done / total) * bar_width)) if total else 0
    bar = full * filled + empty * max(bar_width - filled, 0)
    pct = int(round((done / total) * 100)) if total else 0
    lines: list[tuple[str, str]] = [
        (f"Wily Roadmap v3  {project_title or '(untitled)'}", "bold"),
        (rule * width, "dim"),
        (f"Progress {left}{bar}{right}  {done}/{total} · {pct}%", "green" if done == total and total else "cyan"),
        (f"Mode {mode}", "dim"),
    ]
    actor_summary = "  ·  ".join(
        f"{actor.id} {actor.git_author_emails[0]}" if actor.git_author_emails else actor.id
        for actor in actors
    )
    if actor_summary:
        lines.append((f"Actors {actor_summary}", "dim"))
    lines.append((rule * width, "dim"))

    rows = build_rows(
        tasks,
        actors=actors,
        observed_commits=observed_commits,
        cp_summaries=cp_summaries,
        ascii_mode=ascii_mode,
    )
    if not rows:
        lines.append(("No tasks yet.", "dim"))
        return lines
    for index, row in enumerate(rows):
        branch = "\\-" if ascii_mode and index == len(rows) - 1 else "+-" if ascii_mode else "└─" if index == len(rows) - 1 else "├─"
        line = f"{branch} {row.glyph} {row.task_id:<5} {row.status_label:<12} {row.actor_display:<10} {row.title}"
        lines.append((line, row.style))
        if row.cp_gauge:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            lines.append((f"{rail}    cp {row.cp_gauge}", "green"))
        if row.blocker:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            lines.append((f"{rail}    blocker: {row.blocker}", "red"))
        if row.guessed_text:
            rail = " " if index == len(rows) - 1 else "|" if ascii_mode else "│"
            child = "\\-" if ascii_mode else "└─"
            lines.append((f"{rail}    {child} {row.guessed_text}", "dim"))
    return lines


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
