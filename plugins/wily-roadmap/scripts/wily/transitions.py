"""Pure task state transitions and dependency validation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .models import Task, TaskStatus


class TransitionError(Exception):
    """Raised when a task state transition is invalid."""


class DependencyError(Exception):
    """Raised when task dependencies are missing or cyclic."""


def apply_claim(
    task: Task,
    *,
    actor: str,
    sha: str | None,
    at: str,
    claim_snapshot: dict[str, Any] | None = None,
    force: bool = False,
) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(f"{task.id} is done; cannot claim")
    if task.status == TaskStatus.IN_PROGRESS and not force:
        raise TransitionError(
            f"{task.id} is already in_progress by {task.actor or '?'}; use --force"
        )
    return replace(
        task,
        status=TaskStatus.IN_PROGRESS,
        actor=actor,
        claim_sha=sha,
        claim_snapshot=claim_snapshot,
        claim_at=at,
        blocker=None,
    )


def apply_done(task: Task, *, at: str, force: bool = False) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(f"{task.id} is already done")
    if task.status != TaskStatus.IN_PROGRESS and not force:
        raise TransitionError(f"{task.id} is {task.status.value}; claim first")
    return replace(task, status=TaskStatus.DONE, done_at=at, blocker=None)


def apply_block(task: Task, *, reason: str) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(f"{task.id} is done; cannot block")
    if task.status not in {TaskStatus.READY, TaskStatus.IN_PROGRESS}:
        raise TransitionError(f"{task.id} is {task.status.value}; cannot block")
    return replace(task, status=TaskStatus.BLOCKED, blocker=reason)


def check_dependencies(tasks: Iterable[Task]) -> None:
    task_list = list(tasks)
    by_id = {task.id: task for task in task_list}
    for task in task_list:
        for dep in task.depends_on:
            if dep == task.id:
                raise DependencyError(f"{task.id} depends on itself")
            if dep not in by_id:
                raise DependencyError(f"{task.id} depends on missing task {dep}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, stack: list[str]) -> None:
        if task_id in visiting:
            raise DependencyError("dependency cycle: " + " -> ".join(stack + [task_id]))
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in by_id[task_id].depends_on:
            visit(dep, stack + [task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task in task_list:
        visit(task.id, [])
