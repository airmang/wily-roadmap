"""Recover missing checkpoint ledger events from Custom Workflow status boards."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wily.config import load_tasks
from wily.models import Task, TaskStatus
from wily.paths import WilyPaths, touch_wily
from wily.progress import CpEvent, append_event_once, read_events

IMPORT_STATUSES = {"DONE", "RUNNING", "VERIFYING", "PARTIAL", "BLOCKED"}


def empty_recovery_report() -> dict[str, Any]:
    return {
        "source_paths": [],
        "imported_count": 0,
        "would_import_count": 0,
        "skipped_duplicate_count": 0,
        "dry_run": False,
        "warnings": [],
        "tasks": {},
    }


def recover_status_boards(root: Path, *, actor: str = "", ts: str = "", write: bool = True) -> dict[str, Any]:
    root = root.resolve()
    paths = WilyPaths(root)
    _title, tasks = load_tasks(paths)
    event_ts = ts or utc_now()
    report = empty_recovery_report()
    report["dry_run"] = not write
    for task in tasks:
        task_report = _recover_task(
            root,
            paths,
            task,
            actor=actor or task.actor or task.assignee or "unknown",
            ts=event_ts,
            write=write,
        )
        if task_report["status_boards"] or task_report["warnings"]:
            report["tasks"][task.id] = task_report
            report["source_paths"].extend(board["source_path"] for board in task_report["status_boards"])
            report["imported_count"] += task_report["imported_count"]
            report["would_import_count"] += task_report["would_import_count"]
            report["skipped_duplicate_count"] += task_report["skipped_duplicate_count"]
            report["warnings"].extend(task_report["warnings"])
    if report["imported_count"]:
        touch_wily(paths)
    return report


def _recover_task(root: Path, paths: WilyPaths, task: Task, *, actor: str, ts: str, write: bool) -> dict[str, Any]:
    task_report: dict[str, Any] = {
        "status_boards": [],
        "imported_count": 0,
        "would_import_count": 0,
        "skipped_duplicate_count": 0,
        "warnings": [],
    }
    candidates = _status_board_candidates(root, paths, task.id)
    if not candidates:
        return task_report
    if len(candidates) > 1:
        task_report["warnings"].append(
            f"ambiguous status boards for {task.id}: {', '.join(str(path) for path in candidates)}"
        )
        return task_report
    source = candidates[0]
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        task_report["warnings"].append(f"cannot read status board for {task.id}: {exc}")
        return task_report
    rows = _status_rows(text)
    board_summary: dict[str, Any] = {
        "source_path": str(source),
        "rows": rows,
        "imported_count": 0,
        "would_import_count": 0,
        "skipped_duplicate_count": 0,
        "warnings": [],
    }
    existing = read_events(paths, task.id)
    for row in rows:
        status = str(row["status"])
        if status not in IMPORT_STATUSES:
            continue
        if _contradicts_task_status(task, status):
            warning = f"status board {source} row {row['checkpoint']!r}={status} contradicts task {task.id} status {task.status.value}"
            board_summary["warnings"].append(warning)
            task_report["warnings"].append(warning)
            continue
        cp = str(row["checkpoint"])
        proposed = _events_for_row(row, actor=actor, ts=ts)
        if _has_terminal_event(existing, cp):
            board_summary["skipped_duplicate_count"] += len(proposed)
            task_report["skipped_duplicate_count"] += len(proposed)
            continue
        for event in proposed:
            if not write:
                if _has_event(existing, event):
                    board_summary["skipped_duplicate_count"] += 1
                    task_report["skipped_duplicate_count"] += 1
                else:
                    existing.append(event)
                    board_summary["would_import_count"] += 1
                    task_report["would_import_count"] += 1
                continue
            if append_event_once(paths, task.id, event):
                existing.append(event)
                board_summary["imported_count"] += 1
                task_report["imported_count"] += 1
            else:
                board_summary["skipped_duplicate_count"] += 1
                task_report["skipped_duplicate_count"] += 1
    task_report["status_boards"].append(board_summary)
    return task_report


def _status_board_candidates(root: Path, paths: WilyPaths, task_id: str) -> list[Path]:
    exact = paths.handoff_status_md(task_id)
    if exact.is_file():
        return [exact.resolve()]
    handoffs = root / "agent-handoffs"
    if not handoffs.is_dir():
        return []
    direct = sorted(
        path.resolve()
        for path in handoffs.glob("*-status.md")
        if task_id.lower() in path.name.lower()
    )
    if direct:
        return direct
    referenced: list[Path] = []
    for status in sorted(handoffs.glob("*-status.md")):
        stem = status.name[: -len("-status.md")]
        companions = [
            handoffs / f"{stem}-execution-package.md",
            handoffs / f"{stem}-requirements.md",
        ]
        for companion in companions:
            if not companion.is_file():
                continue
            try:
                if task_id in companion.read_text(encoding="utf-8"):
                    referenced.append(status.resolve())
                    break
            except OSError:
                continue
    return referenced


def _status_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    mode: str | None = None
    for line in text.splitlines():
        cells = _markdown_cells(line)
        if len(cells) < 2:
            mode = None
            continue
        detected = _status_table_mode(cells)
        if detected:
            mode = detected
            continue
        if set(cells[0]) <= {"-"} or set(cells[1]) <= {"-"}:
            continue
        if mode == "custom-workflow" and len(cells) >= 3 and cells[1].upper() in IMPORT_STATUSES | {"TODO", "PENDING"}:
            checkpoint = cells[2]
            status = cells[1].upper()
            evidence = cells[4] if len(cells) > 4 else ""
        elif mode == "checkpoint":
            checkpoint = cells[0]
            status = cells[1].upper()
            evidence = cells[2] if len(cells) > 2 else ""
        else:
            continue
        if not checkpoint or not status:
            continue
        rows.append(
            {
                "checkpoint": checkpoint,
                "status": status,
                "evidence": evidence,
                "line": line,
            }
        )
    return rows


def _events_for_row(row: dict[str, str], *, actor: str, ts: str) -> list[CpEvent]:
    cp = row["checkpoint"]
    status = row["status"]
    evidence = row.get("evidence") or None
    if status == "DONE":
        return [
            CpEvent(ts=ts, actor=actor, cp=cp, event="start"),
            CpEvent(ts=ts, actor=actor, cp=cp, event="done", note=evidence),
        ]
    if status == "BLOCKED":
        return [
            CpEvent(ts=ts, actor=actor, cp=cp, event="start"),
            CpEvent(ts=ts, actor=actor, cp=cp, event="cancel", note=evidence),
        ]
    return [CpEvent(ts=ts, actor=actor, cp=cp, event="start", note=evidence)]


def _has_terminal_event(events: list[CpEvent], cp: str) -> bool:
    return any(event.cp == cp and event.event in {"done", "cancel"} for event in events)


def _has_event(events: list[CpEvent], event: CpEvent) -> bool:
    return any(existing.cp == event.cp and existing.event == event.event for existing in events)


def _contradicts_task_status(task: Task, status: str) -> bool:
    if task.status == TaskStatus.DONE and status != "DONE":
        return True
    if task.status == TaskStatus.BLOCKED and status == "DONE":
        return True
    if task.status == TaskStatus.READY and status in {"DONE", "RUNNING", "VERIFYING", "PARTIAL", "BLOCKED"}:
        return True
    return False


def _markdown_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]


def _status_table_mode(cells: list[str]) -> str | None:
    lowered = [cell.lower() for cell in cells]
    if len(lowered) >= 3 and lowered[0] == "id" and lowered[1] == "status" and lowered[2] == "checkpoint":
        return "custom-workflow"
    if len(lowered) >= 2 and lowered[0] in {"checkpoint", "cp"} and lowered[1] in {"status", "state"}:
        return "checkpoint"
    return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
