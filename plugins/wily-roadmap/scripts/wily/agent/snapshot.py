"""Snapshot helpers for registered Wily repositories."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
from typing import Any

from wily.config import load_actors, load_tasks, repo_mode
from wily.coordination import CoordinationConfig, CoordinationRepo, ProjectContext, resolve_project_context
from wily.models import Actor, Task
from wily.scope import normalize_scope_entries
from wily.progress import cp_summary, read_events
from wily.paths import WilyPaths, WilyRootNotFound
from wily.workspace import WorkspaceManifestError, discover_workspace_manifest, load_workspace

CLIENT_VERSION = "wily-agent/0.1.0"


def repo_snapshot(path: Path) -> dict[str, Any]:
    paths = WilyPaths(path)
    project_title, tasks = load_tasks(paths)
    return {
        "path": str(path),
        "project_title": project_title,
        "tasks": [task.to_dict() for task in tasks],
        "client_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def build_snapshot_payload(
    path: Path,
    *,
    repo: str = "",
    actor: str = "",
    machine_id: str = "",
    recovery_report: dict[str, Any] | None = None,
    sync_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = path.resolve()
    context = project_context_or_default(root)
    root = context.root
    paths = context.paths
    project_title, tasks = load_tasks(paths)
    actors = load_actors(paths)
    remote_url = git_remote_url(root)
    remote = normalize_remote(remote_url, repo=repo, root=root)
    repo_slug = remote["slug"] or repo or root.name
    project = project_id(remote["normalized_url"], slug=repo_slug)
    captured_at = utc_now()
    branch = git_branch(root)
    checkout_id = checkout_identity(root)
    checkout = {
        "checkout_id": checkout_id,
        "worktree_id": checkout_id,
        "branch": branch,
        "local_path": str(root),
    }
    active_task = current_task(tasks)
    task_progress = {
        task.id: {
            "done": (summary := cp_summary(paths, task.id)).done,
            "total": summary.total,
            "current_cp": summary.current_cp,
            "cp_names": summary.cp_names,
            "done_cp_names": summary.done_cp_names,
            "last_event_at": summary.last_event_at,
        }
        for task in tasks
    }
    cp_events = {
        task.id: [event.__dict__ for event in events]
        for task in tasks
        if (events := read_events(paths, task.id))
    }
    task_results = {
        task.id: paths.result_md(task.id).read_text(encoding="utf-8")
        for task in tasks
        if paths.result_md(task.id).exists()
    }
    machine = {"hostname": socket.gethostname(), "machine_id": machine_id}
    actor_payload = actor_identity(actor, actors)
    current_cp = task_progress.get(active_task.id, {}).get("current_cp") if active_task else None
    presence = {
        "project_id": project,
        "repo_slug": repo_slug,
        "actor": actor_payload,
        "machine": machine,
        "checkout_id": checkout_id,
        "worktree_id": checkout_id,
        "branch": branch,
        "local_path": str(root),
        "current_task_id": active_task.id if active_task else None,
        "current_cp": current_cp,
        "status": "active" if active_task else "idle",
        "captured_at": captured_at,
    }
    recovery = recovery_report or empty_recovery_report()
    health = sync_health or empty_sync_health()
    payload: dict[str, Any] = {
        "payload_version": "board_v3_snapshot_v1",
        "active_mode": context.active_mode,
        "repo": repo,
        "project_id": project,
        "remote_url": remote_url,
        "remote": remote,
        "repo_slug": repo_slug,
        "branch": branch,
        "checkout_id": checkout_id,
        "worktree_id": checkout_id,
        "checkout": checkout,
        "workspace": workspace_metadata(root),
        "machine": machine,
        "actor": actor_payload,
        "presence": presence,
        "title": project_title,
        "mode_hint": repo_mode(paths),
        "local_path": str(root),
        "tasks": [task.to_dict() for task in tasks],
        "actors": {item.id: item.to_dict() for item in actors},
        "task_progress": task_progress,
        "cp_events": cp_events,
        "task_results": task_results,
        "checkpoint_timeline": checkpoint_timeline(paths, tasks, task_results=task_results, recovery_report=recovery),
        "recovery": recovery,
        "sync_health": health,
        "observed_commits": observed_commits(root),
        "project_md": paths.project_md.read_text(encoding="utf-8") if paths.project_md.exists() else "",
        "client_version": CLIENT_VERSION,
        "captured_at": captured_at,
    }
    if context.coordination is not None:
        payload["coordination"] = coordination_snapshot(
            context,
            tasks=tasks,
            parent_project_id=project,
            parent_repo_slug=repo_slug,
        )
    payload["snapshot_sha"] = snapshot_sha(payload)
    return payload


def project_context_or_default(root: Path) -> ProjectContext:
    try:
        return resolve_project_context(root)
    except WilyRootNotFound:
        return ProjectContext(active_mode="single_repo", paths=WilyPaths(root))


def coordination_snapshot(
    context: ProjectContext,
    *,
    tasks: list[Task],
    parent_project_id: str,
    parent_repo_slug: str,
) -> dict[str, Any]:
    coordination = context.coordination
    if coordination is None:
        return {}
    return {
        "schema": "wily-coordination-snapshot-v1",
        "title": coordination.title,
        "manifest_path": str(coordination.manifest_path),
        "parent": coordination_parent_payload(coordination, project_id=parent_project_id, repo_slug=parent_repo_slug),
        "children": [coordination_child_payload(repo) for repo in coordination.repos],
        "display": {"default_owner": "parent", "child_default_visibility": "nested"},
        "visibility": {"kind": coordination.visibility.kind, "owner": coordination.visibility.owner},
        "task_roadmap": [
            coordination_task_payload(
                task,
                coordination=coordination,
                parent_repo_slug=parent_repo_slug,
            )
            for task in tasks
        ],
    }


def coordination_parent_payload(coordination: CoordinationConfig, *, project_id: str, repo_slug: str) -> dict[str, Any]:
    parent = coordination.parent
    return {
        "id": parent.id,
        "title": coordination_repo_title(parent, fallback=coordination.title),
        "path": str(parent.path),
        "project_id": project_id,
        "repo_slug": repo_slug,
        "display_role": "owner",
    }


def coordination_child_payload(repo: CoordinationRepo) -> dict[str, Any]:
    remote_url = git_remote_url(repo.path)
    remote = normalize_remote(remote_url, root=repo.path)
    return {
        "id": repo.id,
        "title": coordination_repo_title(repo),
        "path": str(repo.path),
        "repo_slug": remote["slug"] or repo.id,
        "remote": remote,
        "branch": git_branch(repo.path),
        "display": {
            "default_visibility": "nested",
            "owned_by_parent": True,
            "direct_route": "scoped_parent_view",
        },
    }


def coordination_task_payload(
    task: Task,
    *,
    coordination: CoordinationConfig,
    parent_repo_slug: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope_entries(task.scope, default_repo=coordination.parent.id, coordination=True)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "depends_on": list(task.depends_on),
        "actor": task.actor,
        "scope": [
            {
                "repo": entry.repo,
                "path": entry.path,
                "source": entry.source,
            }
            for entry in normalized_scope
        ],
        "target_repos": target_repo_summaries(
            normalized_scope,
            coordination=coordination,
            parent_repo_slug=parent_repo_slug,
        ),
        "claim_snapshot_summary": claim_snapshot_summary(task.claim_snapshot, coordination=coordination),
    }


def target_repo_summaries(
    normalized_scope: list[Any],
    *,
    coordination: CoordinationConfig,
    parent_repo_slug: str,
) -> list[dict[str, Any]]:
    repos = {repo.id: repo for repo in coordination.all_repos}
    summaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in normalized_scope:
        if entry.repo in seen or entry.repo not in repos:
            continue
        seen.add(entry.repo)
        summaries.append(target_repo_summary(repos[entry.repo], coordination=coordination, parent_repo_slug=parent_repo_slug))
    return summaries


def target_repo_summary(repo: CoordinationRepo, *, coordination: CoordinationConfig, parent_repo_slug: str) -> dict[str, Any]:
    if repo.id == coordination.parent.id:
        repo_slug = parent_repo_slug
    else:
        remote = normalize_remote(git_remote_url(repo.path), root=repo.path)
        repo_slug = remote["slug"] or repo.id
    return {
        "id": repo.id,
        "title": coordination_repo_title(repo, fallback=coordination.title if repo.id == coordination.parent.id else ""),
        "path": str(repo.path),
        "repo_slug": repo_slug,
    }


def claim_snapshot_summary(claim_snapshot: dict[str, Any] | None, *, coordination: CoordinationConfig) -> dict[str, Any]:
    if not isinstance(claim_snapshot, dict):
        return {}
    repos = claim_snapshot.get("repos") if isinstance(claim_snapshot.get("repos"), dict) else {}
    summary: dict[str, Any] = {}
    for repo in coordination.all_repos:
        repo_snapshot = repos.get(repo.id)
        if not isinstance(repo_snapshot, dict):
            continue
        changed_files = sorted(str(path) for path in repo_snapshot.get("changed_files") or [])
        summary[repo.id] = {
            "git_available": bool(repo_snapshot.get("git_available")),
            "branch": repo_snapshot.get("branch"),
            "sha": repo_snapshot.get("sha"),
            "dirty": bool(repo_snapshot.get("dirty")),
            "changed_file_count": len(changed_files),
            "changed_files_sample": changed_files[:5],
        }
    return summary


def coordination_repo_title(repo: CoordinationRepo, *, fallback: str = "") -> str:
    return repo.title or fallback or repo.path.name or repo.id


def snapshot_sha(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key not in {"snapshot_sha", "captured_at"}
    }
    body = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def project_id(normalized_url: str, *, slug: str = "") -> str:
    identity = slug or normalized_url
    return identity if slug else hashlib.sha1(identity.encode("utf-8")).hexdigest()


def checkout_identity(root: Path) -> str:
    worktree_path = git_worktree_path(root) or str(root.resolve())
    material = worktree_path.encode("utf-8")
    return f"checkout_{hashlib.sha1(material).hexdigest()[:16]}"


def git_worktree_path(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--show-toplevel"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else ""


def normalize_remote(raw_url: str, *, repo: str = "", root: Path | None = None) -> dict[str, str]:
    raw = raw_url.strip()
    host = ""
    owner = ""
    name = ""
    match = re.match(r"git@([^:]+):(.+)$", raw, flags=re.IGNORECASE)
    if match:
        host, path = match.group(1).lower(), match.group(2)
        owner, name = _owner_name(path)
    if not owner:
        match = re.match(r"(?:https?|ssh|git)://(?:git@)?([^/]+)/(.+)$", raw, flags=re.IGNORECASE)
        if match:
            host, path = match.group(1).lower(), match.group(2)
            owner, name = _owner_name(path)
    if not owner and repo and "/" in repo:
        owner, name = _owner_name(repo)
        host = "github.com"
    if not name and root is not None:
        name = root.name
    slug = f"{owner}/{name}" if owner and name else repo
    normalized = f"https://{host}/{owner}/{name}" if host and owner and name else raw
    return {
        "raw_url": raw,
        "normalized_url": normalized.removesuffix(".git"),
        "owner": owner,
        "name": name.removesuffix(".git"),
        "slug": slug.removesuffix(".git"),
    }


def _owner_name(path: str) -> tuple[str, str]:
    cleaned = path.strip("/").removesuffix(".git")
    parts = cleaned.split("/")
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return "", cleaned


def git_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    detached = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if detached.returncode == 0 and detached.stdout.strip():
        return f"detached-{detached.stdout.strip()}"
    return "unknown"


def workspace_metadata(root: Path) -> dict[str, Any]:
    try:
        manifest = discover_workspace_manifest(root)
        workspace = load_workspace(manifest)
    except WorkspaceManifestError:
        return {"manifest_path": "", "title": "", "repo": {}}
    repo_payload: dict[str, Any] = {}
    for repo in workspace.repos:
        if repo.path == root.resolve():
            repo_payload = repo.to_dict()
            break
    return {
        "manifest_path": str(workspace.manifest_path),
        "title": workspace.title,
        "repo": repo_payload,
    }


def actor_identity(actor_id: str, actors: list[Actor]) -> dict[str, Any]:
    actor = next((item for item in actors if item.id == actor_id), None)
    if actor is None:
        return {"id": actor_id, "display": actor_id}
    payload = {"id": actor.id, **actor.to_dict()}
    payload.setdefault("display", actor.id)
    return payload


def current_task(tasks: list[Task]) -> Task | None:
    return next((task for task in tasks if task.status.value == "in_progress"), None)


def checkpoint_timeline(
    paths: WilyPaths,
    tasks: list[Task],
    *,
    task_results: dict[str, str],
    recovery_report: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    return {
        task.id: _task_timeline(paths, task.id, result_summary=summarize_markdown(task_results.get(task.id, "")), recovery_report=recovery_report)
        for task in tasks
    }


def _task_timeline(
    paths: WilyPaths,
    task_id: str,
    *,
    result_summary: str,
    recovery_report: dict[str, Any],
) -> list[dict[str, Any]]:
    events = read_events(paths, task_id)
    order: list[str] = []
    grouped: dict[str, list[Any]] = {}
    for event in events:
        if event.cp not in grouped:
            grouped[event.cp] = []
            order.append(event.cp)
        grouped[event.cp].append(event)
    status_rows = _status_board_rows_by_cp(recovery_report, task_id)
    rows: list[dict[str, Any]] = []
    for cp in order:
        cp_events = grouped[cp]
        last = cp_events[-1]
        rows.append(
            {
                "id": cp,
                "name": cp,
                "status": _timeline_status(cp_events),
                "current_action": _current_action(cp_events),
                "last_update": last.ts,
                "verification": _verification_text(status_rows.get(cp, {})),
                "status_board": status_rows.get(cp, {}),
                "note": _latest_note(cp_events),
                "result_summary": result_summary,
            }
        )
    return rows


def _timeline_status(events: list[Any]) -> str:
    terminal = next((event for event in reversed(events) if event.event in {"done", "cancel"}), None)
    if terminal is not None:
        return "blocked" if terminal.event == "cancel" else "done"
    return "running"


def _current_action(events: list[Any]) -> str:
    active = next((event for event in reversed(events) if event.event == "start" and event.note), None)
    return str(active.note) if active and active.note else ""


def _latest_note(events: list[Any]) -> str:
    noted = next((event for event in reversed(events) if event.note), None)
    return str(noted.note) if noted and noted.note else ""


def _verification_text(row: dict[str, Any]) -> str:
    status = str(row.get("status") or "").lower()
    evidence = str(row.get("evidence") or "")
    if not status and not evidence:
        return ""
    return f"{status}: {evidence}".strip(": ")


def _status_board_rows_by_cp(recovery_report: dict[str, Any], task_id: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    task_report = (recovery_report.get("tasks") or {}).get(task_id) or {}
    for board in task_report.get("status_boards") or []:
        source_path = str(board.get("source_path") or "")
        for row in board.get("rows") or []:
            cp = str(row.get("checkpoint") or "")
            if not cp:
                continue
            rows[cp] = {
                "source_path": source_path,
                "status": row.get("status") or "",
                "evidence": row.get("evidence") or "",
                "imported_count": board.get("imported_count", 0),
                "skipped_duplicate_count": board.get("skipped_duplicate_count", 0),
            }
    return rows


def summarize_markdown(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped[:300]
    return ""


def empty_recovery_report() -> dict[str, Any]:
    return {
        "source_paths": [],
        "imported_count": 0,
        "skipped_duplicate_count": 0,
        "warnings": [],
        "tasks": {},
    }


def empty_sync_health() -> dict[str, Any]:
    return {
        "last_successful_push": "",
        "last_successful_snapshot": "",
        "last_successful_heartbeat": "",
        "last_failed_push": "",
        "last_failure_reason": "",
        "pending_snapshot_sha": "",
        "pending_snapshot_captured_at": "",
        "client_version": CLIENT_VERSION,
        "captured_at": "",
    }


def git_remote_url(root: Path) -> str:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return f"file://{root}"


def observed_commits(root: Path) -> list[dict[str, str | None]]:
    result = subprocess.run(
        [
            "git",
            "log",
            "--since=7 days ago",
            "--max-count=100",
            "--pretty=format:%H%x1f%an%x1f%aI%x1f%s",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    commits: list[dict[str, str | None]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        sha, author, committed_at, subject = parts
        commits.append(
            {
                "sha": sha,
                "author": author,
                "committed_at": committed_at,
                "subject": subject,
                "guessed_task_id": guess_task_id(subject),
            }
        )
    return commits


def guess_task_id(text: str) -> str | None:
    match = re.search(r"(?i)\bT\d+\b", text)
    return match.group(0).upper() if match else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def heartbeat_payload(*, repo: str, actor: str, task_id: str, note: str = "") -> dict[str, Any]:
    now = utc_now()
    return {
        "repo": repo,
        "item_type": "phase",
        "item_id": task_id,
        "phase_id": task_id,
        "actor": actor,
        "agent": "wily-agent",
        "event": "heartbeat",
        "live_status": "active",
        "session_id": f"wily-agent-{task_id}",
        "note": note,
        "client_time": now,
    }
