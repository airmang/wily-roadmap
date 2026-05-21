"""`wily land <id>` - commit local task changes with a Wily trailer."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..config import load_tasks
from ..coordination import ProjectContext, nested_repo_exclusions, resolve_project_context
from ..models import TaskStatus
from ..observation import repo_snapshot
from ..paths import WilyRootNotFound
from ..scope import file_matches_scope, normalize_scope_entries
from . import _common

DESCRIPTION = "commit local task changes with a Wily trailer"
USAGE = "usage: wily land <task-id> [--dry-run] [--json] [--push|--no-push] [--force] [--include-ledger-closure] [--include-mixed] [--include <repo:path>]"
HELP = "\n".join(
    [
        "Options:",
        "  --dry-run                 report preflight without staging or committing",
        "  --json                    emit preflight as JSON",
        "  --push                    push after committing",
        "  --no-push                 skip push after committing",
        "  --force                   land before done; in legacy single-repo mode it can include out-of-scope files",
        "  --include-ledger-closure  include Wily ledger closure files outside task scope",
        "  --include-mixed           include files modified before and after claim",
        "  --include <repo:path>     explicitly include one mixed coordination file",
    ]
)


def main(args: list[str]) -> int:
    args, as_json = _common.consume_json_flag(args)
    if _common.missing_value_flag(args, {"--include"}):
        _common.emit_error("--include requires a repo-qualified path")
        return _common.EXIT_USAGE
    force = "--force" in args
    include_ledger_closure = "--include-ledger-closure" in args
    include_mixed = "--include-mixed" in args
    dry_run = "--dry-run" in args
    explicit_includes = _common.extract_values(args, "--include")
    push = "--push" in args
    no_push = "--no-push" in args
    if push and no_push:
        _common.emit_error("choose only one of --push or --no-push")
        return _common.EXIT_USAGE
    positional = _common.positionals(args, value_flags={"--include"})
    if len(positional) != 1:
        _common.emit_error(USAGE)
        return _common.EXIT_USAGE
    task_id = positional[0]
    try:
        context = resolve_project_context(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    if context.active_mode == "coordination":
        if push:
            _common.emit_error("--push is not supported in coordination mode")
            return _common.EXIT_USAGE
        return _coordination_main(
            context,
            task_id,
            force=force,
            dry_run=dry_run,
            as_json=as_json,
            include_mixed=include_mixed,
            explicit_includes=explicit_includes,
        )
    root = context.paths.root
    paths = context.paths
    _, tasks = load_tasks(paths)
    task = next((item for item in tasks if item.id == task_id), None)
    if task is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    if task.status != TaskStatus.DONE and not force:
        _common.emit_error(f"{task_id} is {task.status.value}; run wily done first")
        return _common.EXIT_TRANSITION
    changed = _changed(root)
    if not changed:
        _common.emit_error("nothing to commit")
        return _common.EXIT_FAILURE
    in_scope, out_scope = _split(changed, task.scope)
    ledger_out_scope = [file for file in out_scope if _is_ledger_closure_file(file)]
    ordinary_out_scope = [file for file in out_scope if file not in ledger_out_scope]
    if ledger_out_scope and not force and not include_ledger_closure:
        _common.emit_error("ledger closure changes detected outside task scope:")
        for file in ledger_out_scope:
            _common.emit_error(f"  {file}")
        _common.emit_error("rerun with --include-ledger-closure to commit Wily ledger metadata with this task")
        return _common.EXIT_TRANSITION
    files = changed if force or not out_scope else _dedupe(in_scope + ledger_out_scope)
    if out_scope and not force:
        if ordinary_out_scope:
            _common.emit_text(f"warning: {len(ordinary_out_scope)} file(s) outside scope; use --force to include")
        if ledger_out_scope and include_ledger_closure:
            _common.emit_text(f"including {len(ledger_out_scope)} Wily ledger closure file(s)")
    if not files:
        _common.emit_error("no in-scope files to commit")
        return _common.EXIT_FAILURE
    subprocess.run(["git", "add", *files], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", _message(paths, task.id, task.title, pre_done=task.status != TaskStatus.DONE)], cwd=root, check=True)
    _common.emit_text(f"committed: {task.id}: {task.title}")
    if no_push or not push:
        _common.emit_text("(push skipped: --no-push)")
        return _common.EXIT_OK
    return _common.EXIT_OK if _do_push(root) else _common.EXIT_FAILURE


def _coordination_main(
    context: ProjectContext,
    task_id: str,
    *,
    force: bool,
    dry_run: bool,
    as_json: bool,
    include_mixed: bool,
    explicit_includes: list[str],
) -> int:
    paths = context.paths
    _, tasks = load_tasks(paths)
    task = next((item for item in tasks if item.id == task_id), None)
    if task is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    if task.status != TaskStatus.DONE and not force:
        _common.emit_error(f"{task_id} is {task.status.value}; run wily done first")
        return _common.EXIT_TRANSITION
    preflight = coordination_preflight(
        context,
        task,
        include_mixed=include_mixed,
        explicit_includes=explicit_includes,
    )
    if as_json:
        _common.emit_json(preflight)
    else:
        _emit_preflight_text(preflight)
    if not preflight["ok"]:
        return _common.EXIT_TRANSITION
    if dry_run:
        return _common.EXIT_OK
    committed = _commit_coordination_repos(context, task, preflight)
    if not committed:
        _common.emit_error("nothing to commit")
        return _common.EXIT_FAILURE
    for repo_id in committed:
        _common.emit_text(f"committed {repo_id}: {task.id}: {task.title}")
    _common.emit_text("(push skipped: coordination mode is local-only)")
    return _common.EXIT_OK


def coordination_preflight(
    context: ProjectContext,
    task,
    *,
    include_mixed: bool = False,
    explicit_includes: list[str] | None = None,
) -> dict[str, Any]:
    explicit_includes = explicit_includes or []
    coordination = context.coordination
    if coordination is None:
        raise ValueError("coordination preflight requires coordination context")
    scope = normalize_scope_entries(task.scope, default_repo=coordination.parent.id, coordination=True)
    baseline_repos = {}
    if isinstance(task.claim_snapshot, dict) and isinstance(task.claim_snapshot.get("repos"), dict):
        baseline_repos = task.claim_snapshot["repos"]
    repos_payload: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    explicit_include_set = set(explicit_includes)
    matched_explicit_includes: set[str] = set()
    parent_ledger_changes = _parent_ledger_changes(context, task.id)
    parent_payload = _repo_preflight_payload(
        coordination.parent.id,
        coordination.parent.path,
        scope,
        baseline_repos,
        include_mixed=include_mixed,
        explicit_include_set=explicit_include_set,
        matched_explicit_includes=matched_explicit_includes,
        exclude_paths=nested_repo_exclusions(coordination, coordination.parent),
    )
    if not parent_payload["git_available"]:
        parent_payload["task_candidate_changes"] = _parent_non_git_task_artifacts(context, scope)
    parent_task_artifact_changes = [f"{coordination.parent.id}:{path}" for path in parent_payload["task_candidate_changes"]]
    parent_git_required = bool(parent_task_artifact_changes)
    if parent_task_artifact_changes and not parent_payload["git_available"]:
        errors.append(
            {
                "code": "parent_not_git",
                "message": "parent-scoped artifacts require parent Git in coordination land",
                "files": list(parent_task_artifact_changes),
            }
        )
    _append_repo_blockers(errors, coordination.parent.id, parent_payload)
    repos_payload[coordination.parent.id] = parent_payload
    for repo in coordination.repos:
        repo_payload = _repo_preflight_payload(
            repo.id,
            repo.path,
            scope,
            baseline_repos,
            include_mixed=include_mixed,
            explicit_include_set=explicit_include_set,
            matched_explicit_includes=matched_explicit_includes,
            exclude_paths=nested_repo_exclusions(coordination, repo),
        )
        _append_repo_blockers(errors, repo.id, repo_payload)
        repos_payload[repo.id] = repo_payload
    unmatched_includes = sorted(explicit_include_set - matched_explicit_includes)
    if unmatched_includes:
        errors.append(
            {
                "code": "invalid_include",
                "message": "--include must name an existing mixed file as <repo:path>",
                "files": unmatched_includes,
            }
        )
    payload: dict[str, Any] = {
        "active_mode": "coordination",
        "task_id": task.id,
        "ok": not errors,
        "parent_git_required": parent_git_required,
        "parent_ledger_changes": parent_ledger_changes,
        "parent_task_artifact_changes": parent_task_artifact_changes,
        "repos": repos_payload,
        "errors": errors,
    }
    return payload


def _emit_preflight_text(preflight: dict[str, Any]) -> None:
    status = "ok" if preflight.get("ok") else "blocked"
    _common.emit_text(f"coordination land preflight: {status}")
    for error in preflight.get("errors") or []:
        if isinstance(error, dict):
            _common.emit_error(f"{error.get('code')}: {', '.join(str(file) for file in (error.get('files') or []))}")


def _repo_preflight_payload(
    repo_id: str,
    repo_path: Path,
    scope,
    baseline_repos: dict[str, Any],
    *,
    include_mixed: bool,
    explicit_include_set: set[str],
    matched_explicit_includes: set[str],
    exclude_paths: list[str],
) -> dict[str, Any]:
    current = repo_snapshot(repo_path, exclude_paths=exclude_paths)
    baseline = baseline_repos.get(repo_id) if isinstance(baseline_repos, dict) else None
    baseline_fingerprints = {}
    if isinstance(baseline, dict) and isinstance(baseline.get("fingerprints"), dict):
        baseline_fingerprints = baseline["fingerprints"]
    repo_payload = {
        "path": str(repo_path),
        "git_available": current["git_available"],
        "task_candidate_changes": [],
        "pre_existing_dirty": [],
        "mixed_files": [],
        "included_mixed_files": [],
        "out_of_scope_changes": [],
    }
    current_fingerprints = current.get("fingerprints") if isinstance(current.get("fingerprints"), dict) else {}
    for path in current.get("changed_files") or []:
        if not isinstance(path, str) or _is_ledger_closure_file(path) or path.startswith(".wily/"):
            continue
        qualified = f"{repo_id}:{path}"
        in_scope = file_matches_scope(scope, repo_id=repo_id, path=path)
        if path in baseline_fingerprints:
            if baseline_fingerprints.get(path) == current_fingerprints.get(path):
                repo_payload["pre_existing_dirty"].append(path)
            elif include_mixed or qualified in explicit_include_set:
                if qualified in explicit_include_set:
                    matched_explicit_includes.add(qualified)
                repo_payload["included_mixed_files"].append(path)
                if in_scope:
                    repo_payload["task_candidate_changes"].append(path)
                else:
                    repo_payload["out_of_scope_changes"].append(path)
            else:
                repo_payload["mixed_files"].append(path)
            continue
        if in_scope:
            repo_payload["task_candidate_changes"].append(path)
        else:
            repo_payload["out_of_scope_changes"].append(path)
    return repo_payload


def _append_repo_blockers(errors: list[dict[str, Any]], repo_id: str, repo_payload: dict[str, Any]) -> None:
    if repo_payload["out_of_scope_changes"]:
        errors.append(
            {
                "code": "out_of_scope_changes",
                "repo": repo_id,
                "files": list(repo_payload["out_of_scope_changes"]),
            }
        )
    if repo_payload["mixed_files"]:
        errors.append(
            {
                "code": "mixed_files",
                "repo": repo_id,
                "files": list(repo_payload["mixed_files"]),
            }
        )


def _commit_coordination_repos(context: ProjectContext, task, preflight: dict[str, Any]) -> list[str]:
    coordination = context.coordination
    if coordination is None:
        return []
    repos_by_id = {repo.id: repo for repo in coordination.all_repos}
    committed: list[str] = []
    for repo_id, repo_payload in (preflight.get("repos") or {}).items():
        if not isinstance(repo_payload, dict):
            continue
        files = _dedupe([str(file) for file in repo_payload.get("task_candidate_changes") or []])
        if not files:
            continue
        repo = repos_by_id.get(str(repo_id))
        if repo is None:
            continue
        subprocess.run(["git", "add", "--", *files], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", _message(context.paths, task.id, task.title, pre_done=task.status != TaskStatus.DONE)],
            cwd=repo.path,
            check=True,
        )
        committed.append(str(repo_id))
    return committed


def _parent_ledger_changes(context: ProjectContext, task_id: str) -> list[str]:
    paths = context.paths
    candidates = [paths.tasks_yaml, paths.progress_jsonl(task_id), paths.result_md(task_id)]
    result: list[str] = []
    for candidate in candidates:
        if candidate.exists():
            result.append(candidate.relative_to(paths.root).as_posix())
    return result


def _parent_non_git_task_artifacts(context: ProjectContext, scope_entries) -> list[str]:
    coordination = context.coordination
    if coordination is None:
        return []
    files: list[str] = []
    for entry in scope_entries:
        if entry.repo != coordination.parent.id:
            continue
        for path in _existing_files_for_pattern(coordination.parent.path, entry.path):
            relative = path.relative_to(coordination.parent.path).as_posix()
            if _is_ledger_closure_file(relative) or relative.startswith(".wily/"):
                continue
            files.append(relative)
    return _dedupe(files)


def _existing_files_for_pattern(root: Path, pattern: str) -> list[Path]:
    if pattern.endswith("/**"):
        base = root / pattern[:-3].rstrip("/")
        if base.is_dir():
            return [item for item in base.rglob("*") if item.is_file()]
    if any(char in pattern for char in "*?["):
        return [path for path in root.glob(pattern) if path.is_file()]
    path = root / pattern
    if path.is_file():
        return [path]
    if path.is_dir():
        return [item for item in path.rglob("*") if item.is_file()]
    return []


def _changed(root: Path) -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain=v2"], cwd=root, capture_output=True, text=True, check=True).stdout
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip() or line.startswith("? "):
            if line.startswith("? "):
                files.extend(_expand_untracked(root, line[2:]))
            continue
        parts = line.split("\t")
        head = parts[0].split()
        if line.startswith("1 ") and len(head) >= 9:
            files.append(" ".join(head[8:]))
        elif line.startswith("2 ") and len(parts) >= 2:
            files.append(parts[0].split()[-1])
    return files


def _expand_untracked(root: Path, path: str) -> list[str]:
    full_path = root / path
    if not full_path.is_dir():
        return [path]
    return [item.relative_to(root).as_posix() for item in sorted(full_path.rglob("*")) if item.is_file()]


def _split(files: list[str], scope: list[str]) -> tuple[list[str], list[str]]:
    if not scope:
        return files, []
    inside = [file for file in files if any(fnmatch.fnmatch(file, pattern) for pattern in scope)]
    outside = [file for file in files if file not in inside]
    return inside, outside


def _is_ledger_closure_file(file: str) -> bool:
    if file == ".wily/tasks.yaml":
        return True
    if not file.startswith(".wily/tasks/"):
        return False
    return file.endswith("/result.md") or file.endswith("/progress.jsonl")


def _dedupe(files: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for file in files:
        if file in seen:
            continue
        result.append(file)
        seen.add(file)
    return result


def _message(paths: WilyPaths, task_id: str, title: str, *, pre_done: bool = False) -> str:
    body = ""
    result = paths.result_md(task_id)
    if result.exists():
        bullets = [line for line in result.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
        body = "\n".join(bullets[:6])
    pre_done_line = "Wily-Pre-Done: true\n" if pre_done else ""
    return f"{task_id}: {title}\n\n{body}\n\nWily-Task: {task_id}\n{pre_done_line}"


def _do_push(root: Path) -> bool:
    return subprocess.run(["git", "push"], cwd=root, check=False).returncode == 0
