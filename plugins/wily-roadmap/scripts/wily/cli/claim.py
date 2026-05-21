"""`wily claim <id>` - transition a task into progress."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..config import load_actors, load_tasks, save_tasks
from ..coordination import ProjectContext, nested_repo_exclusions, resolve_project_context
from ..models import Actor
from ..observation import claim_snapshot_for_repos, git_config_identity, head_sha, match_actor
from ..paths import WilyPaths, WilyRootNotFound, touch_wily
from ..progress import init_progress
from ..transitions import TransitionError, apply_claim
from . import _common

DESCRIPTION = "transition a task into progress"
USAGE = "usage: wily claim <task-id> [--force] [--allow-empty] [--as <actor-id>] [--json]"
HELP = "\n".join(
    [
        "Options:",
        "  --force        reclaim an already in-progress task",
        "  --allow-empty  allow empty intent or acceptance fields",
        "  --as <actor>   claim as a configured actor id",
        "  --json         emit the updated task as JSON",
    ]
)


def main(args: list[str]) -> int:
    args, as_json = _common.consume_json_flag(args)
    force = "--force" in args
    allow_empty = "--allow-empty" in args
    as_actor_id = _common.extract_value(args, "--as")
    positional = _common.positionals(args, value_flags={"--as"})
    if len(positional) != 1:
        _common.emit_error("usage: wily claim <task-id> [--force] [--allow-empty]")
        return _common.EXIT_USAGE
    task_id = positional[0]
    try:
        context = resolve_project_context(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    root = context.paths.root
    paths = context.paths
    project_title, tasks = load_tasks(paths)
    email, name = git_config_identity(root)
    actors = load_actors(paths)
    actor = _actor_by_id(actors, as_actor_id) if as_actor_id else match_actor(actors, email=email, name=name)
    if actor is None:
        if as_actor_id:
            _common.emit_error(f"actor not found: {as_actor_id}")
        else:
            _emit_actor_mismatch(paths, email=email, name=name)
        return _common.EXIT_FAILURE
    task = next((item for item in tasks if item.id == task_id), None)
    if task is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    missing = _missing_plan_fields(root, task)
    if missing and not allow_empty:
        _common.emit_error(
            f"{task_id} has empty {', '.join(missing)}; revise the task or rerun with --allow-empty"
        )
        return _common.EXIT_TRANSITION
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        claim_sha = None if context.active_mode == "coordination" else head_sha(root)
        claim_snapshot = _claim_snapshot(context) if context.active_mode == "coordination" else None
        updated = apply_claim(
            task,
            actor=actor.id,
            sha=claim_sha,
            at=now,
            claim_snapshot=claim_snapshot,
            force=force,
        )
    except TransitionError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_TRANSITION
    save_tasks(paths, project_title, [updated if item.id == task_id else item for item in tasks])
    init_progress(paths, task_id)
    touch_wily(paths)
    if task.assignee and task.assignee != actor.id:
        warning = f"warning: task assignee is {task.assignee}, actor is {actor.id}"
        (_common.emit_error if as_json else _common.emit_text)(warning)
    if as_json:
        _common.emit_json({"task": updated.to_dict(), "progress_jsonl": str(paths.progress_jsonl(task_id).relative_to(root))})
        return _common.EXIT_OK
    _common.emit_text(f"{task_id}: {task.status.value} -> in_progress")
    _common.emit_text(f"actor: {actor.id} ({email or '-'})")
    if updated.claim_sha:
        _common.emit_text(f"claim_sha: {updated.claim_sha[:7]}")
    elif updated.claim_snapshot:
        _common.emit_text("claim_snapshot: recorded")
    else:
        _common.emit_text("claim_sha: -")
    _common.emit_text(f"progress.jsonl initialized: {paths.progress_jsonl(task_id).relative_to(root)}")
    return _common.EXIT_OK


def _claim_snapshot(context: ProjectContext) -> dict[str, object]:
    if context.coordination is None:
        return claim_snapshot_for_repos([("root", context.root)])
    exclude_paths_by_repo = {
        repo.id: nested_repo_exclusions(context.coordination, repo)
        for repo in context.coordination.all_repos
    }
    return claim_snapshot_for_repos(
        ((repo.id, repo.path) for repo in context.coordination.all_repos),
        exclude_paths_by_repo=exclude_paths_by_repo,
    )


def _missing_plan_fields(root: Path, task) -> list[str]:
    missing = []
    if not task.intent.strip():
        missing.append("intent")
    acceptance = task.acceptance_text
    if not acceptance and task.acceptance_file:
        candidate = root / task.acceptance_file
        if candidate.exists():
            acceptance = candidate.read_text(encoding="utf-8")
    if not acceptance.strip():
        missing.append("acceptance")
    return missing


def _actor_by_id(actors: list[Actor], actor_id: str | None) -> Actor | None:
    return next((actor for actor in actors if actor.id == actor_id), None)


def _emit_actor_mismatch(paths: WilyPaths, *, email: str, name: str) -> None:
    actor_id = _suggest_actor_id(email=email, name=name)
    _common.emit_error("no actor matches current git author; update actors.yaml or use --as <actor_id>")
    _common.emit_error(f"current git author: {name or '-'} <{email or '-'}>")
    _common.emit_error("suggested actors.yaml entry:")
    _common.emit_error("actors:")
    _common.emit_error(f"  {actor_id}:")
    _common.emit_error(f"    display: {name or actor_id}")
    _common.emit_error("    git_author_emails:")
    _common.emit_error(f"      - {email or 'you@example.com'}")
    _common.emit_error(f"or run: wily replan actor add {actor_id} --email={email or 'you@example.com'}")


def _suggest_actor_id(*, email: str, name: str) -> str:
    if email and "@" in email:
        return email.split("@", 1)[0].replace(".", "-").replace("_", "-")
    if name:
        return "-".join(part.lower() for part in name.split())
    return "new-actor"
