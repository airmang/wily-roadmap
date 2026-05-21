"""`wily doctor` - check local Wily project health."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from ..config import SCHEMA_VERSION, load_actors, load_tasks
from ..coordination import load_coordination_config
from ..models import TaskStatus
from ..paths import WilyPaths, WilyRootNotFound, find_wily_root
from . import _common

DESCRIPTION = "check local Wily project health"
USAGE = "usage: wily doctor [--fix] [--json]"
HELP = "\n".join(
    [
        "Options:",
        "  --fix   apply safe repairs such as creating missing progress ledgers",
        "  --json  emit diagnostics as JSON",
    ]
)


@dataclass(frozen=True)
class Diagnostic:
    level: Literal["ok", "warn", "fail"]
    code: str
    message: str
    fixed: bool = False
    repo: str | None = None


def main(args: list[str]) -> int:
    args, as_json = _common.consume_json_flag(args)
    fix = "--fix" in args
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    diagnostics = run_checks(root, paths, fix=fix)
    if as_json:
        _common.emit_json({"diagnostics": [item.__dict__ for item in diagnostics]})
    else:
        for item in diagnostics:
            message = f"[{item.repo}] {item.message}" if item.repo else item.message
            line = f"{item.level}: {item.code}: {message}"
            if item.fixed:
                line += " (fixed)"
            (_common.emit_error if item.level in {"fail", "warn"} else _common.emit_text)(line)
    if any(item.level == "fail" and not item.fixed for item in diagnostics):
        return 2
    if any(item.level == "warn" for item in diagnostics):
        return 1
    return 0


def run_checks(root: Path, paths: WilyPaths, *, fix: bool = False) -> list[Diagnostic]:
    coordination_path = paths.wily_dir / "coordination.yaml"
    if coordination_path.is_file():
        return _coordination_checks(root, paths, fix=fix)
    return _single_repo_checks(root, paths, fix=fix)


def _coordination_checks(root: Path, paths: WilyPaths, *, fix: bool = False) -> list[Diagnostic]:
    try:
        coordination = load_coordination_config(paths.wily_dir / "coordination.yaml")
    except Exception as exc:
        return [
            Diagnostic("fail", "coordination-config", f"cannot load coordination config: {exc}", repo="parent"),
            *_single_repo_checks(root, paths, fix=fix, repo_id="parent", allow_non_git_hook=True),
        ]

    diagnostics: list[Diagnostic] = []
    diagnostics.append(Diagnostic("ok", "coordination-config", "coordination config is valid", repo=coordination.parent.id))
    for repo in coordination.all_repos:
        if not repo.path.exists():
            diagnostics.append(Diagnostic("fail", "coordination-repo-path", f"registered repo path does not exist: {repo.path}", repo=repo.id))
            continue
        if not repo.path.is_dir():
            diagnostics.append(Diagnostic("fail", "coordination-repo-path", f"registered repo path is not a directory: {repo.path}", repo=repo.id))
            continue
        diagnostics.extend(
            _single_repo_checks(
                repo.path,
                WilyPaths(repo.path),
                fix=fix,
                repo_id=repo.id,
                allow_non_git_hook=(repo.id == coordination.parent.id),
            )
        )
    return diagnostics


def _single_repo_checks(
    root: Path,
    paths: WilyPaths,
    *,
    fix: bool = False,
    repo_id: str | None = None,
    allow_non_git_hook: bool = False,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_schema_checks(paths, repo_id=repo_id))
    try:
        _, tasks = load_tasks(paths)
        actors = load_actors(paths)
    except Exception as exc:
        return [*diagnostics, Diagnostic("fail", "state-load", f"cannot load Wily state: {exc}", repo=repo_id)]
    task_ids = {task.id for task in tasks}
    actor_ids = {actor.id for actor in actors}
    for task in tasks:
        for dependency in task.depends_on:
            if dependency not in task_ids:
                diagnostics.append(Diagnostic("fail", "broken-depends-on", f"{task.id} has broken depends_on {dependency}", repo=repo_id))
        if task.status == TaskStatus.IN_PROGRESS and not paths.progress_jsonl(task.id).exists():
            fixed = False
            if fix:
                paths.progress_jsonl(task.id).parent.mkdir(parents=True, exist_ok=True)
                paths.progress_jsonl(task.id).touch()
                fixed = True
            diagnostics.append(Diagnostic("fail", "missing-progress", f"{task.id} missing progress.jsonl", fixed=fixed, repo=repo_id))
        if task.claim_sha and task.actor and task.actor not in actor_ids:
            diagnostics.append(Diagnostic("fail", "missing-actor", f"{task.id} references missing actor {task.actor}", repo=repo_id))
    if paths.tasks_dir.exists():
        for task_dir in sorted(path for path in paths.tasks_dir.iterdir() if path.is_dir()):
            if task_dir.name not in task_ids:
                diagnostics.append(Diagnostic("warn", "orphan-task-dir", f"orphan task dir {task_dir.relative_to(root)}", repo=repo_id))
    diagnostics.extend(_handoff_location_checks(root, repo_id=repo_id))
    diagnostics.append(_hook_check(root, repo_id=repo_id, allow_non_git=allow_non_git_hook))
    diagnostics.append(_venv_check(root, repo_id=repo_id))
    if not diagnostics:
        diagnostics.append(Diagnostic("ok", "state", "no issues found", repo=repo_id))
    return diagnostics


def _schema_checks(paths: WilyPaths, *, repo_id: str | None = None) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for path in (paths.tasks_yaml, paths.actors_yaml):
        if not path.exists():
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            diagnostics.append(Diagnostic("fail", "schema", f"cannot parse {path.name}: {exc}", repo=repo_id))
            continue
        schema = data.get("schema")
        if schema and schema != SCHEMA_VERSION:
            diagnostics.append(Diagnostic("fail", "schema", f"{path.name} schema {schema!r} is not {SCHEMA_VERSION!r}", repo=repo_id))
    return diagnostics


def _handoff_location_checks(root: Path, *, repo_id: str | None = None) -> list[Diagnostic]:
    legacy = root / "agent-handoffs"
    if not legacy.is_dir():
        return []
    return [
        Diagnostic(
            "warn",
            "legacy-handoff-location",
            f"legacy handoff directory remains at {legacy.relative_to(root)}; use .wily/handoffs/",
            repo=repo_id,
        )
    ]


def _hook_check(root: Path, *, repo_id: str | None = None, allow_non_git: bool = False) -> Diagnostic:
    if not (root / ".git").exists():
        if allow_non_git:
            return Diagnostic("ok", "pre-commit-hook", "pre-commit hook not applicable because repo is not git", repo=repo_id)
        return Diagnostic("warn", "pre-commit-hook", "pre-commit hook cannot be checked because repo is not git", repo=repo_id)
    hook = root / ".git" / "hooks" / "pre-commit"
    try:
        text = hook.read_text(encoding="utf-8")
    except OSError:
        return Diagnostic("warn", "pre-commit-hook", "pre-commit hook is not installed", repo=repo_id)
    if "drift-guard --from-hook" not in text:
        return Diagnostic("warn", "pre-commit-hook", "pre-commit hook does not run wily drift guard", repo=repo_id)
    return Diagnostic("ok", "pre-commit-hook", "pre-commit hook runs wily drift guard", repo=repo_id)


def _venv_check(root: Path, *, repo_id: str | None = None) -> Diagnostic:
    if (root / ".venv").exists() or (root / "venv").exists():
        return Diagnostic("ok", "venv", "virtual environment present", repo=repo_id)
    return Diagnostic("warn", "venv", "virtual environment not found", repo=repo_id)
