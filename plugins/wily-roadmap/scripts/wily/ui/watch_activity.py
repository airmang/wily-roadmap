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
    header = "활동"
    lines.append((header, "bold"))
    lines.append((rule * width, "dim"))
    if not actors:
        lines.append(("작업자가 정의되지 않았습니다.", "dim"))
        return lines
    for actor in actors:
        current_tasks = []
        for task in tasks:
            if task.actor == actor.id and task.status == TaskStatus.IN_PROGRESS:
                current_tasks.append(task)
        last_done = None
        for task in tasks:
            if task.actor == actor.id and task.status == TaskStatus.DONE and task.done_at:
                if last_done is None or (task.done_at and task.done_at > last_done.done_at):
                    last_done = task
        lines.append((actor.id, "bold"))
        if current_tasks:
            current_task = current_tasks[0]
            cp = cp_summaries.get(current_task.id)
            cp_text = f" {cp.current_cp}" if cp and cp.current_cp else ""
            more = f" 외 {len(current_tasks) - 1}" if len(current_tasks) > 1 else ""
            lines.append((f"  현재: {current_task.id}{cp_text}{more}", "cyan"))
        else:
            lines.append(("  현재: —", "dim"))
        capacity = max(actor.capacity, 1)
        used = len(current_tasks)
        capacity_style = "red" if used > capacity else "yellow" if used == capacity else "green"
        lines.append((f"  여력: {used}/{capacity}", capacity_style))
        hints = [
            task.capacity_hint
            for task in tasks
            if task.assignee == actor.id and task.status == TaskStatus.READY and task.capacity_hint
        ]
        if hints:
            lines.append((f"  추천 여력: {max(hints)}", "dim"))
        if last_done:
            lines.append((f"  최근 완료: {last_done.id}", "green dim"))
        else:
            lines.append(("  최근 완료: —", "dim"))
        lines.append(("", ""))
    return lines
