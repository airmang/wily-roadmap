from __future__ import annotations

from ..models import Actor, Task, TaskStatus
from ..progress import CpSummary


def build_activity_lines(
    actors: list[Actor],
    tasks: list[Task],
    cp_summaries: dict[str, CpSummary],
    *,
    ascii_mode: bool = False,
    width: int = 40,
) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    rule = "-" if ascii_mode else "─"
    header = "ACTIVITY"
    lines.append((header, "bold"))
    lines.append((rule * width, "dim"))
    if not actors:
        lines.append(("No actors defined.", "dim"))
        return lines
    task_map = {task.id: task for task in tasks}
    for actor in actors:
        current_task = None
        for task in tasks:
            if task.actor == actor.id and task.status == TaskStatus.IN_PROGRESS:
                current_task = task
                break
        last_done = None
        for task in tasks:
            if task.actor == actor.id and task.status == TaskStatus.DONE and task.done_at:
                if last_done is None or (task.done_at and task.done_at > last_done.done_at):
                    last_done = task
        lines.append((actor.id, "bold"))
        if current_task:
            cp = cp_summaries.get(current_task.id)
            cp_text = f" {cp.current_cp}" if cp and cp.current_cp else ""
            lines.append((f"  current: {current_task.id}{cp_text}", "cyan"))
        else:
            lines.append(("  current: —", "dim"))
        if last_done:
            lines.append((f"  last done: {last_done.id}", "green dim"))
        else:
            lines.append(("  last done: —", "dim"))
        lines.append(("", ""))
    return lines
