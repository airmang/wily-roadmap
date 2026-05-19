"""Snapshot helpers for registered Wily repositories."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from wily.config import load_actors, load_tasks, repo_mode
from wily.progress import cp_summary, read_events
from wily.paths import WilyPaths

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


def build_snapshot_payload(path: Path, *, repo: str = "", actor: str = "") -> dict[str, Any]:
    root = path.resolve()
    paths = WilyPaths(root)
    project_title, tasks = load_tasks(paths)
    actors = load_actors(paths)
    remote_url = git_remote_url(root)
    payload: dict[str, Any] = {
        "repo": repo,
        "project_id": project_id(remote_url),
        "remote_url": remote_url,
        "title": project_title,
        "mode_hint": repo_mode(paths),
        "local_path": str(root),
        "tasks": [task.to_dict() for task in tasks],
        "actors": {item.id: item.to_dict() for item in actors},
        "task_progress": {
            task.id: {
                "done": (summary := cp_summary(paths, task.id)).done,
                "total": summary.total,
                "current_cp": summary.current_cp,
                "cp_names": summary.cp_names,
            }
            for task in tasks
        },
        "cp_events": {
            task.id: [event.__dict__ for event in read_events(paths, task.id)]
            for task in tasks
            if read_events(paths, task.id)
        },
        "task_results": {
            task.id: paths.result_md(task.id).read_text(encoding="utf-8")
            for task in tasks
            if paths.result_md(task.id).exists()
        },
        "observed_commits": observed_commits(root),
        "project_md": paths.project_md.read_text(encoding="utf-8") if paths.project_md.exists() else "",
        "client_version": CLIENT_VERSION,
        "captured_at": utc_now(),
    }
    if actor:
        payload["actor"] = actor
    payload["snapshot_sha"] = snapshot_sha(payload)
    return payload


def snapshot_sha(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key not in {"snapshot_sha", "captured_at"}
    }
    body = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def project_id(remote_url: str) -> str:
    return hashlib.sha1(remote_url.encode("utf-8")).hexdigest()


def git_remote_url(root: Path) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
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
