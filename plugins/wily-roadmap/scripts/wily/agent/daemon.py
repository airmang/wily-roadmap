"""Foreground daemon loop for wily-agent."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .client import publish_event, publish_heartbeat, publish_snapshot
from .config import AgentConfig, default_paths
from .recovery import recover_status_boards
from .registry import RegisteredRepo, load_registry
from .sync_health import load_sync_health, record_publish_result
from .snapshot import build_snapshot_payload, heartbeat_payload

POLL_SECONDS = 1.0
SNAPSHOT_DEBOUNCE_SECONDS = 2.0
SNAPSHOT_FALLBACK_SECONDS = 60.0


def run_once(
    config: AgentConfig,
    registry_path: Path,
    *,
    offline_ok: bool = False,
    sync_health_path: Path | None = None,
) -> list[dict[str, Any]]:
    repos = load_registry(registry_path)
    if not config.configured and offline_ok:
        return [{"repo": str(repo.path), "sent": False, "reason": "not configured"} for repo in repos]
    results: list[dict[str, Any]] = []
    health_path = sync_health_path or default_paths().sync_health_path
    multi_repo = len(repos) > 1
    for repo in repos:
        results.append(
            publish_repo_heartbeat(
                config,
                repo,
                include_snapshot=True,
                sync_health_path=repo_sync_health_path(health_path, repo, multi_repo=multi_repo),
            )
        )
    return results


def run_loop(
    config: AgentConfig,
    registry_path: Path,
    *,
    once: bool = False,
    offline_ok: bool = False,
    sync_health_path: Path | None = None,
) -> list[dict[str, Any]]:
    health_path = sync_health_path or default_paths().sync_health_path
    results = run_once(config, registry_path, offline_ok=offline_ok, sync_health_path=health_path)
    if once:
        return results
    last_mtime: dict[str, float] = {}
    changed_at: dict[str, float] = {}
    last_snapshot: dict[str, float] = {}
    last_heartbeat: dict[str, float] = {}
    initial_now = time.monotonic()
    for repo in load_registry(registry_path):
        key = str(repo.path.resolve())
        last_snapshot[key] = initial_now
        last_heartbeat[key] = initial_now
    while True:
        time.sleep(POLL_SECONDS)
        repos = load_registry(registry_path)
        multi_repo = len(repos) > 1
        results = []
        now = time.monotonic()
        for repo in repos:
            key = str(repo.path.resolve())
            mtime = wily_tree_mtime(repo.path)
            if last_mtime.get(key) != mtime:
                last_mtime[key] = mtime
                changed_at[key] = now
            change_snapshot_due = key in changed_at and now - changed_at[key] >= SNAPSHOT_DEBOUNCE_SECONDS
            heartbeat_due = now - last_heartbeat.get(key, 0.0) >= max(config.heartbeat_interval, 1)
            snapshot_due = key not in last_snapshot or now - last_snapshot[key] >= SNAPSHOT_FALLBACK_SECONDS
            if change_snapshot_due:
                snapshot_due = True
            if not heartbeat_due and not snapshot_due:
                continue
            result = publish_repo_heartbeat(
                config,
                repo,
                include_snapshot=snapshot_due,
                sync_health_path=repo_sync_health_path(health_path, repo, multi_repo=multi_repo),
            )
            results.append(result)
            if heartbeat_due:
                last_heartbeat[key] = now
            if snapshot_due and (result.get("snapshot") or {}).get("sent") is True:
                last_snapshot[key] = now
                if change_snapshot_due:
                    changed_at.pop(key, None)


def publish_repo_heartbeat(
    config: AgentConfig,
    repo: RegisteredRepo,
    *,
    include_snapshot: bool = True,
    sync_health_path: Path | None = None,
) -> dict[str, Any]:
    try:
        board_repo = repo.repo or config.repo
        health_path = sync_health_path or default_paths().sync_health_path
        recovery_report = recover_status_boards(repo.path, actor=config.actor, write=False)
        snapshot_payload = build_snapshot_payload(
            repo.path,
            repo=board_repo,
            actor=config.actor,
            machine_id=config.machine_id,
            recovery_report=recovery_report,
            sync_health=load_sync_health(health_path),
        )
    except Exception as exc:  # best-effort daemon path
        return {"repo": str(repo.path), "sent": False, "reason": str(exc)}
    task_id = str(snapshot_payload["presence"].get("current_task_id") or "T00")
    payload = heartbeat_payload(
        repo=board_repo,
        actor=config.actor,
        task_id=task_id,
        note=f"{snapshot_payload['title']} heartbeat",
    )
    health_path = sync_health_path or default_paths().sync_health_path
    should_publish_snapshot = include_snapshot and config.snapshot_configured
    snapshot_result = publish_snapshot(config, snapshot_payload) if should_publish_snapshot else {"sent": False, "reason": "not configured" if include_snapshot else "not due"}
    if should_publish_snapshot:
        health = record_publish_result(
            health_path,
            kind="snapshot",
            snapshot_sha=str(snapshot_payload.get("snapshot_sha") or ""),
            result=snapshot_result,
            client_version=str(snapshot_payload.get("client_version") or ""),
            captured_at=str(snapshot_payload.get("captured_at") or ""),
        )
    else:
        health = load_sync_health(health_path)
    heartbeat_result = (
        publish_heartbeat(config, payload=snapshot_payload["presence"])
        if config.snapshot_configured
        else publish_event(config, payload)
    )
    health = record_publish_result(
        health_path,
        kind="heartbeat",
        result=heartbeat_result,
        client_version=str(snapshot_payload.get("client_version") or ""),
        captured_at=str(snapshot_payload.get("captured_at") or ""),
    )
    return {
        "repo": str(repo.path),
        "task_id": task_id,
        "snapshot": snapshot_result,
        "heartbeat": heartbeat_result,
        "recovery": recovery_report,
        "sync_health": health,
    }


def repo_sync_health_path(base_path: Path, repo: RegisteredRepo, *, multi_repo: bool) -> Path:
    if not multi_repo:
        return base_path
    material = str(repo.path.resolve()).encode("utf-8")
    suffix = hashlib.sha1(material).hexdigest()[:12]
    return base_path.with_name(f"{base_path.stem}-{suffix}{base_path.suffix}")


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
