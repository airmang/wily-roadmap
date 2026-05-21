"""`wily next` - print the next ready task."""

from __future__ import annotations

from pathlib import Path

from ..config import load_actors, load_tasks
from ..coordination import resolve_project_context
from ..models import Task, TaskStatus
from ..observation import git_config_identity, match_actor
from ..paths import WilyRootNotFound
from ..scheduling import parallel_candidates, waiting_candidates
from . import _common

DESCRIPTION = "print the next ready task"
USAGE = "usage: wily next [--mine] [--all|--parallel] [--json]"
HELP = "\n".join(
    [
        "Options:",
        "  --mine      restrict candidates to the current actor",
        "  --all       print all parallel and waiting candidates",
        "  --parallel  alias for --all",
        "  --json      emit candidates as JSON",
    ]
)


def main(args: list[str]) -> int:
    args, as_json = _common.consume_json_flag(args)
    mine = "--mine" in args
    all_candidates = "--all" in args or "--parallel" in args
    try:
        context = resolve_project_context(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    root = context.paths.root
    paths = context.paths
    _, tasks = load_tasks(paths)
    actor_id = None
    if mine:
        email, name = git_config_identity(root)
        actor = match_actor(load_actors(paths), email=email, name=name)
        if actor is None:
            _common.emit_error("no actor matches current git author; update actors.yaml")
            return _common.EXIT_FAILURE
        actor_id = actor.id if actor else None
    if all_candidates:
        parallel = parallel_candidates(tasks, mine_actor_id=actor_id)
        waiting = waiting_candidates(tasks, mine_actor_id=actor_id)
        if not parallel and not waiting:
            _common.emit_error("no ready task with satisfied dependencies")
            return _common.EXIT_FAILURE
        if as_json:
            payload = {
                "parallel": [task.to_dict() for task in parallel],
                "waiting": [task.to_dict() for task in waiting],
            }
            if context.active_mode == "coordination":
                payload["active_mode"] = context.active_mode
            _common.emit_json(payload)
        else:
            for task in parallel:
                _emit_task_line(task, status="parallel")
            for task in waiting:
                _emit_task_line(task, status="waiting")
        return _common.EXIT_OK
    task = next_task(tasks, mine_actor_id=actor_id)
    if task is None:
        _common.emit_error("no ready task with satisfied dependencies")
        return _common.EXIT_FAILURE
    if as_json:
        if context.active_mode == "coordination":
            _common.emit_json({"active_mode": context.active_mode, "task": task.to_dict()})
        else:
            _common.emit_json(task.to_dict())
    else:
        _emit_task_line(task, status="ready")
    return _common.EXIT_OK


def next_task(tasks: list[Task], *, mine_actor_id: str | None = None) -> Task | None:
    candidates = parallel_candidates(tasks, mine_actor_id=mine_actor_id)
    return candidates[0] if candidates else None


def _emit_task_line(task: Task, *, status: str) -> None:
    deps = ",".join(task.depends_on) if task.depends_on else "-"
    _common.emit_text(
        f"{task.id} {status}  {task.title!r}  assignee={task.assignee or '-'}  depends_on=[{deps}]"
    )
