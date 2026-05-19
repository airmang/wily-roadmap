"""Foreground daemon loop for wily-agent."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .client import publish_event, publish_heartbeat, publish_snapshot
from .config import AgentConfig
from .registry import RegisteredRepo, load_registry
from .snapshot import build_snapshot_payload, heartbeat_payload, repo_snapshot

POLL_SECONDS = 1.0
SNAPSHOT_DEBOUNCE_SECONDS = 2.0
SNAPSHOT_FALLBACK_SECONDS = 60.0


def run_once(config: AgentConfig, registry_path: Path, *, offline_ok: bool = False) -> list[dict[str, Any]]:
    repos = load_registry(registry_path)
    if not config.configured and offline_ok:
        return [{"repo": str(repo.path), "sent": False, "reason": "not configured"} for repo in repos]
    results: list[dict[str, Any]] = []
    for repo in repos:
        results.append(publish_repo_heartbeat(config, repo, include_snapshot=True))
    return results


def run_loop(config: AgentConfig, registry_path: Path, *, once: bool = False, offline_ok: bool = False) -> list[dict[str, Any]]:
    results = run_once(config, registry_path, offline_ok=offline_ok)
    if once:
        return results
    last_mtime: dict[str, float] = {}
    changed_at: dict[str, float] = {}
    last_snapshot: dict[str, float] = {}
    last_heartbeat: dict[str, float] = {}
    while True:
        time.sleep(POLL_SECONDS)
        repos = load_registry(registry_path)
        results = []
        now = time.monotonic()
        for repo in repos:
            key = str(repo.path.resolve())
            mtime = wily_tree_mtime(repo.path)
            if last_mtime.get(key) != mtime:
                last_mtime[key] = mtime
                changed_at[key] = now
            heartbeat_due = now - last_heartbeat.get(key, 0.0) >= max(config.heartbeat_interval, 1)
            snapshot_due = key not in last_snapshot or now - last_snapshot[key] >= SNAPSHOT_FALLBACK_SECONDS
            if key in changed_at and now - changed_at[key] >= SNAPSHOT_DEBOUNCE_SECONDS:
                snapshot_due = True
                changed_at.pop(key, None)
            if not heartbeat_due and not snapshot_due:
                continue
            results.append(publish_repo_heartbeat(config, repo, include_snapshot=snapshot_due))
            if heartbeat_due:
                last_heartbeat[key] = now
            if snapshot_due:
                last_snapshot[key] = now


def publish_repo_heartbeat(config: AgentConfig, repo: RegisteredRepo, *, include_snapshot: bool = True) -> dict[str, Any]:
    try:
        snapshot = repo_snapshot(repo.path)
    except Exception as exc:  # best-effort daemon path
        return {"repo": str(repo.path), "sent": False, "reason": str(exc)}
    active = next((task for task in snapshot["tasks"] if task.get("status") == "in_progress"), None)
    task_id = str((active or snapshot["tasks"][0] if snapshot["tasks"] else {"id": "T00"}).get("id"))
    board_repo = repo.repo or config.repo
    payload = heartbeat_payload(
        repo=board_repo,
        actor=config.actor,
        task_id=task_id,
        note=f"{snapshot['project_title']} heartbeat",
    )
    snapshot_payload = build_snapshot_payload(repo.path, repo=board_repo, actor=config.actor)
    snapshot_result = publish_snapshot(config, snapshot_payload) if include_snapshot else {"sent": False, "reason": "not due"}
    heartbeat_result = (
        publish_heartbeat(config, project_id=str(snapshot_payload["project_id"]), current_task_id=task_id)
        if config.snapshot_configured
        else publish_event(config, payload)
    )
    return {
        "repo": str(repo.path),
        "task_id": task_id,
        "snapshot": snapshot_result,
        "heartbeat": heartbeat_result,
    }


def wily_tree_mtime(root: Path) -> float:
    wily_dir = root / ".wily"
    if not wily_dir.exists():
        return 0.0
    latest = wily_dir.stat().st_mtime
    for path in wily_dir.rglob("*"):
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest
