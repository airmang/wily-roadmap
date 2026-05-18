#!/usr/bin/env python3
"""Local Wily roadmap helper."""

from __future__ import annotations

import json
import hmac
import hashlib
import os
import re
import secrets
import select
import shlex
import shutil
import subprocess
import sys
import termios
import time
import tty
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import wily_state_summary
import wily_watch_ui


Phase = dict[str, Any]
Stage = dict[str, Any]
Issue = dict[str, Any]
WATCH_MOUSE_RE = re.compile(r"\x1b\[<(\d+);(\d+);(\d+)([Mm])")
WATCH_BODY_START_ROW = 4
WATCH_MOUSE_LEFT = 0
WATCH_MOUSE_MIDDLE = 1
WATCH_MOUSE_RIGHT = 2
WATCH_MOUSE_WHEEL_UP = 64
WATCH_MOUSE_WHEEL_DOWN = 65
WATCH_MOUSE_ENABLE = "\033[?1000h\033[?1006h"
WATCH_MOUSE_DISABLE = "\033[?1006l\033[?1000l"
DEFAULT_UPDATE_REPOSITORY = "https://github.com/airmang/wily-roadmap"
BOARD_LIVE_ENV = ("WILY_BOARD_URL", "WILY_BOARD_SECRET", "WILY_BOARD_REPO", "WILY_BOARD_ACTOR")
BOARD_LIVE_OPTIONAL_ENV = ("WILY_BOARD_AGENT", "WILY_BOARD_HEARTBEAT", "WILY_BOARD_HEARTBEAT_INTERVAL")


def state_dir(root: Path) -> Path:
    return root / ".wily"


def _board_config_file_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    aliases = {
        "url": "WILY_BOARD_URL",
        "secret": "WILY_BOARD_SECRET",
        "repo": "WILY_BOARD_REPO",
        "actor": "WILY_BOARD_ACTOR",
        "agent": "WILY_BOARD_AGENT",
        "heartbeat": "WILY_BOARD_HEARTBEAT",
        "heartbeat_interval": "WILY_BOARD_HEARTBEAT_INTERVAL",
    }
    values: dict[str, str] = {}
    for key, value in payload.items():
        env_key = key if str(key).startswith("WILY_BOARD_") else aliases.get(str(key))
        if env_key:
            values[env_key] = str(value).strip()
    if not all(values.values()):
        return values
    return values


def board_live_config_values(root: Path | None = None) -> dict[str, str]:
    values: dict[str, str] = {}
    user_config = Path(os.environ.get("WILY_BOARD_USER_CONFIG", str(Path.home() / ".wily" / "board.json")))
    values.update(_board_config_file_values(user_config))
    if root is not None:
        values.update(_board_config_file_values(root / ".wily" / "board.json"))
        values.update(_board_config_file_values(root / ".wily" / "local" / "board.json"))
    for name in (*BOARD_LIVE_ENV, *BOARD_LIVE_OPTIONAL_ENV):
        env_value = os.environ.get(name, "").strip()
        if env_value:
            values[name] = env_value
    return values


def board_live_config(root: Path | None = None) -> dict[str, str] | None:
    values = board_live_config_values(root)
    if not all(values.get(name, "") for name in BOARD_LIVE_ENV):
        return None
    values.setdefault("WILY_BOARD_AGENT", "codex")
    return values


def missing_board_live_config_keys(root: Path | None = None) -> list[str]:
    values = board_live_config_values(root)
    return [name for name in BOARD_LIVE_ENV if not values.get(name, "")]


def board_live_enabled(root: Path | None = None) -> bool:
    return board_live_config(root) is not None


def redacted_board_live_config(values: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in values.items():
        if key == "WILY_BOARD_SECRET" and value:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def codex_hook_installed(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return "live-worked" in json.dumps(payload)


def board_live_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


BoardLiveEventResult = tuple[bool, str]


def board_last_emit_path(root: Path) -> Path:
    return state_dir(root) / "local" / "board-last-emit.json"


def _record_board_emit_result(
    root: Path, event: str, ok: bool, reason: str = ""
) -> None:
    try:
        path = board_last_emit_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                payload = {}
        except (OSError, json.JSONDecodeError):
            payload = {}
        entry = {"at": utc_now_z(), "event": event}
        if ok:
            payload["last_success"] = entry
        else:
            payload["last_failure"] = {**entry, "reason": reason}
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except OSError:
        pass


def read_board_last_emit(root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            board_last_emit_path(root).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def emit_board_live_event(
    root: Path,
    phase: Phase,
    event: str,
    live_status: str,
    note: str = "",
) -> BoardLiveEventResult:
    config = board_live_config(root)
    if config is None:
        return False, "missing config"
    item_id = str(phase.get("item_id") or phase.get("phase_id") or phase.get("id", ""))
    item_type = str(phase.get("item_type") or ("stage" if item_id.startswith("s") else "phase"))
    phase_id = str(phase.get("phase_id") or (item_id if item_type == "phase" else ""))
    payload = {
        "repo": config["WILY_BOARD_REPO"],
        "item_type": item_type,
        "item_id": item_id,
        "phase_id": phase_id,
        "stage_id": str(phase.get("stage_id", "") or (item_id if item_type == "stage" else "")),
        "actor": config["WILY_BOARD_ACTOR"],
        "agent": str(phase.get("agent") or config.get("WILY_BOARD_AGENT") or "codex"),
        "event": event,
        "live_status": live_status,
        "session_id": str(phase.get("session_id", "")),
        "session_path": str(phase.get("current_session", "")),
        "note": note,
        "client_time": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    for key in (
        "current_item_id",
        "draft_kind",
        "phases",
        "worked",
        "checkpoint",
        "title",
        "status",
        "owner",
        "depends_on",
        "execution_mode",
        "raw_path",
        "position",
    ):
        if key in phase:
            payload[key] = phase[key]
    if not payload["phase_id"]:
        payload.pop("phase_id")
    if not payload["session_id"]:
        payload.pop("session_id")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        config["WILY_BOARD_URL"].rstrip("/") + "/api/live/events",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Wily-Signature": board_live_signature(config["WILY_BOARD_SECRET"], body),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=2):
            _record_board_emit_result(root, event, True)
            return True, ""
    except urllib.error.HTTPError as exc:
        reason = f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = f"network error: {exc.reason}"
    except OSError as exc:
        reason = f"network error: {exc}"
    _record_board_emit_result(root, event, False, reason)
    return False, reason


def _surface_emit_failure(event: str, result: BoardLiveEventResult | None) -> None:
    if not isinstance(result, tuple):
        return
    ok, err = result
    if ok:
        return
    if err == "missing config":
        print(
            f"Board bridge: not configured for {event} (run 'wily board check')",
            file=sys.stderr,
        )
    else:
        print(
            f"Board bridge: {event} failed: {err} (run 'wily board check')",
            file=sys.stderr,
        )


def fetch_board_live_claims(phase: Phase) -> list[dict[str, Any]]:
    config = board_live_config()
    if config is None:
        return []
    phase_id = str(phase.get("phase_id") or phase.get("id", ""))
    stage_id = str(phase.get("stage_id") or "")
    if "/" in phase_id:
        inferred_stage_id, inferred_phase_id = phase_id.split("/", 1)
        stage_id = stage_id or inferred_stage_id
        phase_id = inferred_phase_id
    query = {
        "repo": config["WILY_BOARD_REPO"],
        "phase_id": phase_id,
        "actor": config["WILY_BOARD_ACTOR"],
    }
    if stage_id:
        query["stage_id"] = stage_id
    query_string = urllib.parse.urlencode(query)
    request = urllib.request.Request(
        config["WILY_BOARD_URL"].rstrip("/") + f"/api/live/claims?{query_string}",
        method="GET",
        headers={"X-Wily-Signature": board_live_signature(config["WILY_BOARD_SECRET"], b"")},
    )
    try:
        with urllib.request.urlopen(request, timeout=0.25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, urllib.error.URLError, urllib.error.HTTPError):
        return []
    claims = payload.get("claims") if isinstance(payload, dict) else None
    return claims if isinstance(claims, list) else []


def warn_board_live_claims(phase: Phase) -> None:
    claims = fetch_board_live_claims(phase)
    if not claims:
        return
    labels = []
    for claim in claims[:3]:
        actor = str(claim.get("actor") or "someone")
        last_seen = str(claim.get("last_seen_label") or "recently")
        labels.append(f"{actor} ({last_seen})")
    print(
        "Board claim warning: another active local session is already on this phase: "
        + ", ".join(labels),
        file=sys.stderr,
    )


def utc_now_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def live_root(root: Path) -> Path:
    return state_dir(root) / "local" / "live"


def live_active_dir(root: Path) -> Path:
    return live_root(root) / "active"


def live_alive_path(root: Path, session_id: str) -> Path:
    return live_root(root) / f"{session_id}.alive"


def live_pid_path(root: Path, session_id: str) -> Path:
    return live_root(root) / f"{session_id}.pid"


def new_live_session_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{stamp}-{os.getpid()}-{secrets.token_hex(4)}"


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def live_actor(root: Path | None = None) -> str:
    config = board_live_config(root)
    if config is not None:
        return config["WILY_BOARD_ACTOR"]
    return os.environ.get("USER") or os.environ.get("USERNAME") or "local"


def live_agent(root: Path | None = None) -> str:
    config = board_live_config(root)
    if config is not None:
        return config.get("WILY_BOARD_AGENT", "codex")
    return os.environ.get("WILY_BOARD_AGENT") or os.environ.get("WILY_AGENT") or "codex"


def live_item_type(item: Phase) -> str:
    item_id = str(item.get("item_id") or item.get("phase_id") or item.get("id", ""))
    explicit = item.get("item_type")
    if explicit:
        return str(explicit)
    return "stage" if item_id.startswith("s") and not item.get("phase_id") else "phase"


def live_item_id(item: Phase) -> str:
    return str(item.get("item_id") or item.get("phase_id") or item.get("id", ""))


def live_registry_payload(
    root: Path,
    item: Phase,
    *,
    event: str,
    live_status: str,
    note: str = "",
    session_id: str | None = None,
    parent_shell_pid: int | None = None,
) -> dict[str, Any]:
    item_id = live_item_id(item)
    item_type = live_item_type(item)
    phase_id = str(item.get("phase_id") or (item_id if item_type == "phase" else ""))
    stage_id = str(item.get("stage_id") or (item_id if item_type == "stage" else ""))
    now = utc_now_z()
    payload: dict[str, Any] = {
        "session_id": session_id or new_live_session_id(),
        "item_type": item_type,
        "item_id": item_id,
        "phase_id": phase_id,
        "stage_id": stage_id,
        "actor": live_actor(root),
        "agent": str(item.get("agent") or live_agent(root)),
        "event": event,
        "live_status": live_status,
        "session_path": str(item.get("current_session", "")),
        "note": note,
        "started_at": now,
        "last_seen_at": now,
    }
    if event == "worked":
        payload["last_worked_at"] = now
    if "checkpoint" in item:
        payload["checkpoint"] = item["checkpoint"]
    if parent_shell_pid:
        payload["parent_shell_pid"] = parent_shell_pid
    if not phase_id:
        payload.pop("phase_id")
    if not stage_id:
        payload.pop("stage_id")
    return payload


def live_draft_stage_decomposition_payload(
    root: Path,
    stage: Stage,
    phases: list[Phase],
    *,
    position: int | None = None,
) -> Phase:
    stage_id = str(stage.get("id", ""))
    normalized_phases: list[dict[str, Any]] = []
    for phase in phases:
        normalized_phases.append(
            {
                "id": str(phase.get("id", "")),
                "title": str(phase.get("title", "")),
                "status": str(phase.get("status", "pending")),
                "depends_on": [str(value) for value in phase.get("depends_on") or []],
                "owner": str(phase.get("owner") or stage.get("owner") or ""),
                "task": str(phase.get("task") or ""),
                "path": str(phase.get("path") or ""),
            }
        )
    payload: Phase = {
        "id": stage_id,
        "item_type": "stage",
        "item_id": stage_id,
        "stage_id": stage_id,
        "title": str(stage.get("title") or stage_id),
        "status": str(stage.get("status") or "pending"),
        "owner": str(stage.get("owner") or ""),
        "depends_on": [str(value) for value in stage.get("depends_on") or []],
        "execution_mode": str(stage.get("execution_mode") or "decomposed"),
        "raw_path": str(stage.get("path") or ""),
        "draft_kind": "stage_decomposition",
        "session_id": new_live_session_id(),
        "agent": live_agent(root),
        "phases": normalized_phases,
    }
    if position is not None:
        payload["position"] = position
    return payload


def _clean_markdown_cell(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def _parse_status_field(lines: list[str], label: str) -> str:
    prefix = f"{label}:"
    for line in lines:
        if line.strip().lower().startswith(prefix.lower()):
            return _clean_markdown_cell(line.split(":", 1)[1])
    return ""


def _parse_progress(value: str) -> dict[str, int]:
    match = re.search(r"(\d+)\s*/\s*(\d+)(?:\s*\((\d+)%\))?", value)
    if not match:
        return {"done": 0, "total": 0, "percent": 0}
    done = int(match.group(1))
    total = int(match.group(2))
    percent = int(match.group(3)) if match.group(3) else int((done / total) * 100) if total else 0
    return {"done": done, "total": total, "percent": percent}


def _parse_checkpoint_ref(value: str) -> dict[str, str]:
    value = _clean_markdown_cell(value)
    if not value or value.lower() in {"none", "n/a", "-"}:
        return {}
    if " - " in value:
        checkpoint_id, title = value.split(" - ", 1)
    else:
        parts = value.split(maxsplit=1)
        checkpoint_id = parts[0]
        title = parts[1] if len(parts) > 1 else ""
    return {"id": checkpoint_id.strip(), "title": title.strip()}


def _markdown_table_rows(lines: list[str], required_headers: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("|") or not line.endswith("|"):
            index += 1
            continue
        headers = [_clean_markdown_cell(cell) for cell in line.strip("|").split("|")]
        normalized = {header.lower() for header in headers}
        if not required_headers.issubset(normalized):
            index += 1
            continue
        index += 1
        if index < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[index]):
            index += 1
        while index < len(lines):
            row_line = lines[index].strip()
            if not row_line.startswith("|") or not row_line.endswith("|"):
                break
            cells = [_clean_markdown_cell(cell) for cell in row_line.strip("|").split("|")]
            if len(cells) >= len(headers):
                rows.append({headers[pos].lower(): cells[pos] for pos in range(len(headers))})
            index += 1
        break
    return rows


def _parse_markdown_bullets_under_heading(lines: list[str], heading: str) -> list[str]:
    bullets: list[str] = []
    in_section = False
    target = heading.strip().lower()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped[3:].strip().lower() == target
            continue
        if in_section and stripped.startswith("- "):
            bullets.append(_clean_markdown_cell(stripped[2:]))
    return bullets


def _checkpoint_from_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "id": row.get("id", ""),
        "title": row.get("checkpoint", ""),
        "status": row.get("status", "").lower(),
        "owner": row.get("owner", ""),
        "evidence": row.get("evidence", ""),
    }


def parse_checkpoint_status_board(path: Path, root: Path | None = None) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    checkpoint_rows = [_checkpoint_from_row(row) for row in _markdown_table_rows(lines, {"id", "status", "checkpoint"})]
    verification_rows = _markdown_table_rows(lines, {"status", "evidence"})
    current = _parse_checkpoint_ref(_parse_status_field(lines, "Current checkpoint"))
    next_checkpoint = _parse_checkpoint_ref(_parse_status_field(lines, "Next checkpoint"))

    def row_for(checkpoint: dict[str, str]) -> dict[str, str]:
        checkpoint_id = checkpoint.get("id")
        if not checkpoint_id:
            return {}
        for row in checkpoint_rows:
            if row.get("id") == checkpoint_id:
                return row
        return {}

    current_row = row_for(current)
    if current_row:
        current = {**current, **{key: value for key, value in current_row.items() if value}}
    if not current:
        for row in checkpoint_rows:
            if row.get("status") in {"running", "in_progress", "verifying", "verify", "partial", "blocked"}:
                current = row
                break
    next_row = row_for(next_checkpoint)
    if next_row:
        next_checkpoint = {**next_checkpoint, **{key: value for key, value in next_row.items() if value}}
    if not next_checkpoint:
        for row in checkpoint_rows:
            if row.get("status") in {"todo", "pending", "ready"}:
                next_checkpoint = row
                break

    blocker = _parse_status_field(lines, "Current blocker")
    if blocker.lower() in {"none", "n/a", "-"}:
        blocker = ""
    status_board = path
    if root is not None:
        try:
            status_board = path.relative_to(root)
        except ValueError:
            pass
    verification = verification_rows[-1] if verification_rows else {}
    return {
        "source": "custom-workflow",
        "is_durable": False,
        "status_board": status_board.as_posix() if isinstance(status_board, Path) else str(status_board),
        "state": _parse_status_field(lines, "State").lower(),
        "progress": _parse_progress(_parse_status_field(lines, "Progress")),
        "current": current,
        "next": next_checkpoint,
        "current_action": _parse_status_field(lines, "Current action"),
        "blocker": blocker,
        "verification": verification,
        "recent_events": _parse_markdown_bullets_under_heading(lines, "Recent Events"),
        "rows": checkpoint_rows,
    }


def _checkpoint_live_status(checkpoint: dict[str, Any]) -> str:
    current = checkpoint.get("current") if isinstance(checkpoint.get("current"), dict) else {}
    state = str(checkpoint.get("state") or "").lower()
    blocker = str(checkpoint.get("blocker") or "")
    status = str(current.get("status") or "").lower()
    progress = checkpoint.get("progress") if isinstance(checkpoint.get("progress"), dict) else {}
    if blocker or status == "blocked" or state == "blocked":
        return "blocked_local"
    if state in {"done", "complete", "completed"} or (
        progress.get("total") and progress.get("done") == progress.get("total")
    ):
        return "completed_local"
    return "active"


def _status_board_candidates(root: Path, item: Phase) -> list[Path]:
    candidates: list[Path] = []
    current = item.get("current_session")
    if current:
        session = root / ".wily" / str(current)
        candidates.extend([
            session / "runner" / "status-board.md",
            session / "status-board.md",
        ])
    phase_id = str(item.get("id") or item.get("phase_id") or "")
    handoffs = root / "agent-handoffs"
    if handoffs.exists() and phase_id:
        candidates.extend(sorted(handoffs.glob(f"*{phase_id}*status*.md")))
    if handoffs.exists():
        candidates.extend(sorted(handoffs.glob("*-status.md"), key=lambda path: path.stat().st_mtime, reverse=True))
    return [path for path in candidates if path.exists()]


def checkpoint_sync_usage() -> str:
    return "Usage: wily.py checkpoint-sync <stage-id>/<phase-id> [--status-board path]"


def command_checkpoint_sync(root: Path, args: list[str]) -> int:
    phase_id = require_phase_id(args, "checkpoint-sync")
    if not phase_id:
        return 2
    status_board: Path | None = None
    index = 1
    while index < len(args):
        arg = args[index]
        if arg == "--status-board":
            try:
                status_board = Path(args[index + 1])
            except IndexError:
                print("Missing value for --status-board", file=sys.stderr)
                return 2
            index += 2
            continue
        print(f"Unknown option: {arg}", file=sys.stderr)
        print(checkpoint_sync_usage(), file=sys.stderr)
        return 2

    roadmap = load_roadmap(root)
    item: Phase | None = find_phase(roadmap, phase_id)
    if item is None:
        found = find_stage_phase(root, roadmap, phase_id)
        if found:
            stage, phase, _stage_state = found
            item = {**phase, "stage_id": stage.get("id", "")}
    if item is None:
        stage = find_stage(roadmap, phase_id)
        if stage:
            item = stage
    if item is None:
        print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
        return 1

    if status_board is None:
        candidates = _status_board_candidates(root, item)
        if not candidates:
            print("No checkpoint status board found. Pass --status-board <path>.", file=sys.stderr)
            return 1
        status_board = candidates[0]
    if not status_board.is_absolute():
        status_board = root / status_board
    if not status_board.exists():
        print(f"Checkpoint status board not found: {status_board}", file=sys.stderr)
        return 1

    checkpoint = parse_checkpoint_status_board(status_board, root)
    live_status = _checkpoint_live_status(checkpoint)
    note = str(checkpoint.get("current_action") or checkpoint.get("blocker") or "")
    existing = live_registries_for_item(root, item)
    session_id = str(existing[0].get("session_id")) if existing else None
    payload = write_live_registry(
        root,
        {**item, "checkpoint": checkpoint},
        event="checkpoint_updated",
        live_status=live_status,
        note=note,
        session_id=session_id,
    )
    event_payload = {**item, **payload, "id": item.get("id", phase_id), "checkpoint": checkpoint}
    result = emit_board_live_event(root, event_payload, "checkpoint_updated", live_status, note)
    sent, detail = result if isinstance(result, tuple) else (bool(result), "")
    current = checkpoint.get("current") if isinstance(checkpoint.get("current"), dict) else {}
    print(f"Checkpoint overlay synced for {phase_id}: {current.get('id', 'unknown')} ({live_status})")
    if not sent:
        suffix = f": {detail}" if detail else ""
        print(f"Board checkpoint event not sent{suffix}", file=sys.stderr)
    return 0


def read_live_registry(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def active_live_registry_files(root: Path) -> list[Path]:
    directory = live_active_dir(root)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def write_live_registry(
    root: Path,
    item: Phase,
    *,
    event: str,
    live_status: str,
    note: str = "",
    session_id: str | None = None,
    parent_shell_pid: int | None = None,
) -> dict[str, Any]:
    directory = live_active_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    live_root(root).mkdir(parents=True, exist_ok=True)
    payload = live_registry_payload(
        root,
        item,
        event=event,
        live_status=live_status,
        note=note,
        session_id=session_id,
        parent_shell_pid=parent_shell_pid,
    )
    path = directory / f"{payload['session_id']}.json"
    existing = read_live_registry(path) if path.exists() else None
    if existing:
        payload["started_at"] = existing.get("started_at") or payload["started_at"]
        if existing.get("last_worked_at") and event != "worked":
            payload["last_worked_at"] = existing["last_worked_at"]
        if "checkpoint" not in payload and existing.get("checkpoint") is not None:
            payload["checkpoint"] = existing["checkpoint"]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    live_alive_path(root, str(payload["session_id"])).touch()
    return payload


def live_registry_matches(payload: dict[str, Any], item: Phase) -> bool:
    if item.get("session_id") and str(payload.get("session_id", "")) == str(item.get("session_id")):
        return True
    item_id = live_item_id(item)
    session_path = str(item.get("current_session", ""))
    if session_path and str(payload.get("session_path", "")) == session_path:
        return True
    if str(payload.get("item_id", "")) == item_id:
        return True
    if item_id and str(payload.get("phase_id", "")) == item_id:
        return True
    return False


def live_registries_for_item(root: Path, item: Phase) -> list[dict[str, Any]]:
    registries = []
    for path in active_live_registry_files(root):
        payload = read_live_registry(path)
        if payload and live_registry_matches(payload, item):
            registries.append(payload)
    return registries


def remove_live_registry(root: Path, session_id: str) -> None:
    for path in (
        live_active_dir(root) / f"{session_id}.json",
        live_alive_path(root, session_id),
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def recover_orphan_live_sessions(root: Path) -> None:
    for path in active_live_registry_files(root):
        payload = read_live_registry(path)
        if not payload:
            path.unlink(missing_ok=True)
            continue
        session_id = str(payload.get("session_id") or path.stem)
        alive = live_alive_path(root, session_id)
        pid_path = live_pid_path(root, session_id)
        if not alive.exists():
            path.unlink(missing_ok=True)
            continue
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = 0
            if pid and not process_alive(pid):
                remove_live_registry(root, session_id)
                pid_path.unlink(missing_ok=True)


def heartbeat_enabled(root: Path) -> bool:
    config = board_live_config(root) or {}
    value = os.environ.get("WILY_BOARD_HEARTBEAT") or config.get("WILY_BOARD_HEARTBEAT", "")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def heartbeat_interval(root: Path) -> str:
    config = board_live_config(root) or {}
    return os.environ.get("WILY_BOARD_HEARTBEAT_INTERVAL") or config.get("WILY_BOARD_HEARTBEAT_INTERVAL") or "30"


def spawn_heartbeat_sidecar(root: Path, item: Phase, session_id: str) -> None:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "live-heartbeat",
        live_item_id(item),
        "--session",
        session_id,
        "--interval",
        heartbeat_interval(root),
        "--parent-shell-pid",
        str(os.getppid()),
    ]
    subprocess.Popen(
        command,
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def open_live_session(root: Path, item: Phase) -> dict[str, Any]:
    recover_orphan_live_sessions(root)
    return write_live_registry(root, item, event="start", live_status="claimed")


def close_live_sessions(
    root: Path,
    item: Phase,
    *,
    event: str,
    live_status: str,
    note: str = "",
) -> list[dict[str, Any]]:
    registries = live_registries_for_item(root, item)
    if not registries:
        registries = [live_registry_payload(root, item, event=event, live_status=live_status, note=note)]
    closed = []
    for payload in registries:
        payload = {**payload, "id": live_item_id(item), "event": event, "live_status": live_status}
        if note:
            payload["note"] = note
        _surface_emit_failure(event, emit_board_live_event(root, payload, event, live_status, note))
        session_id = str(payload.get("session_id", ""))
        if session_id:
            remove_live_registry(root, session_id)
        closed.append(payload)
    return closed


def resolve_active_live_payload(
    root: Path,
    *,
    item_id: str = "",
    session_id: str = "",
    agent: str = "",
) -> dict[str, Any] | None:
    candidates: list[tuple[float, dict[str, Any]]] = []
    for path in active_live_registry_files(root):
        payload = read_live_registry(path)
        if not payload:
            continue
        if session_id and str(payload.get("session_id", "")) != session_id:
            continue
        if agent and not session_id and str(payload.get("agent", "")) != agent:
            continue
        if item_id and item_id not in {
            str(payload.get("item_id", "")),
            str(payload.get("phase_id", "")),
            str(payload.get("stage_id", "")),
        }:
            continue
        candidates.append((path.stat().st_mtime, payload))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0], reverse=True)[0][1]


def write_once(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def write_baseline_roadmap(path: Path, goal: str | None) -> bool:
    goal_value = goal or "사용자 목표 필요"
    return write_once(
        path,
        "\n".join(
            [
                "roadmap_version: 1",
                f"goal: {quote(goal_value)}",
                "stages: []",
                "",
            ]
        ),
    )


def mature_repo_hints(root: Path) -> list[str]:
    candidates = [
        ("README.md", root / "README.md"),
        ("pyproject.toml", root / "pyproject.toml"),
        ("package.json", root / "package.json"),
        ("Cargo.toml", root / "Cargo.toml"),
        ("go.mod", root / "go.mod"),
        ("src/", root / "src"),
        ("scripts/", root / "scripts"),
        ("tests/", root / "tests"),
        ("docs/", root / "docs"),
    ]
    return [label for label, path in candidates if path.exists()]


def command_init(root: Path, args: list[str]) -> int:
    goal = " ".join(args).strip() or None
    state = state_dir(root)
    hints = mature_repo_hints(root)
    for name in ("phases", "stages", "sessions", "revisions"):
        (state / name).mkdir(parents=True, exist_ok=True)

    preserved_files: list[str] = []
    if not write_once(
        state / "project.md",
        "\n".join(
            [
                "# Wily Project",
                "",
                f"루트: {root}",
                f"목표: {goal or '사용자 목표 필요'}",
                "",
                "현재 기준:",
                f"- 기존 프로젝트 단서: {', '.join(hints) if hints else '없음'}",
                "- phase 생성 전에 저장소 스캔이 필요합니다.",
                "",
            ]
        ),
    ):
        preserved_files.append("project.md")
    if not write_baseline_roadmap(state / "roadmap.yaml", goal):
        preserved_files.append("roadmap.yaml")
    if not write_once(
        state / "status.md",
        "\n".join(
            [
                "# Wily Status",
                "",
                "상태가 초기화되었습니다.",
                "다음 작업: 저장소를 스캔하고 로드맵 phase를 생성합니다.",
                "",
            ]
        ),
    ):
        preserved_files.append("status.md")
    if not write_once(
        state / "decisions.md",
        "\n".join(
            [
                "# Wily Decisions",
                "",
                "아직 기록된 결정이 없습니다.",
                "",
            ]
        ),
    ):
        preserved_files.append("decisions.md")

    print(f"Initialized .wily at {state}")
    if goal:
        print(f"Goal: {goal}")
    else:
        print("Goal: needed")
        print("Next action: scan the repository, summarize current state, and ask for the intended final outcome.")
    if hints:
        print(f"Existing project hints: {', '.join(hints)}")
    if preserved_files:
        print(f"Preserved existing .wily files: {', '.join(sorted(preserved_files))}")
    return 0


def command_status(root: Path) -> int:
    print(wily_watch_ui.render_watch(root, interval=2.0, rich=False))
    return 0


def load_roadmap(root: Path) -> dict[str, Any]:
    path = state_dir(root) / "roadmap.yaml"
    if not path.exists():
        return {"roadmap_version": "unknown", "phases": []}
    return wily_state_summary.parse_roadmap(wily_state_summary.read_text(path))


def save_roadmap(root: Path, roadmap: dict[str, Any]) -> None:
    path = state_dir(root) / "roadmap.yaml"
    path.write_text(serialize_roadmap(roadmap), encoding="utf-8")


def find_phase(roadmap: dict[str, Any], phase_id: str) -> Phase | None:
    for phase in roadmap.get("phases") or []:
        if str(phase.get("id")) == phase_id:
            return phase
    return None


def find_stage(roadmap: dict[str, Any], stage_id: str) -> Stage | None:
    for stage in roadmap.get("stages") or []:
        if str(stage.get("id")) == stage_id:
            return stage
    return None


def stage_state_path(root: Path, stage: Stage) -> Path | None:
    stage_path = stage.get("path")
    if not stage_path:
        return None
    return state_dir(root) / str(stage_path) / "stage.yaml"


def load_stage_state(root: Path, stage: Stage) -> dict[str, Any]:
    path = stage_state_path(root, stage)
    if not path or not path.exists():
        return {}
    return wily_state_summary.parse_roadmap(wily_state_summary.read_text(path))


def save_stage_state(root: Path, stage: Stage, stage_state: dict[str, Any]) -> None:
    path = stage_state_path(root, stage)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    phases = stage_state.get("phases") or []
    if stage_state.get("schema") == "wily-roadmap-v2":
        path.write_text(serialize_v2_stage_state(stage, phases), encoding="utf-8")
    else:
        path.write_text(serialize_stage_state(stage, phases), encoding="utf-8")


def find_stage_phase(root: Path, roadmap: dict[str, Any], phase_id: str) -> tuple[Stage, Phase, dict[str, Any]] | None:
    requested_stage_id: str | None = None
    requested_phase_id = phase_id
    if "/" in phase_id:
        requested_stage_id, requested_phase_id = phase_id.split("/", 1)
    for stage in roadmap.get("stages") or []:
        if requested_stage_id is not None and str(stage.get("id")) != requested_stage_id:
            continue
        stage_state = load_stage_state(root, stage)
        for phase in stage_state.get("phases") or []:
            if str(phase.get("id")) == requested_phase_id:
                return stage, phase, stage_state
    return None


def is_v2_roadmap(roadmap: dict[str, Any]) -> bool:
    return wily_state_summary.is_v2_roadmap(roadmap)


def next_ready_phase_ref(root: Path, roadmap: dict[str, Any], stage_id: str | None = None) -> str | None:
    stages = wily_state_summary.enrich_stages_with_local_state(root, roadmap.get("stages") or [])
    stages = wily_state_summary.normalize_v2_stage_statuses(stages)
    if stage_id:
        stages = [stage for stage in stages if str(stage.get("id")) == stage_id]
    candidate = wily_state_summary.next_executable_child_phase(stages)
    if not candidate:
        return None
    stage, phase = candidate
    return wily_state_summary.canonical_phase_ref(stage, phase)


def reject_v2_stage_execution(root: Path, roadmap: dict[str, Any], stage: Stage) -> int:
    stage_id = str(stage.get("id", "unknown"))
    print(f"Stage is not executable: {stage_id}", file=sys.stderr)
    next_ref = next_ready_phase_ref(root, roadmap, stage_id) or next_ready_phase_ref(root, roadmap)
    if next_ref:
        print(f"Next phase: {next_ref}", file=sys.stderr)
    else:
        print(f"Run: wily decompose-stage {stage_id} or wily migrate-state --to wily-roadmap-v2 --dry-run", file=sys.stderr)
    return 1


def stage_phase_display_id(roadmap: dict[str, Any], requested_id: str, stage: Stage, phase: Phase) -> str:
    if is_v2_roadmap(roadmap) or "/" in requested_id:
        return wily_state_summary.canonical_phase_ref(stage, phase)
    return str(phase.get("id", requested_id))


def stage_child_phases_done(stage_state: dict[str, Any]) -> bool:
    phases = stage_state.get("phases") or []
    return bool(phases) and all(phase.get("status") == "done" for phase in phases)


def ready_phase(roadmap: dict[str, Any]) -> Phase | None:
    phases = roadmap.get("phases") or []
    ready = wily_state_summary.executable_phases(phases)
    return ready[0] if ready else None


def ready_stage(roadmap: dict[str, Any]) -> Stage | None:
    stages = roadmap.get("stages") or []
    ready = wily_state_summary.executable_stages(stages)
    return ready[0] if ready else None


def active_stage_context(root: Path, roadmap: dict[str, Any]) -> tuple[Stage, Phase | None] | None:
    active_statuses = {"in_progress", "needs_review", "blocked"}
    for stage in roadmap.get("stages") or []:
        if stage.get("status") not in active_statuses:
            continue
        stage_state = load_stage_state(root, stage)
        for phase in stage_state.get("phases") or []:
            if phase.get("status") in active_statuses:
                return stage, phase
        return stage, None
    return None


def command_next(root: Path) -> int:
    roadmap = load_roadmap(root)
    stages = roadmap.get("stages") or []
    enriched_stages = wily_state_summary.enrich_stages_with_local_state(root, stages) if stages else []
    v2 = is_v2_roadmap(roadmap)
    stage_candidates = (
        wily_state_summary.normalize_v2_stage_statuses(enriched_stages)
        if v2
        else enriched_stages
    )
    ready_stages = (
        wily_state_summary.executable_v2_stages(stage_candidates)
        if v2
        else wily_state_summary.executable_stages(stage_candidates)
    )
    stage = ready_stages[0] if ready_stages else None
    if stage:
        if len(ready_stages) > 1:
            print("Ready stage candidates:")
            for candidate in ready_stages:
                owner = candidate.get("owner") or candidate.get("assignee") or candidate.get("assigned_to") or "unassigned"
                scopes = ", ".join(sorted(wily_state_summary.write_scopes(candidate))) or "unspecified"
                print(f"- {candidate.get('id')} @{owner} ({scopes})")
            has_overlap = any(
                wily_state_summary.write_scopes_overlap(left, right)
                for index, left in enumerate(ready_stages)
                for right in ready_stages[index + 1 :]
            )
            if has_overlap:
                print("Parallel-safe: write_scope overlaps; coordinate before parallel work")
            else:
                print("Parallel-safe: write_scope does not overlap")
            print()
        stage_id = stage.get("id", "unknown")
        title = stage.get("title", "Untitled stage")
        print(f"Next stage: {stage_id} - {title}")
        depends_on = stage.get("depends_on") or []
        print(f"Depends on: {', '.join(str(value) for value in depends_on) if depends_on else 'none'}")
        stage_path = stage.get("path")
        if not stage_path:
            print("Stage path: missing")
            return 0
        folder = state_dir(root) / str(stage_path)
        print(f"Stage path: {folder}")
        if v2 or stage.get("execution_mode") == "decomposed":
            child_phases = stage.get("phases") or []
            if child_phases:
                ready_children = (
                    wily_state_summary.executable_child_phases(stage, stage_candidates)
                    if v2
                    else wily_state_summary.executable_phases(child_phases)
                )
                next_child = ready_children[0] if ready_children else None
                if next_child:
                    child_id = (
                        wily_state_summary.canonical_phase_ref(stage, next_child)
                        if v2
                        else next_child.get("id", "unknown")
                    )
                    child_title = next_child.get("title", "Untitled phase")
                    print(f"Next phase: {child_id} - {child_title}")
                    child_path = next_child.get("path")
                    if child_path:
                        print(f"Phase path: {state_dir(root) / str(child_path)}")
            elif stage.get("decomposition_status") == "applied":
                print("Decomposition warning: missing child phases")
        print()
        context = stage_context_bundle(str(stage_id), str(title), folder)
        print(context.strip())
        print("Approval required before implementation.")
        return 0

    if roadmap.get("stages"):
        active = active_stage_context(root, roadmap)
        if active:
            active_stage, active_phase = active
            stage_id = active_stage.get("id", "unknown")
            title = active_stage.get("title", "Untitled stage")
            print(f"Active stage: {stage_id} - {title}")
            if active_phase:
                phase_id = active_phase.get("id", "unknown")
                phase_title = active_phase.get("title", "Untitled phase")
                print(f"Active phase: {phase_id} - {phase_title}")
                session = active_phase.get("current_session") or active_stage.get("current_session")
            else:
                stage_state = load_stage_state(root, active_stage)
                child_phases = stage_state.get("phases") or active_stage.get("phases") or []
                ready_children = wily_state_summary.executable_phases(child_phases)
                if ready_children:
                    next_child = ready_children[0]
                    child_id = next_child.get("id", "unknown")
                    child_title = next_child.get("title", "Untitled phase")
                    print(f"Next phase: {child_id} - {child_title}")
                    child_path = next_child.get("path")
                    if child_path:
                        print(f"Phase path: {state_dir(root) / str(child_path)}")
                session = active_stage.get("current_session")
            if session:
                print(f"Session: {session}")
            return 0

    phase = ready_phase(roadmap)
    if not phase:
        print("Next phase: none")
        return 0

    phase_id = phase.get("id", "unknown")
    title = phase.get("title", "Untitled phase")
    print(f"Next phase: {phase_id} - {title}")
    depends_on = phase.get("depends_on") or []
    print(f"Depends on: {', '.join(str(value) for value in depends_on) if depends_on else 'none'}")

    phase_path = phase.get("path")
    if not phase_path:
        print("Phase path: missing")
        return 0

    folder = state_dir(root) / str(phase_path)
    print(f"Phase path: {folder}")
    print()
    context, _planner = phase_context_bundle(str(phase_id), str(title), folder)
    print(context.strip())
    print("Approval required before implementation.")
    return 0


def serialize_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, list):
        return "[" + ", ".join(quote(str(item)) for item in value) + "]"
    if isinstance(value, int):
        return str(value)
    return quote(str(value))


def serialize_mapping_entry(prefix: str, key: str, value: Any) -> list[str]:
    if isinstance(value, str) and "\n" in value:
        marker = "|" if value.endswith("\n") else "|-"
        body_prefix = " " * (len(prefix) + 2)
        lines = [f"{prefix}{key}: {marker}"]
        lines.extend(f"{body_prefix}{line}" if line else body_prefix.rstrip() for line in value.splitlines())
        return lines
    return [f"{prefix}{key}: {serialize_scalar(value)}"]


def serialize_roadmap(roadmap: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in roadmap.items():
        if key in {"phases", "stages"}:
            continue
        lines.extend(serialize_mapping_entry("", key, value))

    stages = roadmap.get("stages") or []
    if stages:
        lines.append("stages:")
        for stage in stages:
            lines.extend(serialize_stage(stage))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    phases = roadmap.get("phases") or []
    if not phases:
        lines.append("phases: []")
        return "\n".join(lines) + "\n"

    lines.append("phases:")
    for phase in phases:
        lines.extend(serialize_phase_with_lanes(phase, first_prefix="  - ", rest_prefix="    ", lanes_prefix="    "))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def serialize_nested_mapping(prefix: str, mapping: dict[str, Any], skip: set[str] | None = None) -> list[str]:
    skip = skip or set()
    lines: list[str] = []
    for key, value in mapping.items():
        if key in skip:
            continue
        lines.extend(serialize_mapping_entry(prefix, key, value))
    return lines


def serialize_stage(stage: Stage) -> list[str]:
    lines: list[str] = []
    first = True
    for key, value in stage.items():
        if key == "phases":
            continue
        prefix = "  - " if first else "    "
        lines.extend(serialize_mapping_entry(prefix, key, value))
        first = False
    phases = stage.get("phases") or []
    if phases:
        lines.append("    phases:")
        for phase in phases:
            lines.extend(serialize_phase_with_lanes(phase, first_prefix="      - ", rest_prefix="        ", lanes_prefix="        "))
    return lines


def serialize_phase_with_lanes(phase: Phase, *, first_prefix: str, rest_prefix: str, lanes_prefix: str) -> list[str]:
    lines: list[str] = []
    first = True
    for key, value in phase.items():
        if key == "lanes":
            continue
        prefix = first_prefix if first else rest_prefix
        lines.extend(serialize_mapping_entry(prefix, key, value))
        first = False
    lanes = phase.get("lanes") or []
    if lanes:
        lines.append(f"{lanes_prefix}lanes:")
        for lane in lanes:
            first_lane = True
            for key, value in lane.items():
                prefix = f"{lanes_prefix}  - " if first_lane else f"{lanes_prefix}    "
                lines.extend(serialize_mapping_entry(prefix, key, value))
                first_lane = False
    return lines


def serialize_stage_state(stage: Stage, phases: list[Phase]) -> str:
    data: dict[str, Any] = {
        "stage_id": str(stage.get("id", "unknown")),
        "execution_mode": "decomposed",
        "decomposition_status": "applied",
        "phases": phases,
    }
    return serialize_roadmap(data)


def serialize_v2_stage_state(stage: Stage, phases: list[Phase]) -> str:
    data: dict[str, Any] = {
        "stage_id": str(stage.get("id", "unknown")),
        "schema": "wily-roadmap-v2",
        "phases": phases,
    }
    return serialize_roadmap(data)


def phase_slug(phase_id: str) -> str:
    return phase_id.lower().replace("/", "-")


def slugify_title(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "issue"


def issue_ref(issue: Issue) -> str:
    return f"#{issue.get('number')}"


def issue_title(issue: Issue) -> str:
    return str(issue.get("title") or "Untitled issue")


def issue_state(issue: Issue) -> str:
    return str(issue.get("state") or "OPEN").upper()


def phase_github_refs(phase: Phase) -> set[str]:
    refs: set[str] = set()
    for key in ("github_issues", "github_issue"):
        value = phase.get(key)
        if isinstance(value, list):
            refs.update(str(item) for item in value)
        elif value:
            refs.add(str(value))
    return refs


def load_github_issues(root: Path) -> tuple[list[Issue], str | None]:
    fixture = os.environ.get("WILY_ISSUES_JSON")
    if fixture:
        try:
            loaded = json.loads(fixture)
        except json.JSONDecodeError as exc:
            return [], f"Invalid WILY_ISSUES_JSON: {exc}"
        if not isinstance(loaded, list):
            return [], "Invalid WILY_ISSUES_JSON: expected a list"
        return [issue for issue in loaded if isinstance(issue, dict)], None

    command = [
        "gh",
        "issue",
        "list",
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        "number,title,state,url,assignees,labels",
    ]
    try:
        result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        return [], "GitHub issue source not configured."
    if result.returncode != 0:
        return [], "GitHub issue source not configured."
    try:
        loaded = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [], "GitHub issue source returned invalid JSON."
    if not isinstance(loaded, list):
        return [], "GitHub issue source returned invalid JSON."
    return [issue for issue in loaded if isinstance(issue, dict)], None


def linked_issue_map(phases: list[Phase]) -> dict[str, Phase]:
    linked: dict[str, Phase] = {}
    for phase in phases:
        for ref in phase_github_refs(phase):
            linked[ref] = phase
    return linked


def next_numeric_phase_id(phases: list[Phase]) -> str:
    numeric = []
    for phase in phases:
        pid = str(phase.get("id", ""))
        if pid.isdigit():
            numeric.append(int(pid))
    return f"{(max(numeric) if numeric else 0) + 1:02d}"


def write_issue_phase(root: Path, phase: Phase, issue: Issue) -> None:
    folder = state_dir(root) / str(phase["path"])
    folder.mkdir(parents=True, exist_ok=True)
    number = issue_ref(issue)
    title = issue_title(issue)
    url = str(issue.get("url") or "")
    (folder / "phase.md").write_text(
        "\n".join(
            [
                f"# Phase {phase['id']}: {number} {title}",
                "",
                "## Purpose",
                "",
                f"Implement or resolve GitHub issue {number}.",
                "",
                "## GitHub Issue",
                "",
                f"- Issue: {number}",
                f"- URL: {url or 'not provided'}",
                "",
                "## Expected Starting Conditions",
                "",
                "- The issue remains open and assigned or accepted for Wily roadmap work.",
                "",
                "## Known Risks",
                "",
                "- GitHub issue details may change after this phase is created.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (folder / "planner.md").write_text(
        "# Planner Adapter\n\nRecommended planner: superpowers:writing-plans\n\nUse the planner when issue scope needs detailed implementation steps.\n",
        encoding="utf-8",
    )
    (folder / "prompt.md").write_text(
        f"# Execution Prompt\n\nImplement GitHub issue {number}: {title}\n\nIssue URL: {url or 'not provided'}\n",
        encoding="utf-8",
    )
    (folder / "verification.md").write_text(
        "# Verification\n\nRun the tests or manual checks appropriate for the linked issue.\n",
        encoding="utf-8",
    )
    (folder / "handoff.md").write_text(
        f"# Handoff\n\nStart by reading GitHub issue {number} and confirming current scope before implementation.\n",
        encoding="utf-8",
    )
    (folder / "plan.md").write_text("# Implementation Plan\n\nNo detailed implementation plan exists yet.\n", encoding="utf-8")
    (folder / "notes.md").write_text(f"# Notes\n\nCreated from GitHub issue {number}.\n", encoding="utf-8")


def command_issues(root: Path, args: list[str]) -> int:
    add_to_roadmap = "--add-to-roadmap" in args
    issues, error = load_github_issues(root)
    if error:
        print(error)
        print("Core Wily commands do not require GitHub Issues.")
        return 0

    roadmap = load_roadmap(root)
    phases = roadmap.get("phases")
    if not isinstance(phases, list):
        phases = []
        roadmap["phases"] = phases
    linked = linked_issue_map(phases)
    open_issues = [issue for issue in issues if issue_state(issue) == "OPEN"]
    linked_issues = [issue for issue in open_issues if issue_ref(issue) in linked]
    unlinked = [issue for issue in open_issues if issue_ref(issue) not in linked]

    print("GitHub Issues")
    print()
    print("Linked issues:")
    if linked_issues:
        for issue in linked_issues:
            phase = linked[issue_ref(issue)]
            print(f"- {issue_ref(issue)} {issue_title(issue)} -> {phase.get('id')}")
    else:
        print("- none")

    print()
    print("Unlinked open issues:")
    if unlinked:
        for issue in unlinked:
            print(f"- {issue_ref(issue)} {issue_title(issue)}")
    else:
        print("- none")

    if not unlinked:
        return 0

    print()
    print("Suggested roadmap additions:")
    next_id = next_numeric_phase_id(phases)
    for offset, issue in enumerate(unlinked):
        suggested = f"{int(next_id) + offset:02d}" if next_id.isdigit() else f"github-{issue.get('number')}"
        print(f"- {suggested} {issue_ref(issue)} {issue_title(issue)}")

    if not add_to_roadmap:
        print()
        print("Run with `--add-to-roadmap` only after approval.")
        return 0

    version = roadmap.get("roadmap_version")
    roadmap["roadmap_version"] = (version if isinstance(version, int) else 1) + 1
    existing_ids = {str(phase.get("id")) for phase in phases}
    added: list[Phase] = []
    for issue in unlinked:
        phase_id = next_numeric_phase_id(phases)
        while phase_id in existing_ids:
            phase_id = f"{int(phase_id) + 1:02d}"
        existing_ids.add(phase_id)
        ref = issue_ref(issue)
        title = f"{ref} {issue_title(issue)}"
        path = f"phases/{phase_id}-github-issue-{issue.get('number')}-{slugify_title(issue_title(issue))}"
        phase: Phase = {
            "id": phase_id,
            "title": title,
            "path": path,
            "status": "pending",
            "depends_on": [],
            "github_issues": [ref],
            "github_urls": [str(issue.get("url") or "")],
            "sync_policy": "manual",
        }
        phases.append(phase)
        added.append(phase)
        write_issue_phase(root, phase, issue)

    save_roadmap(root, roadmap)
    print()
    print("Added roadmap phases from GitHub issues:")
    for phase in added:
        print(f"- {phase['id']} {phase['title']}")
    return 0


def session_glob(root: Path, phase_id: str) -> list[Path]:
    return sorted((state_dir(root) / "sessions").glob(f"*phase-{phase_slug(phase_id)}-attempt-*"))


def next_attempt(root: Path, phase_id: str) -> int:
    return len(session_glob(root, phase_id)) + 1


def stage_session_glob(root: Path, stage_id: str) -> list[Path]:
    return sorted((state_dir(root) / "sessions").glob(f"*stage-{phase_slug(stage_id)}-attempt-*"))


def next_stage_attempt(root: Path, stage_id: str) -> int:
    return len(stage_session_glob(root, stage_id)) + 1


def session_status_text(
    phase_id: str,
    attempt: int,
    status: str,
    blocker: str | None = None,
    planner: str | None = None,
) -> str:
    lines = [
        f'phase: "{phase_id}"',
        f"attempt: {attempt}",
        f'status: "{status}"',
    ]
    if planner:
        lines.append(f"planner: {quote(planner)}")
    if blocker:
        lines.append(f"blocker: {quote(blocker)}")
    return "\n".join(lines) + "\n"


SESSION_STATUS_CORE_KEYS = {"phase", "attempt", "status", "planner", "blocker"}


def preserved_session_status_blocks(text: str) -> str:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line and not line.startswith(" ") and ":" in line:
            key = line.split(":", 1)[0]
            if key not in SESSION_STATUS_CORE_KEYS:
                if blocks and blocks[-1].strip():
                    blocks.append("")
                blocks.append(line)
                index += 1
                while index < len(lines) and (not lines[index].strip() or lines[index].startswith(" ")):
                    blocks.append(lines[index])
                    index += 1
                continue
        index += 1
    return "\n".join(blocks).strip()


def markdown_section(title: str, content: str) -> str:
    body = content.strip() or "Missing."
    return f"## {title}\n\n{body}\n"


def planner_recommendation(planner_text: str) -> str | None:
    for line in planner_text.splitlines():
        stripped = line.strip()
        prefix = "Recommended planner:"
        if stripped.startswith(prefix):
            value = stripped[len(prefix) :].strip()
            return value or None
    return None


def phase_context_bundle(phase_id: str, title: str, folder: Path | None) -> tuple[str, str | None]:
    if folder is None:
        return (
            "\n".join(
                [
                    "# Wily Phase Context",
                    "",
                    f"Phase: {phase_id} - {title}",
                    "",
                    "Phase folder is missing.",
                    "",
                ]
            ),
            None,
        )

    phase_text = wily_state_summary.read_text(folder / "phase.md")
    planner_text = wily_state_summary.read_text(folder / "planner.md")
    prompt_text = wily_state_summary.read_text(folder / "prompt.md")
    verification_text = wily_state_summary.read_text(folder / "verification.md")
    handoff_text = wily_state_summary.read_text(folder / "handoff.md")
    plan_text = wily_state_summary.read_text(folder / "plan.md")
    planner = planner_recommendation(planner_text)

    if not plan_text.strip():
        plan_text = "\n".join(
            [
                "No implementation plan exists yet.",
                "Use the recommended planner to create one if this phase needs a detailed plan.",
            ]
        )

    content = "\n".join(
        [
            "# Wily Phase Context",
            "",
            f"Phase: {phase_id} - {title}",
            "",
            markdown_section("Phase", phase_text),
            markdown_section("Planner Adapter", planner_text),
            markdown_section("Prompt", prompt_text),
            markdown_section("Verification", verification_text),
            markdown_section("Handoff", handoff_text),
            markdown_section("Existing Implementation Plan", plan_text),
        ]
    )
    return content, planner


def stage_context_bundle(stage_id: str, title: str, folder: Path | None) -> str:
    if folder is None:
        return "\n".join(
            [
                "# Wily Stage Context",
                "",
                f"Stage: {stage_id} - {title}",
                "",
                "Stage folder is missing.",
                "",
            ]
        )

    stage_text = wily_state_summary.read_text(folder / "stage.md")
    prompt_text = wily_state_summary.read_text(folder / "prompt.md")
    verification_text = wily_state_summary.read_text(folder / "verification.md")
    handoff_text = wily_state_summary.read_text(folder / "handoff.md")
    notes_text = wily_state_summary.read_text(folder / "notes.md")

    return "\n".join(
        [
            "# Wily Stage Context",
            "",
            f"Stage: {stage_id} - {title}",
            "",
            markdown_section("Stage", stage_text),
            markdown_section("Prompt", prompt_text),
            markdown_section("Verification", verification_text),
            markdown_section("Handoff", handoff_text),
            markdown_section("Notes", notes_text),
        ]
    )


def create_session(root: Path, phase: Phase, attempt: int) -> Path:
    phase_id = str(phase.get("id", "unknown"))
    title = str(phase.get("title", "Untitled phase"))
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session = state_dir(root) / "sessions" / f"{stamp}-phase-{phase_slug(phase_id)}-attempt-{attempt}"
    session.mkdir(parents=True, exist_ok=False)

    phase_path = phase.get("path")
    phase_folder = state_dir(root) / str(phase_path) if phase_path else None
    input_text, planner = phase_context_bundle(phase_id, title, phase_folder)
    verification = wily_state_summary.read_text(phase_folder / "verification.md") if phase_folder else ""

    (session / "status.yaml").write_text(
        session_status_text(phase_id, attempt, "started", planner=planner),
        encoding="utf-8",
    )
    (session / "input.md").write_text(input_text, encoding="utf-8")
    (session / "result.md").write_text("# Result\n\nPending.\n", encoding="utf-8")
    (session / "verification.md").write_text(verification or "# Verification\n\nPending.\n", encoding="utf-8")
    (session / "changed-files.md").write_text("# Changed Files\n\nPending.\n", encoding="utf-8")
    return session


def create_stage_session(root: Path, stage: Stage, attempt: int) -> Path:
    stage_id = str(stage.get("id", "unknown"))
    title = str(stage.get("title", "Untitled stage"))
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session = state_dir(root) / "sessions" / f"{stamp}-stage-{phase_slug(stage_id)}-attempt-{attempt}"
    session.mkdir(parents=True, exist_ok=False)

    stage_path = stage.get("path")
    stage_folder = state_dir(root) / str(stage_path) if stage_path else None
    input_text = stage_context_bundle(stage_id, title, stage_folder)
    verification = wily_state_summary.read_text(stage_folder / "verification.md") if stage_folder else ""

    (session / "status.yaml").write_text(
        session_status_text(stage_id, attempt, "started"),
        encoding="utf-8",
    )
    (session / "input.md").write_text(input_text, encoding="utf-8")
    (session / "result.md").write_text("# Result\n\nPending.\n", encoding="utf-8")
    (session / "verification.md").write_text(verification or "# Verification\n\nPending.\n", encoding="utf-8")
    (session / "changed-files.md").write_text("# Changed Files\n\nPending.\n", encoding="utf-8")
    return session


def relative_session_path(root: Path, session: Path) -> str:
    return session.relative_to(state_dir(root)).as_posix()


def current_session_path(root: Path, phase: Phase) -> Path | None:
    value = phase.get("current_session")
    if not value:
        return None
    return state_dir(root) / str(value)


def update_session_status(root: Path, phase: Phase, status: str, blocker: str | None = None) -> None:
    session = current_session_path(root, phase)
    if not session:
        return
    status_path = session / "status.yaml"
    attempt = 1
    name = session.name
    marker = "-attempt-"
    if marker in name:
        suffix = name.rsplit(marker, 1)[-1]
        if suffix.isdigit():
            attempt = int(suffix)
    planner = None
    preserved = ""
    if status_path.exists():
        existing = status_path.read_text(encoding="utf-8")
        preserved = preserved_session_status_blocks(existing)
        for line in existing.splitlines():
            if line.startswith("planner:"):
                planner = wily_state_summary.parse_scalar(line.split(":", 1)[1].strip())
                break
    text = session_status_text(str(phase.get("id", "unknown")), attempt, status, blocker, planner)
    if preserved:
        text = text.rstrip() + "\n" + preserved + "\n"
    status_path.write_text(text, encoding="utf-8")


def snapshot_runner_session(root: Path, phase: Phase, recommended_status: str) -> None:
    try:
        import wily_runner
    except ImportError:
        return
    wily_runner.snapshot_runner_artifacts(root, phase, recommended_status)


def require_phase_id(args: list[str], command: str) -> str | None:
    if args:
        return args[0]
    print(f"Usage: wily.py {command} <stage-id>/<phase-id>", file=sys.stderr)
    return None


def command_start(root: Path, args: list[str], *, retry: bool = False) -> int:
    phase_id = require_phase_id(args, "retry" if retry else "start")
    if not phase_id:
        return 2
    roadmap = load_roadmap(root)
    phase = find_phase(roadmap, phase_id)
    if not phase:
        found = find_stage_phase(root, roadmap, phase_id)
        if found:
            stage, phase, stage_state = found
            display_id = stage_phase_display_id(roadmap, phase_id, stage, phase)
            warn_board_live_claims({**phase, "id": display_id, "stage_id": stage.get("id", "")})
            attempt = next_attempt(root, display_id)
            session = create_session(root, {**phase, "id": display_id}, attempt)
            phase["status"] = "in_progress"
            phase["current_session"] = relative_session_path(root, session)
            stage["status"] = "in_progress"
            stage["current_session"] = relative_session_path(root, session)
            phase.pop("blocker", None)
            save_stage_state(root, stage, stage_state)
            save_roadmap(root, roadmap)
            live_payload = open_live_session(root, {**phase, "stage_id": stage.get("id", "")})
            event_payload = {**phase, **live_payload, "id": display_id, "stage_id": stage.get("id", "")}
            if board_live_enabled(root):
                _surface_emit_failure(
                    "start",
                    emit_board_live_event(root, event_payload, "start", "claimed"),
                )
            else:
                print(
                    "Board bridge: not configured (run 'wily board check')",
                    file=sys.stderr,
                )
            if heartbeat_enabled(root):
                spawn_heartbeat_sidecar(root, event_payload, str(live_payload["session_id"]))
            if retry:
                print(f"Started phase {display_id} attempt {attempt}")
            else:
                print(f"Started phase {display_id}")
            print(f"Session: {session}")
            return 0
        stage = find_stage(roadmap, phase_id)
        if not stage:
            print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
            return 1
        if is_v2_roadmap(roadmap):
            return reject_v2_stage_execution(root, roadmap, stage)
        warn_board_live_claims(stage)
        attempt = next_stage_attempt(root, phase_id)
        session = create_stage_session(root, stage, attempt)
        stage["status"] = "in_progress"
        stage["current_session"] = relative_session_path(root, session)
        stage.pop("blocker", None)
        save_roadmap(root, roadmap)
        live_payload = open_live_session(root, stage)
        event_payload = {**stage, **live_payload, "id": stage.get("id", phase_id)}
        if board_live_enabled(root):
            _surface_emit_failure(
                "start",
                emit_board_live_event(root, event_payload, "start", "claimed"),
            )
        else:
            print(
                "Board bridge: not configured (run 'wily board check')",
                file=sys.stderr,
            )
        if heartbeat_enabled(root):
            spawn_heartbeat_sidecar(root, event_payload, str(live_payload["session_id"]))
        if retry:
            print(f"Started stage {phase_id} attempt {attempt}")
        else:
            print(f"Started stage {phase_id}")
        print(f"Session: {session}")
        return 0

    warn_board_live_claims(phase)
    attempt = next_attempt(root, phase_id)
    session = create_session(root, phase, attempt)
    phase["status"] = "in_progress"
    phase["current_session"] = relative_session_path(root, session)
    if "blocker" in phase:
        del phase["blocker"]
    save_roadmap(root, roadmap)
    live_payload = open_live_session(root, phase)
    event_payload = {**phase, **live_payload, "id": phase.get("id", phase_id)}
    if board_live_enabled(root):
        _surface_emit_failure(
            "start",
            emit_board_live_event(root, event_payload, "start", "claimed"),
        )
    else:
        print(
            "Board bridge: not configured (run 'wily board check')",
            file=sys.stderr,
        )
    if heartbeat_enabled(root):
        spawn_heartbeat_sidecar(root, event_payload, str(live_payload["session_id"]))

    if retry:
        print(f"Started phase {phase_id} attempt {attempt}")
    else:
        print(f"Started phase {phase_id}")
    print(f"Session: {session}")
    return 0


def command_complete(root: Path, args: list[str]) -> int:
    phase_id = require_phase_id(args, "complete")
    if not phase_id:
        return 2
    roadmap = load_roadmap(root)
    phase = find_phase(roadmap, phase_id)
    if not phase:
        found = find_stage_phase(root, roadmap, phase_id)
        if found:
            stage, phase, stage_state = found
            display_id = stage_phase_display_id(roadmap, phase_id, stage, phase)
            phase["status"] = "done"
            phase.pop("blocker", None)
            if stage_child_phases_done(stage_state):
                stage["status"] = "done"
            update_session_status(root, {**phase, "id": display_id}, "verified")
            save_stage_state(root, stage, stage_state)
            save_roadmap(root, roadmap)
            close_live_sessions(
                root,
                {**phase, "id": display_id, "stage_id": stage.get("id", "")},
                event="complete",
                live_status="completed_local",
            )
            print(f"Completed phase {display_id}")
            return 0
        stage = find_stage(roadmap, phase_id)
        if not stage:
            print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
            return 1
        if is_v2_roadmap(roadmap):
            return reject_v2_stage_execution(root, roadmap, stage)
        stage["status"] = "done"
        stage.pop("blocker", None)
        update_session_status(root, stage, "verified")
        save_roadmap(root, roadmap)
        close_live_sessions(root, stage, event="complete", live_status="completed_local")
        print(f"Completed stage {phase_id}")
        return 0
    phase["status"] = "done"
    phase.pop("blocker", None)
    update_session_status(root, phase, "verified")
    snapshot_runner_session(root, phase, "done")
    save_roadmap(root, roadmap)
    close_live_sessions(root, phase, event="complete", live_status="completed_local")
    print(f"Completed phase {phase_id}")
    return 0


def command_block(root: Path, args: list[str]) -> int:
    phase_id = require_phase_id(args, "block")
    if not phase_id:
        return 2
    reason = " ".join(args[1:]).strip() or "Blocked without recorded reason"
    roadmap = load_roadmap(root)
    phase = find_phase(roadmap, phase_id)
    if not phase:
        found = find_stage_phase(root, roadmap, phase_id)
        if found:
            stage, phase, stage_state = found
            display_id = stage_phase_display_id(roadmap, phase_id, stage, phase)
            phase["status"] = "blocked"
            phase["blocker"] = reason
            stage["status"] = "blocked"
            stage["blocker"] = reason
            update_session_status(root, {**phase, "id": display_id}, "blocked", reason)
            save_stage_state(root, stage, stage_state)
            save_roadmap(root, roadmap)
            close_live_sessions(
                root,
                {**phase, "id": display_id, "stage_id": stage.get("id", "")},
                event="block",
                live_status="blocked_local",
                note=reason,
            )
            print(f"Blocked phase {display_id}: {reason}")
            return 0
        stage = find_stage(roadmap, phase_id)
        if not stage:
            print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
            return 1
        if is_v2_roadmap(roadmap):
            return reject_v2_stage_execution(root, roadmap, stage)
        stage["status"] = "blocked"
        stage["blocker"] = reason
        update_session_status(root, stage, "blocked", reason)
        save_roadmap(root, roadmap)
        close_live_sessions(root, stage, event="block", live_status="blocked_local", note=reason)
        print(f"Blocked stage {phase_id}: {reason}")
        return 0
    phase["status"] = "blocked"
    phase["blocker"] = reason
    update_session_status(root, phase, "blocked", reason)
    snapshot_runner_session(root, phase, "blocked")
    save_roadmap(root, roadmap)
    close_live_sessions(root, phase, event="block", live_status="blocked_local", note=reason)
    print(f"Blocked phase {phase_id}: {reason}")
    return 0


def heartbeat_usage() -> str:
    return (
        "Usage: wily.py live-heartbeat <stage-id>/<phase-id> [--interval seconds] [--count n] "
        "[--note text] [--session id] [--parent-shell-pid pid] [--ttl seconds] [--foreground]"
    )


def resolve_live_phase(root: Path, roadmap: dict[str, Any], phase_id: str) -> Phase | None:
    phase = find_phase(roadmap, phase_id)
    if phase:
        return phase
    found = find_stage_phase(root, roadmap, phase_id)
    if found:
        stage, child_phase, _stage_state = found
        return {**child_phase, "stage_id": stage.get("id", "")}
    stage = find_stage(roadmap, phase_id)
    if stage:
        return stage
    return None


def command_live_heartbeat(root: Path, args: list[str]) -> int:
    if not args:
        print(heartbeat_usage(), file=sys.stderr)
        return 2
    if not board_live_enabled(root):
        print(
            "Board live heartbeat requires WILY_BOARD_URL, WILY_BOARD_SECRET, WILY_BOARD_REPO, and WILY_BOARD_ACTOR.",
            file=sys.stderr,
        )
        return 1

    phase_id = args[0]
    interval = 15.0
    count = 0
    note = "active"
    session_id = ""
    parent_shell_pid = 0
    ttl = 0.0
    index = 1
    while index < len(args):
        option = args[index]
        if option == "--interval" and index + 1 < len(args):
            try:
                interval = float(args[index + 1])
            except ValueError:
                print("Invalid --interval value", file=sys.stderr)
                return 2
            if interval < 0:
                print("Invalid --interval value", file=sys.stderr)
                return 2
            index += 2
            continue
        if option == "--count" and index + 1 < len(args):
            try:
                count = int(args[index + 1])
            except ValueError:
                print("Invalid --count value", file=sys.stderr)
                return 2
            if count < 0:
                print("Invalid --count value", file=sys.stderr)
                return 2
            index += 2
            continue
        if option == "--note" and index + 1 < len(args):
            note = args[index + 1]
            index += 2
            continue
        if option == "--session" and index + 1 < len(args):
            session_id = args[index + 1]
            index += 2
            continue
        if option == "--parent-shell-pid" and index + 1 < len(args):
            try:
                parent_shell_pid = int(args[index + 1])
            except ValueError:
                print("Invalid --parent-shell-pid value", file=sys.stderr)
                return 2
            index += 2
            continue
        if option == "--ttl" and index + 1 < len(args):
            try:
                ttl = float(args[index + 1])
            except ValueError:
                print("Invalid --ttl value", file=sys.stderr)
                return 2
            if ttl < 0:
                print("Invalid --ttl value", file=sys.stderr)
                return 2
            index += 2
            continue
        if option == "--foreground":
            index += 1
            continue
        print(heartbeat_usage(), file=sys.stderr)
        return 2

    roadmap = load_roadmap(root)
    phase = resolve_live_phase(root, roadmap, phase_id)
    if not phase:
        print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
        return 1
    active = resolve_active_live_payload(root, item_id=phase_id, session_id=session_id)
    if active:
        phase = {**phase}
        if not session_id:
            session_id = str(active.get("session_id") or "")
        if active.get("session_path") and not phase.get("current_session"):
            phase["current_session"] = active["session_path"]
        if "checkpoint" in active and "checkpoint" not in phase:
            phase["checkpoint"] = active["checkpoint"]

    sent = 0
    started = time.monotonic()
    if session_id:
        live_root(root).mkdir(parents=True, exist_ok=True)
        live_pid_path(root, session_id).write_text(str(os.getpid()) + "\n", encoding="utf-8")
    try:
        while count == 0 or sent < count:
            if parent_shell_pid and not process_alive(parent_shell_pid):
                close_live_sessions(root, {**phase, "session_id": session_id}, event="release", live_status="released")
                break
            if session_id and not live_alive_path(root, session_id).exists():
                close_live_sessions(root, {**phase, "session_id": session_id}, event="release", live_status="released")
                break
            if ttl and time.monotonic() - started >= ttl:
                close_live_sessions(root, {**phase, "session_id": session_id}, event="release", live_status="released")
                break
            payload = write_live_registry(
                root,
                phase,
                event="heartbeat",
                live_status="active",
                note=note,
                session_id=session_id or None,
                parent_shell_pid=parent_shell_pid or None,
            )
            _surface_emit_failure(
                "heartbeat",
                emit_board_live_event(
                    root,
                    {**phase, **payload, "id": phase.get("id", phase_id)},
                    "heartbeat",
                    "active",
                    note,
                ),
            )
            sent += 1
            if count and sent >= count:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print()

    print(f"Heartbeat sent for {phase_id}: {sent}")
    return 0


def live_worked_usage() -> str:
    return (
        "Usage: wily.py live-worked [<stage-id>/<phase-id>|item-id] [--session id] "
        "[--agent name] [--tool name] [--summary text] [--from-hook]"
    )


def command_live_worked(root: Path, args: list[str]) -> int:
    item_id = ""
    session_id = ""
    agent = ""
    tool = ""
    summary = ""
    from_hook = False
    index = 0
    if args and not args[0].startswith("--"):
        item_id = args[0]
        index = 1
    while index < len(args):
        option = args[index]
        if option == "--session" and index + 1 < len(args):
            session_id = args[index + 1]
            index += 2
            continue
        if option == "--agent" and index + 1 < len(args):
            agent = args[index + 1]
            index += 2
            continue
        if option == "--tool" and index + 1 < len(args):
            tool = args[index + 1]
            index += 2
            continue
        if option == "--summary" and index + 1 < len(args):
            summary = args[index + 1]
            index += 2
            continue
        if option == "--from-hook":
            from_hook = True
            index += 1
            continue
        print(live_worked_usage(), file=sys.stderr)
        return 2

    active = resolve_active_live_payload(root, item_id=item_id, session_id=session_id, agent=agent)
    if active is None:
        if from_hook:
            return 0
        print("No active Wily live session found.", file=sys.stderr)
        return 1

    session_id = str(active.get("session_id") or session_id)
    item_id = item_id or str(active.get("item_id") or active.get("phase_id") or active.get("stage_id") or "")
    roadmap = load_roadmap(root)
    phase = resolve_live_phase(root, roadmap, item_id) or {
        "id": item_id,
        "item_id": item_id,
        "item_type": active.get("item_type", "phase"),
        "phase_id": active.get("phase_id", ""),
        "stage_id": active.get("stage_id", ""),
        "current_session": active.get("session_path", ""),
    }
    event_item = {
        **phase,
        "session_id": session_id,
        "agent": agent or active.get("agent") or live_agent(root),
        "tool": tool,
        "summary": summary,
    }
    if "checkpoint" in active:
        event_item["checkpoint"] = active["checkpoint"]
    payload = write_live_registry(
        root,
        event_item,
        event="worked",
        live_status="active",
        note=summary,
        session_id=session_id,
    )
    if tool:
        payload["tool"] = tool
    if summary:
        payload["summary"] = summary
    path = live_active_dir(root) / f"{session_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _surface_emit_failure(
        "worked",
        emit_board_live_event(
            root,
            {**event_item, **payload, "id": phase.get("id", item_id)},
            "worked",
            "active",
            summary,
        ),
    )
    print(f"Worked event recorded for {item_id or session_id}")
    return 0


def command_release(root: Path, args: list[str]) -> int:
    phase_id = require_phase_id(args, "release")
    if not phase_id:
        return 2
    roadmap = load_roadmap(root)
    phase = resolve_live_phase(root, roadmap, phase_id)
    if not phase:
        print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
        return 1
    close_live_sessions(root, phase, event="release", live_status="released")
    print(f"Released live session for {phase_id}")
    return 0


def hook_command(target: str) -> str:
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} live-worked --from-hook --agent {shlex.quote(target)}"


def command_hooks(root: Path, args: list[str]) -> int:
    if not args or args[0] != "install":
        print("Usage: wily.py hooks install --target codex|claude [--path file]", file=sys.stderr)
        return 2
    target = ""
    path = None
    index = 1
    while index < len(args):
        option = args[index]
        if option == "--target" and index + 1 < len(args):
            target = args[index + 1]
            index += 2
            continue
        if option == "--path" and index + 1 < len(args):
            path = Path(args[index + 1])
            index += 2
            continue
        print("Usage: wily.py hooks install --target codex|claude [--path file]", file=sys.stderr)
        return 2
    if target not in {"codex", "claude"}:
        print("--target must be codex or claude", file=sys.stderr)
        return 2
    if path is None:
        path = Path.home() / (".codex/hooks.json" if target == "codex" else ".claude/settings.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    command = hook_command(target)
    payload = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                        }
                    ],
                }
            ]
        }
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed {target} hook: {path}")
    return 0


def board_usage() -> str:
    return "Usage: wily.py board check [--hooks-path file] [--probe] | board sync-local <stage-id>"


def probe_board_endpoint(values: dict[str, str]) -> str:
    url = values.get("WILY_BOARD_URL", "").rstrip("/")
    secret = values.get("WILY_BOARD_SECRET", "")
    repo = values.get("WILY_BOARD_REPO", "")
    actor = values.get("WILY_BOARD_ACTOR", "")
    if not (url and secret and repo):
        return "skipped (missing config)"
    query = urllib.parse.urlencode(
        {"repo": repo, "phase_id": "__probe__", "actor": actor}
    )
    request = urllib.request.Request(
        f"{url}/api/live/claims?{query}",
        method="GET",
        headers={"X-Wily-Signature": board_live_signature(secret, b"")},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return f"ok (HTTP {response.status})"
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            return f"rejected (HTTP {exc.code})"
        if 500 <= exc.code < 600:
            return f"server error (HTTP {exc.code})"
        return f"unexpected (HTTP {exc.code})"
    except urllib.error.URLError as exc:
        return f"unreachable ({exc.reason})"
    except OSError as exc:
        return f"unreachable ({exc})"


def command_board(root: Path, args: list[str]) -> int:
    if not args:
        print(board_usage(), file=sys.stderr)
        return 2
    if args[0] == "sync-local":
        return command_board_sync_local(root, args[1:])
    if args[0] != "check":
        print(board_usage(), file=sys.stderr)
        return 2
    hooks_path = Path.home() / ".codex" / "hooks.json"
    probe_requested = False
    index = 1
    while index < len(args):
        option = args[index]
        if option == "--hooks-path" and index + 1 < len(args):
            hooks_path = Path(args[index + 1])
            index += 2
            continue
        if option == "--probe":
            probe_requested = True
            index += 1
            continue
        print(board_usage(), file=sys.stderr)
        return 2

    values = board_live_config_values(root)
    missing = missing_board_live_config_keys(root)
    ok = True
    if missing:
        ok = False
        print("Board live config: missing")
        print("Missing: " + ", ".join(missing))
    else:
        config = redacted_board_live_config(board_live_config(root) or {})
        print("Board live config: ok")
        print(f"url: {config.get('WILY_BOARD_URL', '')}")
        print(f"repo: {config.get('WILY_BOARD_REPO', '')}")
        print(f"actor: {config.get('WILY_BOARD_ACTOR', '')}")
        print(f"agent: {config.get('WILY_BOARD_AGENT', '')}")
        print(f"secret: {config.get('WILY_BOARD_SECRET', '<redacted>')}")

    if values.get("WILY_BOARD_SECRET"):
        probe = b'{"probe":"wily-board-check"}'
        signature = board_live_signature(values["WILY_BOARD_SECRET"], probe)
        print(f"signature: ready ({signature.split('=', 1)[0]})")
    else:
        print("signature: missing secret")

    if codex_hook_installed(hooks_path):
        print(f"Codex hook: ok ({hooks_path})")
    else:
        ok = False
        print(f"Codex hook: missing ({hooks_path})")

    if probe_requested and not missing:
        print(f"endpoint: {probe_board_endpoint(values)}")
    elif probe_requested:
        print("endpoint: not probed (config missing)")
    else:
        print("endpoint: not probed")

    cache = read_board_last_emit(root)
    success = cache.get("last_success") if isinstance(cache, dict) else None
    failure = cache.get("last_failure") if isinstance(cache, dict) else None
    if isinstance(success, dict) and success.get("at"):
        print(
            f"last bridge success: {success.get('event', '?')} at {success['at']}"
        )
    if isinstance(failure, dict) and failure.get("at"):
        print(
            f"last bridge failure: {failure.get('event', '?')} at {failure['at']} ({failure.get('reason', '?')})"
        )
    return 0 if ok else 1


def codex_bridge_should_emit_worked(notification: dict[str, Any]) -> bool:
    return str(notification.get("method") or "") in {"item/completed", "hook/completed"}


def codex_bridge_tool_name(notification: dict[str, Any]) -> str:
    params = notification.get("params")
    item = params.get("item") if isinstance(params, dict) else None
    if isinstance(item, dict):
        return str(item.get("name") or item.get("type") or "codex-item")
    return "codex-item"


def command_codex_bridge(root: Path, args: list[str]) -> int:
    session_id = ""
    fixture = None
    agent = "codex-desktop"
    index = 0
    while index < len(args):
        option = args[index]
        if option == "--session" and index + 1 < len(args):
            session_id = args[index + 1]
            index += 2
            continue
        if option == "--fixture" and index + 1 < len(args):
            fixture = Path(args[index + 1])
            index += 2
            continue
        if option == "--agent" and index + 1 < len(args):
            agent = args[index + 1]
            index += 2
            continue
        if option == "--once":
            index += 1
            continue
        print("Usage: wily.py codex-bridge --session id [--fixture jsonl] [--once]", file=sys.stderr)
        return 2
    if not session_id:
        print("--session is required", file=sys.stderr)
        return 2
    if fixture is None or not fixture.exists():
        print("codex-bridge unavailable; live activity will remain heartbeat-only", file=sys.stderr)
        return 0
    for line in fixture.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            notification = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(notification, dict) or not codex_bridge_should_emit_worked(notification):
            continue
        command_live_worked(
            root,
            [
                "--from-hook",
                "--session",
                session_id,
                "--agent",
                agent,
                "--tool",
                codex_bridge_tool_name(notification),
            ],
        )
    return 0


def command_replan(root: Path, args: list[str]) -> int:
    reason = " ".join(args).strip() or "Roadmap target changed"
    state = state_dir(root)
    revisions = state / "revisions"
    revisions.mkdir(parents=True, exist_ok=True)
    roadmap_path = state / "roadmap.yaml"
    roadmap = load_roadmap(root)
    current_version = roadmap.get("roadmap_version")
    version = current_version if isinstance(current_version, int) else 1
    roadmap["roadmap_version"] = version + 1
    roadmap_path.write_text(serialize_roadmap(roadmap), encoding="utf-8")

    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    revision_path = revisions / f"{stamp}-replan-{version}.md"
    completed = [phase for phase in roadmap.get("phases") or [] if phase.get("status") == "done"]
    revision_path.write_text(
        "\n".join(
            [
                f"# Roadmap Revision {version}",
                "",
                f"Reason: {reason}",
                "",
                "Completed phases kept:",
                *[f"- {phase.get('id')} {phase.get('title', 'Untitled phase')}" for phase in completed],
                *([] if completed else ["- none"]),
                "",
                "Next action:",
                "- Revise future phases from the current implementation baseline.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Recorded replan revision: {revision_path}")
    print(f"Roadmap version: {version + 1}")
    return 0


def stage_decomposition_proposal(stage: Stage) -> list[Phase]:
    stage_id = str(stage.get("id", "stage"))
    title = str(stage.get("title", "Untitled stage"))
    return [
        {
            "id": f"{stage_id}-p01",
            "title": f"{title} implementation slice",
            "status": "pending",
            "depends_on": [],
            "parallel_group": f"{stage_id}-lane-a",
            "lanes": [
                {
                    "id": "server-lane",
                    "title": "Server-side work",
                    "write_scope": ["src/server"],
                },
                {
                    "id": "client-lane",
                    "title": "Client-side work",
                    "write_scope": ["src/client"],
                },
            ],
        },
        {
            "id": f"{stage_id}-p02",
            "title": f"{title} integration and verification",
            "status": "pending",
            "depends_on": [f"{stage_id}-p01"],
            "parallel_group": None,
            "lanes": [],
        },
    ]


def print_stage_decomposition(stage: Stage, phases: list[Phase]) -> None:
    stage_id = stage.get("id", "unknown")
    print(f"Stage decomposition proposal: {stage_id}")
    print("Automatic decomposition is disabled; apply only after user approval.")
    for phase in phases:
        print(f"- {phase.get('id')} {phase.get('title')}")
        lanes = phase.get("lanes") or []
        if lanes:
            print(f"  parallel lanes: {len(lanes)}")
            for lane in lanes:
                scope = ", ".join(str(value) for value in lane.get("write_scope") or [])
                print(f"  - {lane.get('id')} write_scope: {scope}")


def stage_decomposition_from_json(path: Path) -> tuple[list[Phase], str | None]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [], f"Cannot read decomposition file: {exc}"
    except json.JSONDecodeError as exc:
        return [], f"Invalid decomposition JSON: {exc}"
    if not isinstance(loaded, list):
        return [], "Invalid decomposition JSON: expected a list of phases."
    if not loaded:
        return [], "Invalid decomposition JSON: expected at least one phase."
    phases: list[Phase] = []
    for index, item in enumerate(loaded, start=1):
        if not isinstance(item, dict):
            return [], f"Invalid decomposition JSON: phase {index} is not an object."
        if not item.get("id") or not item.get("title"):
            return [], f"Invalid decomposition JSON: phase {index} needs id and title."
        lanes = item.get("lanes") or []
        if not isinstance(lanes, list):
            return [], f"Invalid decomposition JSON: phase {item.get('id')} lanes must be a list."
        for lane_index, lane in enumerate(lanes, start=1):
            if not isinstance(lane, dict):
                return [], f"Invalid decomposition JSON: lane {lane_index} in {item.get('id')} is not an object."
            if not lane.get("id"):
                return [], f"Invalid decomposition JSON: lane {lane_index} in {item.get('id')} needs id."
        phase = dict(item)
        phase.setdefault("status", "pending")
        phase.setdefault("depends_on", [])
        phase.setdefault("lanes", lanes)
        phases.append(phase)
    return phases, None


def write_decomposed_stage_phase_files(root: Path, stage: Stage, phases: list[Phase]) -> None:
    stage_path = str(stage.get("path") or f"stages/{stage.get('id')}")
    stage_folder = state_dir(root) / stage_path
    stage_folder.mkdir(parents=True, exist_ok=True)
    (stage_folder / "stage.yaml").write_text(serialize_stage_state(stage, phases), encoding="utf-8")
    phase_root = state_dir(root) / stage_path / "phases"
    for phase in phases:
        phase_id = str(phase.get("id"))
        folder = phase_root / phase_id
        folder.mkdir(parents=True, exist_ok=True)
        title = str(phase.get("title") or "Untitled phase")
        lanes = phase.get("lanes") or []
        lane_lines = []
        for lane in lanes:
            scope = ", ".join(str(value) for value in lane.get("write_scope") or [])
            lane_lines.append(f"- {lane.get('id')}: {lane.get('title')} ({scope})")
        (folder / "phase.md").write_text(
            "\n".join(
                [
                    f"# Phase {phase_id}: {title}",
                    "",
                    "## Purpose",
                    "",
                    "Execute one decomposed slice of the parent Stage.",
                    "",
                    "## Parallel Lanes",
                    "",
                    *(lane_lines or ["- none"]),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (folder / "planner.md").write_text(
            "# Planner\n\nRecommended planner: manual\n",
            encoding="utf-8",
        )
        (folder / "prompt.md").write_text(f"# Execution Prompt\n\nImplement {phase_id}: {title}\n", encoding="utf-8")
        (folder / "verification.md").write_text("# Verification\n\nRun phase-scoped checks.\n", encoding="utf-8")
        (folder / "handoff.md").write_text("# Handoff\n\nRead the parent Stage and lane write scopes first.\n", encoding="utf-8")
        (folder / "plan.md").write_text("# Implementation Plan\n\nNo detailed implementation plan exists yet.\n", encoding="utf-8")
        (folder / "notes.md").write_text("# Notes\n\nCreated by stage decomposition.\n", encoding="utf-8")


def stage_position(roadmap: dict[str, Any], stage_id: str) -> int | None:
    for index, stage in enumerate(roadmap.get("stages") or [], start=1):
        if str(stage.get("id")) == stage_id:
            return index
    return None


def warn_stage_decomposition_board_recovery(stage_id: str) -> None:
    print(
        "Board reflection recovery: run `wily board check --probe`, then "
        f"`wily board sync-local {stage_id}` after fixing Board config or reachability; "
        "actual-site verification remains incomplete.",
        file=sys.stderr,
    )


def command_migrate_state_usage() -> str:
    return "Usage: wily.py migrate-state --to wily-roadmap-v2 (--dry-run|--apply|--prune-legacy)"


def migration_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def migration_backup_path(root: Path, stamp: str) -> Path:
    return state_dir(root) / "backups" / f"{stamp}-wily-roadmap-v2"


def migration_report_paths(root: Path, stamp: str) -> tuple[Path, Path]:
    base = state_dir(root) / "migrations" / f"{stamp}-wily-roadmap-v2"
    return base.with_suffix(".md"), base.with_suffix(".json")


def copy_migration_backup(root: Path, backup: Path) -> None:
    backup.mkdir(parents=True, exist_ok=True)
    state = state_dir(root)
    for name in ("roadmap.yaml", "project.md", "status.md", "decisions.md"):
        source = state / name
        if source.exists():
            shutil.copy2(source, backup / name)
    for name in ("stages", "phases", "sessions", "revisions"):
        source = state / name
        if source.exists():
            shutil.copytree(source, backup / name, dirs_exist_ok=True)


def stage_slug(stage_id: str, title: str) -> str:
    title_slug = slugify_title(title)
    if title_slug.startswith(stage_id):
        return title_slug
    return f"{stage_id}-{title_slug}"


def default_stage_path(stage_id: str, title: str) -> str:
    return f"stages/{stage_slug(stage_id, title)}"


def migration_stage_for_phase(index: int, phase: Phase) -> Stage:
    stage_id = f"s{index:02d}"
    title = str(phase.get("title") or f"Stage {index:02d}")
    return {
        "id": stage_id,
        "title": title,
        "path": default_stage_path(stage_id, title),
        "status": phase.get("status", "pending"),
        "depends_on": [],
        "owner": phase.get("owner") or phase.get("lead") or "codex",
    }


def phase_dependency_refs(stage: Stage, phase: Phase, legacy_phase_mappings: dict[str, str]) -> list[str]:
    refs: list[str] = []
    for dependency in phase.get("depends_on") or []:
        value = str(dependency)
        if value in legacy_phase_mappings:
            refs.append(legacy_phase_mappings[value])
        elif "/" in value:
            refs.append(value)
        elif value.startswith("s"):
            refs.append(value)
        else:
            refs.append(f"{stage.get('id')}/{value}")
    return refs


def migration_transform(root: Path, roadmap: dict[str, Any]) -> dict[str, Any]:
    legacy_phases = [dict(phase) for phase in roadmap.get("phases") or [] if isinstance(phase, dict)]
    original_stages = [dict(stage) for stage in roadmap.get("stages") or [] if isinstance(stage, dict)]
    warnings: list[str] = []
    changed_files = [".wily/roadmap.yaml"]
    legacy_phase_mappings: dict[str, str] = {}

    if not original_stages and legacy_phases:
        phase_to_stage: dict[str, str] = {}
        generated: list[Stage] = []
        for index, phase in enumerate(legacy_phases, start=1):
            stage = migration_stage_for_phase(index, phase)
            generated.append(stage)
            phase_to_stage[str(phase.get("id"))] = str(stage["id"])
            phase["stage_id"] = stage["id"]
        for stage, phase in zip(generated, legacy_phases, strict=False):
            stage["depends_on"] = [
                phase_to_stage[str(dependency)]
                for dependency in phase.get("depends_on") or []
                if str(dependency) in phase_to_stage
            ]
        original_stages = generated

    stages = original_stages
    stages_by_id = {str(stage.get("id")): stage for stage in stages if stage.get("id")}
    grouped_legacy: dict[str, list[tuple[Phase, str]]] = {str(stage.get("id")): [] for stage in stages}

    for phase in legacy_phases:
        old_id = str(phase.get("id"))
        stage_id = str(phase.get("stage_id") or "")
        if not stage_id or stage_id not in stages_by_id:
            if len(stages) == 1:
                stage_id = str(stages[0].get("id"))
            else:
                warnings.append(f"Legacy phase {old_id} has no valid stage_id; skipped.")
                continue
        new_id = f"p{len(grouped_legacy.setdefault(stage_id, [])) + 1:02d}"
        grouped_legacy[stage_id].append((phase, new_id))
        legacy_phase_mappings[old_id] = f"{stage_id}/{new_id}"

    stage_phase_map: dict[str, list[Phase]] = {}
    for stage in stages:
        stage_id = str(stage.get("id"))
        phase_rows: list[Phase] = []
        stage_state = load_stage_state(root, stage)
        existing = [dict(phase) for phase in stage_state.get("phases") or [] if isinstance(phase, dict)]
        if existing:
            for phase in existing:
                phase.setdefault("runner", "custom-workflow")
                phase.setdefault(
                    "path",
                    f"{stage.get('path')}/phases/{phase.get('id')}-{slugify_title(str(phase.get('title', phase.get('id'))))}",
                )
                phase_rows.append(phase)
        for legacy_phase, new_id in grouped_legacy.get(stage_id, []):
            title = str(legacy_phase.get("title") or stage.get("title") or new_id)
            migrated = {
                "id": new_id,
                "title": title,
                "status": legacy_phase.get("status", "pending"),
                "depends_on": phase_dependency_refs(stage, legacy_phase, legacy_phase_mappings),
                "owner": legacy_phase.get("owner") or legacy_phase.get("lead") or stage.get("owner") or "codex",
                "runner": legacy_phase.get("runner") or "custom-workflow",
                "path": f"{stage.get('path')}/phases/{new_id}-{slugify_title(title)}",
            }
            for key in ("current_session", "summary", "blocker", "verification"):
                if key in legacy_phase:
                    migrated[key] = legacy_phase[key]
            phase_rows.append(migrated)
        if not phase_rows and stage.get("status") != "superseded":
            title = str(stage.get("title") or f"{stage_id} implementation")
            phase_rows.append(
                {
                    "id": "p01",
                    "title": title,
                    "status": stage.get("status", "pending"),
                    "depends_on": [],
                    "owner": stage.get("owner") or "codex",
                    "runner": "custom-workflow",
                    "path": f"{stage.get('path')}/phases/p01-{slugify_title(title)}",
                }
            )
        stage_phase_map[stage_id] = phase_rows
        changed_files.append(f".wily/{stage.get('path')}/stage.yaml")

    normalized_for_status: list[Stage] = []
    for stage in stages:
        copy = dict(stage)
        copy["phases"] = stage_phase_map.get(str(stage.get("id")), [])
        normalized_for_status.append(copy)
    normalized_for_status = wily_state_summary.normalize_v2_stage_statuses(normalized_for_status)
    status_by_id = {str(stage.get("id")): stage.get("status") for stage in normalized_for_status}

    migrated_stages: list[Stage] = []
    for stage in stages:
        copy = {key: value for key, value in stage.items() if key != "phases"}
        copy.setdefault("path", default_stage_path(str(copy.get("id")), str(copy.get("title", "Stage"))))
        copy["status"] = status_by_id.get(str(copy.get("id")), copy.get("status", "pending"))
        migrated_stages.append(copy)

    migrated_roadmap = {
        key: value
        for key, value in roadmap.items()
        if key not in {"phases", "stages", "roadmap_version", "roadmap_schema"}
    }
    migrated_roadmap["roadmap_schema"] = "wily-roadmap-v2"
    migrated_roadmap["stages"] = migrated_stages

    return {
        "roadmap": migrated_roadmap,
        "stage_phase_map": stage_phase_map,
        "phase_mappings": legacy_phase_mappings,
        "changed_files": changed_files,
        "warnings": warnings,
    }


def write_migration_reports(
    root: Path,
    stamp: str,
    mode: str,
    transform: dict[str, Any],
    backup: Path | None,
) -> tuple[Path, Path]:
    report_md, report_json = migration_report_paths(root, stamp)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "target_schema": "wily-roadmap-v2",
        "created_at": utc_now_z(),
        "backup": str(backup.relative_to(root)) if backup else "",
        "changed_files": transform["changed_files"],
        "phase_mappings": transform["phase_mappings"],
        "warnings": transform["warnings"],
    }
    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Wily Roadmap v2 Migration Report",
        "",
        f"- Mode: {mode}",
        "- Target schema: wily-roadmap-v2",
        f"- Backup: {payload['backup'] or 'none'}",
        "",
        "## Changed Files",
        *[f"- {path}" for path in transform["changed_files"]],
        "",
        "## Phase Mappings",
        *[f"- {old} -> {new}" for old, new in sorted(transform["phase_mappings"].items())],
        *(["- none"] if not transform["phase_mappings"] else []),
        "",
        "## Warnings",
        *[f"- {warning}" for warning in transform["warnings"]],
        *(["- none"] if not transform["warnings"] else []),
        "",
    ]
    report_md.write_text("\n".join(lines), encoding="utf-8")
    return report_md, report_json


def write_migrated_v2_state(root: Path, transform: dict[str, Any]) -> None:
    save_roadmap(root, transform["roadmap"])
    stages_by_id = {str(stage.get("id")): stage for stage in transform["roadmap"].get("stages") or []}
    for stage_id, phases in transform["stage_phase_map"].items():
        stage = stages_by_id.get(stage_id)
        if not stage:
            continue
        path = stage_state_path(root, stage)
        if not path:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialize_v2_stage_state(stage, phases), encoding="utf-8")


def command_migrate_state(root: Path, args: list[str]) -> int:
    if "--to" not in args:
        print(command_migrate_state_usage(), file=sys.stderr)
        return 2
    target_index = args.index("--to")
    if target_index + 1 >= len(args) or args[target_index + 1] != "wily-roadmap-v2":
        print("Only --to wily-roadmap-v2 is supported.", file=sys.stderr)
        return 2
    modes = [flag for flag in ("--dry-run", "--apply", "--prune-legacy") if flag in args]
    if len(modes) != 1:
        print(command_migrate_state_usage(), file=sys.stderr)
        return 2
    mode = modes[0].lstrip("-")
    roadmap = load_roadmap(root)
    transform = migration_transform(root, roadmap)
    stamp = migration_stamp()
    backup = migration_backup_path(root, stamp)
    report_md, report_json = migration_report_paths(root, stamp)

    print(f"Migration mode: {mode}")
    print("Target schema: wily-roadmap-v2")
    for old, new in sorted(transform["phase_mappings"].items()):
        print(f"- {new} <- {old}")
    if transform["warnings"]:
        print("Warnings:")
        for warning in transform["warnings"]:
            print(f"- {warning}")

    if mode == "dry-run":
        print(f"Would write backup: {backup.relative_to(root)}")
        print(f"Would write reports: {report_md.relative_to(root)}, {report_json.relative_to(root)}")
        for path in transform["changed_files"]:
            print(f"Would change: {path}")
        return 0

    if mode == "prune-legacy":
        legacy = state_dir(root) / "phases"
        if not legacy.exists():
            print("No legacy .wily/phases directory to prune.")
            return 0
        shutil.rmtree(legacy)
        print("Pruned legacy .wily/phases directory.")
        return 0

    copy_migration_backup(root, backup)
    write_migrated_v2_state(root, transform)
    written_md, written_json = write_migration_reports(root, stamp, mode, transform, backup)
    print(f"Backup: {backup.relative_to(root)}")
    print(f"Report: {written_md.relative_to(root)}")
    print(f"Report: {written_json.relative_to(root)}")
    print("Migration applied.")
    return 0


def emit_stage_decomposition_live_draft(
    root: Path,
    stage: Stage,
    phases: list[Phase],
    *,
    position: int | None = None,
) -> BoardLiveEventResult:
    stage_id = str(stage.get("id", "unknown"))
    if not board_live_enabled(root):
        missing = ", ".join(missing_board_live_config_keys(root))
        print(
            f"Board live draft not sent: missing Wily Board live config ({missing}).",
            file=sys.stderr,
        )
        warn_stage_decomposition_board_recovery(stage_id)
        return False, "missing config"
    draft_payload = live_draft_stage_decomposition_payload(root, stage, phases, position=position)
    result = emit_board_live_event(root, draft_payload, "stage_decomposed_local", "active")
    ok = result[0] if isinstance(result, tuple) else bool(result)
    detail = result[1] if isinstance(result, tuple) and len(result) > 1 else ""
    if ok:
        print(f"Board live draft sent for {stage_id}: {len(phases)} phases")
    else:
        suffix = f" ({detail})" if detail else ""
        print(f"Board live draft failed for {stage_id}: Wily Board event was not stored{suffix}.", file=sys.stderr)
        warn_stage_decomposition_board_recovery(stage_id)
    return result


def command_board_sync_local(root: Path, args: list[str]) -> int:
    stage_id = args[0] if args else ""
    if not stage_id:
        print("Usage: wily.py board sync-local <stage-id>", file=sys.stderr)
        return 2
    roadmap = load_roadmap(root)
    stage = find_stage(roadmap, stage_id)
    if not stage:
        print(f"Stage not found: {stage_id}", file=sys.stderr)
        return 1
    stage_state = load_stage_state(root, stage)
    phases = stage_state.get("phases") or []
    if not phases:
        print(f"No local decomposed phases found for {stage_id}", file=sys.stderr)
        return 1
    result = emit_stage_decomposition_live_draft(
        root,
        stage,
        phases,
        position=stage_position(roadmap, stage_id),
    )
    ok = result[0] if isinstance(result, tuple) else bool(result)
    if ok:
        print(f"Board local draft synced for {stage_id}: {len(phases)} phases")
    return 0


def command_decompose_stage(root: Path, args: list[str]) -> int:
    stage_id = require_phase_id(args, "decompose-stage")
    if not stage_id:
        return 2
    roadmap = load_roadmap(root)
    stage = find_stage(roadmap, stage_id)
    if not stage:
        print(f"Stage not found: {stage_id}", file=sys.stderr)
        return 1

    from_json: Path | None = None
    if "--from-json" in args:
        index = args.index("--from-json")
        try:
            from_json = Path(args[index + 1])
        except IndexError:
            print("Usage: wily.py decompose-stage <stage-id> --from-json <path>", file=sys.stderr)
            return 2

    phases = stage_decomposition_proposal(stage)
    if from_json:
        phases, error = stage_decomposition_from_json(from_json)
        if error:
            print(error, file=sys.stderr)
            return 1

    if "--dry-run" in args or "--apply-fixture" not in args:
        print_stage_decomposition(stage, phases)
        if "--apply-fixture" not in args and not from_json:
            print("No files changed.")
        if from_json and "--dry-run" not in args:
            stage["execution_mode"] = "decomposed"
            stage["decomposition_status"] = "applied"
            stage.pop("phases", None)
            write_decomposed_stage_phase_files(root, stage, phases)
            save_roadmap(root, roadmap)
            emit_stage_decomposition_live_draft(root, stage, phases, position=stage_position(roadmap, stage_id))
            print(f"Decomposed stage {stage_id}")
            print(f"Stage path: {state_dir(root) / str(stage.get('path'))}")
        return 0

    stage["execution_mode"] = "decomposed"
    stage["decomposition_status"] = "applied"
    stage.pop("phases", None)
    write_decomposed_stage_phase_files(root, stage, phases)
    save_roadmap(root, roadmap)
    emit_stage_decomposition_live_draft(root, stage, phases, position=stage_position(roadmap, stage_id))
    print(f"Decomposed stage {stage_id}")
    print(f"Stage path: {state_dir(root) / str(stage.get('path'))}")
    return 0


def watch_interval(args: list[str]) -> float:
    if "--interval" not in args:
        return 2.0
    index = args.index("--interval")
    try:
        return max(0.2, float(args[index + 1]))
    except (IndexError, ValueError):
        return 2.0


def watch_ui(args: list[str]) -> str:
    if "--ui" not in args:
        return "auto"
    index = args.index("--ui")
    try:
        value = args[index + 1].strip().lower()
    except IndexError:
        return "auto"
    return value if value in {"auto", "ascii", "rich"} else "auto"


def rich_available() -> bool:
    if os.environ.get("WILY_FORCE_NO_RICH"):
        return False
    add_watch_dependency_path()
    try:
        import rich  # noqa: F401
    except ImportError:
        return False
    return True


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def watch_venv_dir() -> Path:
    return plugin_root() / ".venv-watch"


def watch_venv_python() -> Path:
    if sys.platform == "win32":
        return watch_venv_dir() / "Scripts" / "python.exe"
    return watch_venv_dir() / "bin" / "python"


def watch_dependency_paths() -> list[Path]:
    venv = watch_venv_dir()
    if sys.platform == "win32":
        return list((venv / "Lib").glob("site-packages"))
    return list((venv / "lib").glob("python*/site-packages"))


def add_watch_dependency_path() -> None:
    for path in watch_dependency_paths():
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def rich_install_commands() -> list[list[str]]:
    requirements = plugin_root() / "requirements-watch.txt"
    return [
        [sys.executable, "-m", "venv", str(watch_venv_dir())],
        [str(watch_venv_python()), "-m", "pip", "install", "-r", str(requirements)],
    ]


def command_install_watch_ui(args: list[str]) -> int:
    commands = rich_install_commands()
    if "--dry-run-install" in args:
        print("\n".join(format_shell_command(command) for command in commands))
        return 0
    for command in commands:
        result = subprocess.run(command, text=True, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def watch_output(
    root: Path,
    interval: float = 2.0,
    ui: str = "auto",
    *,
    expand_done: bool = False,
    interactive: bool = False,
    show_rich_hint: bool = True,
    scroll_offset: int = 0,
) -> str:
    use_rich = ui != "ascii" and rich_available()
    body = wily_watch_ui.render_watch(
        root,
        interval=interval,
        rich=use_rich,
        expand_done=expand_done,
        interactive=interactive,
        scroll_offset=scroll_offset,
    )
    if show_rich_hint and not use_rich and ui in {"auto", "rich"} and not rich_available():
        return "\n".join(
            [
                "Rich UI is not installed.",
                "Run: $wily-watch --install-ui",
                "Fallback: using ASCII watch UI.",
                "",
                body,
            ]
        )
    return body


def parse_watch_mouse_event(data: str) -> tuple[int, int, int, bool] | None:
    match = WATCH_MOUSE_RE.search(data)
    if not match:
        return None
    button, x, y, kind = match.groups()
    return int(button), int(x), int(y), kind == "M"


def watch_action_from_input(
    data: str,
    *,
    summary_row: int = WATCH_BODY_START_ROW,
    body_rows: int = 1,
    expand_done: bool = False,
) -> str | None:
    if not data:
        return None
    if "\x03" in data or "q" in data:
        return "quit"
    if "r" in data:
        return "refresh"
    if "d" in data:
        return "toggle_done"

    mouse = parse_watch_mouse_event(data)
    if not mouse:
        return None
    button, _x, y, pressed = mouse
    if not pressed:
        return None
    if button == WATCH_MOUSE_WHEEL_UP:
        return "scroll_up" if expand_done else None
    if button == WATCH_MOUSE_WHEEL_DOWN:
        return "scroll_down" if expand_done else None
    if button == WATCH_MOUSE_RIGHT:
        return "tmux_menu"
    if button != WATCH_MOUSE_LEFT:
        return None

    end_row = summary_row + max(0, body_rows)
    if summary_row <= y < end_row:
        return "toggle_done"
    return None


def apply_watch_scroll_action(current: int, action: str | None, *, max_offset: int) -> int:
    if action == "scroll_down":
        return min(max_offset, current + 1)
    if action == "scroll_up":
        return max(0, current - 1)
    return min(max(0, current), max_offset)


def tmux_context_menu_command(x: int, y: int) -> list[str]:
    return [
        "tmux",
        "display-menu",
        "-T",
        "#[align=centre]#{pane_index} (#{pane_id})",
        "-x",
        str(x),
        "-y",
        str(y),
        "Horizontal Split",
        "h",
        "split-window -h",
        "Vertical Split",
        "v",
        "split-window -v",
        "",
        "",
        "",
        "Copy Mode",
        "c",
        "copy-mode",
        "#{?pane_marked,Unmark,Mark}",
        "m",
        "select-pane -m",
        "#{?#{>:#{window_panes},1},,-}#{?window_zoomed_flag,Unzoom,Zoom}",
        "z",
        "resize-pane -Z",
        "",
        "",
        "",
        "Kill",
        "X",
        "kill-pane",
        "Respawn",
        "R",
        "respawn-pane -k",
    ]


def show_tmux_context_menu(data: str) -> None:
    if not os.environ.get("TMUX"):
        return
    mouse = parse_watch_mouse_event(data)
    if not mouse:
        return
    button, x, y, pressed = mouse
    if button != WATCH_MOUSE_RIGHT or not pressed:
        return
    subprocess.run(
        tmux_context_menu_command(x, y),
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def tmux_watch_command(root: Path, args: list[str]) -> list[str]:
    script = Path(__file__).resolve()
    interval = watch_interval(args)
    parts = [
        "cd",
        shlex.quote(str(root)),
        "&&",
        shlex.quote(sys.executable),
        shlex.quote(str(script)),
        "watch",
        "--here",
        "--ui",
        shlex.quote(watch_ui(args)),
        "--interval",
        shlex.quote(f"{interval:.1f}"),
    ]
    if "--show-done" in args:
        parts.append("--show-done")
    if "--no-interactive" in args:
        parts.append("--no-interactive")
    inner = " ".join(parts)
    command = ["tmux", "split-window"]
    current_pane = os.environ.get("TMUX_PANE", "").strip()
    if current_pane:
        command.extend(["-t", current_pane])
    command.extend(["-h", inner])
    return command


def format_shell_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def command_watch_pane(root: Path, args: list[str]) -> int:
    command = tmux_watch_command(root, args)
    if "--dry-run-pane" in args:
        print(format_shell_command(command))
        return 0

    if not os.environ.get("TMUX"):
        print("tmux 세션이 아니라서 pane을 열 수 없습니다.", file=sys.stderr)
        print(
            "현재 pane에서 보려면 다음을 실행하세요: "
            f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} watch --here",
            file=sys.stderr,
        )
        return 1

    result = subprocess.run(command, text=True, check=False)
    return result.returncode


def watch_launch_mode(args: list[str], *, in_tmux: bool, stdin_tty: bool, stdout_tty: bool) -> str:
    if "--here" in args:
        return "here"
    if in_tmux:
        return "pane"
    if stdin_tty and stdout_tty:
        return "here"
    return "needs_interactive_terminal"


def watch_here_noninteractive(root: Path, interval: float, ui: str, *, expand_done: bool) -> int:
    try:
        while True:
            print("\033[2J\033[H", end="")
            print(watch_output(root, interval, ui, expand_done=expand_done), flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0


def read_watch_input(timeout: float) -> str:
    ready, _write, _error = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return ""
    try:
        return os.read(sys.stdin.fileno(), 64).decode(errors="ignore")
    except OSError:
        return ""


def watch_here_interactive(root: Path, interval: float, ui: str, *, expand_done: bool) -> int:
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    current_expand_done = expand_done
    scroll_offset = 0
    body_rows = 1
    try:
        tty.setcbreak(fd)
        sys.stdout.write(WATCH_MOUSE_ENABLE)
        sys.stdout.flush()
        while True:
            terminal_size = shutil.get_terminal_size((80, 24))
            use_rich = ui != "ascii" and rich_available()
            visible_body_rows = max(1, terminal_size.lines - wily_watch_ui.CHROME_ROWS)
            total_body_rows = wily_watch_ui.rendered_body_row_count(
                root,
                width=terminal_size.columns,
                rich=use_rich,
                expand_done=current_expand_done,
            )
            max_scroll_offset = max(0, total_body_rows - visible_body_rows) if current_expand_done else 0
            scroll_offset = apply_watch_scroll_action(scroll_offset, None, max_offset=max_scroll_offset)
            output = watch_output(
                root,
                interval,
                ui,
                expand_done=current_expand_done,
                interactive=True,
                show_rich_hint=False,
                scroll_offset=scroll_offset,
            )
            body_rows = max(1, len(output.splitlines()) - wily_watch_ui.CHROME_ROWS)
            print("\033[2J\033[H", end="")
            print(output, flush=True)
            input_data = read_watch_input(interval)
            action = watch_action_from_input(
                input_data,
                body_rows=body_rows,
                expand_done=current_expand_done,
            )
            if action == "quit":
                return 0
            if action == "toggle_done":
                current_expand_done = not current_expand_done
                scroll_offset = 0
            if action in {"scroll_up", "scroll_down"}:
                scroll_offset = apply_watch_scroll_action(scroll_offset, action, max_offset=max_scroll_offset)
            if action == "tmux_menu":
                show_tmux_context_menu(input_data)
            if action in {"toggle_done", "refresh", "scroll_up", "scroll_down", "tmux_menu"}:
                continue
    except KeyboardInterrupt:
        return 0
    finally:
        sys.stdout.write(WATCH_MOUSE_DISABLE)
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


def command_watch(root: Path, args: list[str]) -> int:
    if "--install-ui" in args:
        return command_install_watch_ui(args)
    interval = watch_interval(args)
    ui = watch_ui(args)
    expand_done = "--show-done" in args
    if "--once" in args:
        print(watch_output(root, interval, ui, expand_done=expand_done))
        return 0
    mode = watch_launch_mode(
        args,
        in_tmux=bool(os.environ.get("TMUX")),
        stdin_tty=sys.stdin.isatty(),
        stdout_tty=sys.stdout.isatty(),
    )
    if mode == "pane":
        return command_watch_pane(root, args)
    if mode == "needs_interactive_terminal":
        print("wily watch needs an interactive terminal outside tmux.", file=sys.stderr)
        print("In Codex app, open a side terminal and run: ./wily watch", file=sys.stderr)
        print(
            "For a one-shot text preview, run: "
            f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} watch --once --ui ascii",
            file=sys.stderr,
        )
        return 1

    can_interact = "--no-interactive" not in args and sys.stdin.isatty() and sys.stdout.isatty()
    if can_interact:
        return watch_here_interactive(root, interval, ui, expand_done=expand_done)
    return watch_here_noninteractive(root, interval, ui, expand_done=expand_done)


def command_run(root: Path, args: list[str]) -> int:
    import wily_runner

    return wily_runner.command_run(root, args)


def command_land_usage() -> str:
    return "Usage: wily.py land <stage-id>/<phase-id> [--base branch] [--message text] [--direct|--pr]"


def resolve_land_item(root: Path, roadmap: dict[str, Any], phase_id: str) -> tuple[str, Phase] | None:
    phase = find_phase(roadmap, phase_id)
    if phase:
        return phase_id, phase
    found = find_stage_phase(root, roadmap, phase_id)
    if found:
        stage, phase, _stage_state = found
        return stage_phase_display_id(roadmap, phase_id, stage, phase), {
            **phase,
            "id": stage_phase_display_id(roadmap, phase_id, stage, phase),
            "stage_id": stage.get("id", ""),
        }
    stage = find_stage(roadmap, phase_id)
    if stage and not is_v2_roadmap(roadmap):
        return phase_id, stage
    return None


def git_step(root: Path, args: list[str], label: str) -> subprocess.CompletedProcess[str]:
    result = git_run(root, args)
    if result.returncode != 0:
        print(f"{label} failed: {format_shell_command(['git', *args])}", file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        elif result.stdout.strip():
            print(result.stdout.strip(), file=sys.stderr)
    return result


def cleanup_land_artifacts(root: Path, item: Phase) -> int:
    removed = 0
    wanted = {
        str(item.get("id", "")),
        str(item.get("phase_id", "")),
        str(item.get("stage_id", "")),
    }
    wanted.discard("")
    for path in active_live_registry_files(root):
        payload = read_live_registry(path)
        if not payload:
            continue
        values = {
            str(payload.get("id", "")),
            str(payload.get("item_id", "")),
            str(payload.get("phase_id", "")),
            str(payload.get("stage_id", "")),
        }
        if wanted & values:
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def print_land_commit_paths(root: Path) -> int:
    diff = git_run(root, ["diff", "--cached", "--name-status"])
    if diff.returncode != 0:
        print("Unable to list commit paths.", file=sys.stderr)
        if diff.stderr.strip():
            print(diff.stderr.strip(), file=sys.stderr)
        return diff.returncode
    paths = [line for line in diff.stdout.splitlines() if line.strip()]
    if not paths:
        return 0
    print("Commit paths:")
    for line in paths:
        print(line)
    return 0


def command_land(root: Path, args: list[str]) -> int:
    if not args:
        print(command_land_usage(), file=sys.stderr)
        return 2
    phase_id = args[0]
    base = "main"
    message = ""
    mode = "direct"
    index = 1
    while index < len(args):
        arg = args[index]
        if arg == "--base":
            if index + 1 >= len(args):
                print("Missing value for --base", file=sys.stderr)
                return 2
            base = args[index + 1]
            index += 2
            continue
        if arg == "--message":
            if index + 1 >= len(args):
                print("Missing value for --message", file=sys.stderr)
                return 2
            message = args[index + 1]
            index += 2
            continue
        if arg == "--direct":
            mode = "direct"
            index += 1
            continue
        if arg == "--pr":
            mode = "pr"
            index += 1
            continue
        print(f"Unknown land option: {arg}", file=sys.stderr)
        print(command_land_usage(), file=sys.stderr)
        return 2

    roadmap = load_roadmap(root)
    resolved = resolve_land_item(root, roadmap, phase_id)
    if not resolved:
        print(f"Phase or stage not found: {phase_id}", file=sys.stderr)
        return 1
    display_id, item = resolved
    if item.get("status") != "done":
        print(f"Phase is not done: {display_id}", file=sys.stderr)
        return 1

    git_root = git_install_root(root)
    if not git_root:
        print("Cannot land outside a git repository.", file=sys.stderr)
        return 1
    branch = current_git_branch(git_root)
    if not branch:
        print("Cannot land while HEAD is detached.", file=sys.stderr)
        return 1
    if not git_stdout(git_root, ["config", "--get", "remote.origin.url"]):
        print("No origin remote configured.", file=sys.stderr)
        return 1
    if not message:
        title = str(item.get("title") or "Wily phase")
        message = f"land {display_id}: {title}"

    add = git_step(git_root, ["add", "-A"], "Stage changes")
    if add.returncode != 0:
        return add.returncode

    status = git_run(git_root, ["status", "--porcelain"])
    if status.returncode != 0:
        print("Unable to read git status.", file=sys.stderr)
        if status.stderr.strip():
            print(status.stderr.strip(), file=sys.stderr)
        return status.returncode
    if status.stdout.strip():
        listed = print_land_commit_paths(git_root)
        if listed != 0:
            return listed
        commit = git_step(git_root, ["commit", "-m", message], "Commit")
        if commit.returncode != 0:
            return commit.returncode
        print(f"Committed: {git_commit(git_root, 'HEAD') or 'unknown'}")
    else:
        print("No local changes to commit.")

    push_branch = git_step(git_root, ["push", "-u", "origin", branch], "Push branch")
    if push_branch.returncode != 0:
        return push_branch.returncode
    print(f"Pushed branch: {branch}")

    if mode == "pr":
        if shutil.which("gh") is None:
            print("Cannot create PR because gh is not installed.", file=sys.stderr)
            return 1
        pr = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base,
                "--head",
                branch,
                "--title",
                message,
                "--body",
                f"Lands Wily phase {display_id}.",
            ],
            cwd=git_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if pr.returncode != 0:
            print("PR creation failed.", file=sys.stderr)
            if pr.stderr.strip():
                print(pr.stderr.strip(), file=sys.stderr)
            return pr.returncode
        if pr.stdout.strip():
            print(pr.stdout.strip())
        checkout = git_step(git_root, ["checkout", base], "Checkout base")
        if checkout.returncode != 0:
            return checkout.returncode
        pull = git_step(git_root, ["pull", "--ff-only", "origin", base], "Pull base")
        if pull.returncode != 0:
            return pull.returncode
        cleaned = cleanup_land_artifacts(root, item)
        print(f"Checked out {base}")
        if cleaned:
            print(f"Cleaned local live artifacts: {cleaned}")
        return 0

    checkout = git_step(git_root, ["checkout", base], "Checkout base")
    if checkout.returncode != 0:
        return checkout.returncode
    pull = git_step(git_root, ["pull", "--ff-only", "origin", base], "Pull base")
    if pull.returncode != 0:
        return pull.returncode
    merge = git_step(git_root, ["merge", "--ff-only", branch], "Fast-forward merge")
    if merge.returncode != 0:
        return merge.returncode
    push_base = git_step(git_root, ["push", "origin", base], "Push base")
    if push_base.returncode != 0:
        return push_base.returncode
    cleaned = cleanup_land_artifacts(root, item)
    print(f"Landed on {base}")
    print(f"Pushed base: {base}")
    if cleaned:
        print(f"Cleaned local live artifacts: {cleaned}")
    return 0


def command_clean_usage() -> str:
    return "Usage: wily.py clean [--yes]"


def cleanable_artifact_paths(root: Path) -> list[Path]:
    candidates: list[Path] = []
    live_dir = root / ".wily" / "local" / "live"
    if live_dir.is_dir():
        candidates.extend(path for path in live_dir.rglob("*") if path.is_file())
    board_emit = root / ".wily" / "local" / "board-last-emit.json"
    if board_emit.exists():
        candidates.append(board_emit)
    for dirname in (".playwright-mcp", ".pytest_cache"):
        path = root / dirname
        if path.exists():
            candidates.append(path)
    for path in root.rglob("__pycache__"):
        if path.is_dir() and ".git" not in path.parts:
            candidates.append(path)
    for path in root.rglob("*.pyc"):
        if path.is_file() and ".git" not in path.parts:
            candidates.append(path)
    unique: dict[str, Path] = {}
    root_resolved = root.resolve()
    covered_dirs = {
        path.resolve()
        for path in candidates
        if path.is_dir()
    }
    for path in candidates:
        try:
            resolved = path.resolve()
            resolved.relative_to(root_resolved)
        except ValueError:
            continue
        if path.is_file() and any(parent in covered_dirs for parent in resolved.parents):
            continue
        unique[resolved.as_posix()] = path
    return sorted(unique.values(), key=lambda value: relative_display_path(root, value))


def relative_display_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def remove_cleanable_artifact(path: Path) -> bool:
    try:
        if path.is_dir():
            shutil.rmtree(path)
            return True
        if path.exists():
            path.unlink()
            return True
    except OSError:
        return False
    return False


def command_clean(root: Path, args: list[str]) -> int:
    yes = False
    for arg in args:
        if arg == "--yes":
            yes = True
            continue
        if arg == "--dry-run":
            continue
        print(f"Unknown clean option: {arg}", file=sys.stderr)
        print(command_clean_usage(), file=sys.stderr)
        return 2

    candidates = cleanable_artifact_paths(root)
    if not candidates:
        print("No cleanable artifacts found.")
        return 0

    if not yes:
        print("Cleanable artifacts:")
        for path in candidates:
            print(f"- {relative_display_path(root, path)}")
        print("Dry run only. Run wily clean --yes to remove these artifacts.")
        return 0

    removed: list[Path] = []
    failed: list[Path] = []
    for path in candidates:
        if remove_cleanable_artifact(path):
            removed.append(path)
        else:
            failed.append(path)
    if removed:
        print("Removed cleanable artifacts:")
        for path in removed:
            print(f"- {relative_display_path(root, path)}")
    if failed:
        print("Failed to remove cleanable artifacts:", file=sys.stderr)
        for path in failed:
            print(f"- {relative_display_path(root, path)}", file=sys.stderr)
        return 1
    return 0


def update_repository_url() -> str:
    return os.environ.get("WILY_UPDATE_REPOSITORY_URL", DEFAULT_UPDATE_REPOSITORY)


def normalize_repository_url(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.rstrip("/")


def plugin_version(root: Path) -> str:
    manifest = root / ".codex-plugin" / "plugin.json"
    try:
        loaded = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(loaded.get("version") or "unknown")


def git_run(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_stdout(root: Path, args: list[str]) -> str | None:
    result = git_run(root, args)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_install_root(root: Path) -> Path | None:
    detected = git_stdout(root, ["rev-parse", "--show-toplevel"])
    if not detected:
        return None
    return Path(detected).resolve()


def git_changed_paths(root: Path) -> list[str]:
    result = git_run(root, ["status", "--porcelain", "--untracked-files=all"])
    if result.returncode != 0:
        return ["<unable to read git status>"]
    paths = []
    for line in result.stdout.splitlines():
        value = line[3:].strip()
        if value:
            paths.append(value)
    return paths


def current_git_branch(root: Path) -> str | None:
    branch = git_stdout(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if not branch or branch == "HEAD":
        return None
    return branch


def git_commit(root: Path, ref: str) -> str | None:
    return git_stdout(root, ["rev-parse", "--short", ref])


def print_update_header(root: Path) -> None:
    print(f"Current version: {plugin_version(root)}")


def command_update_migrate(root: Path) -> int:
    print_update_header(root)
    if git_install_root(root):
        print("Install type: git")
        print("This install is already git-managed. Use ./wily update --check or ./wily update --yes.")
        return 0

    print("Install type: zip")
    target = root.parent / "wily-roadmap-managed"
    if target.exists():
        print(f"Managed install already exists: {target}", file=sys.stderr)
        return 1

    repository = update_repository_url()
    command = ["git", "clone", repository, str(target)]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        print(f"Migration failed while running: {format_shell_command(command)}", file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    print(f"Managed install created: {target}")
    print("Original zip install left unchanged.")
    print("Use the managed install for future updates.")
    return 0


def command_update(root: Path, args: list[str]) -> int:
    install_root = plugin_root()
    check_only = "--check" in args
    migrate = "--migrate" in args
    yes = "--yes" in args

    if migrate:
        return command_update_migrate(install_root)

    print_update_header(install_root)
    git_root = git_install_root(install_root)
    if not git_root:
        print("Install type: zip")
        print("This install was copied from a zip, so Wily cannot pull updates in place.")
        print("Run ./wily update --migrate to create a git-managed install next to this directory.")
        return 0

    print("Install type: git")
    if git_root != install_root.resolve():
        print(f"Plugin root: {install_root}")
        print(f"Git root: {git_root}")

    changed = git_changed_paths(git_root)
    if changed:
        print("Working tree has local changes.")
        for path in changed[:12]:
            print(f"- {path}")
        if len(changed) > 12:
            print(f"- ... {len(changed) - 12} more")
        print("Commit, stash, or use a fresh managed clone before updating.")
        return 1

    expected = update_repository_url()
    remote = git_stdout(git_root, ["config", "--get", "remote.origin.url"])
    if not remote:
        print("No origin remote configured for this managed install.", file=sys.stderr)
        return 1
    if normalize_repository_url(remote) != normalize_repository_url(expected):
        print("Unexpected origin remote.")
        print(f"Expected: {expected}")
        print(f"Detected: {remote}")
        if not yes:
            print("Re-run with --yes only if you trust this remote.")
            return 1

    branch = current_git_branch(git_root)
    if not branch:
        print("Cannot update while HEAD is detached.", file=sys.stderr)
        return 1

    print(f"Local commit: {git_commit(git_root, 'HEAD') or 'unknown'}")
    print("Fetching origin...")
    fetch = git_run(git_root, ["fetch", "origin", branch])
    if fetch.returncode != 0:
        print("Fetch failed.", file=sys.stderr)
        if fetch.stderr.strip():
            print(fetch.stderr.strip(), file=sys.stderr)
        return fetch.returncode

    remote_ref = f"origin/{branch}"
    remote_commit = git_commit(git_root, remote_ref)
    if not remote_commit:
        print(f"Remote branch not found: {remote_ref}", file=sys.stderr)
        return 1
    print(f"Remote commit: {remote_commit}")

    local_full = git_stdout(git_root, ["rev-parse", "HEAD"])
    remote_full = git_stdout(git_root, ["rev-parse", remote_ref])
    if local_full == remote_full:
        print("Already current.")
        return 0

    log = git_run(git_root, ["log", "--oneline", f"HEAD..{remote_ref}"])
    if log.returncode == 0 and log.stdout.strip():
        print("Pending commits:")
        for line in log.stdout.splitlines()[:10]:
            print(f"- {line}")

    if check_only:
        print("Update available. Run ./wily update --yes to apply a fast-forward update.")
        return 0

    if not yes:
        print("Update available. Re-run with --yes to apply a fast-forward update.")
        return 1

    pull = git_run(git_root, ["pull", "--ff-only", "origin", branch])
    if pull.returncode != 0:
        print("Fast-forward update failed.", file=sys.stderr)
        if pull.stderr.strip():
            print(pull.stderr.strip(), file=sys.stderr)
        return pull.returncode
    print(f"Updated version: {plugin_version(install_root)}")
    print("Update complete.")
    return 0


def usage() -> str:
    return "\n".join(
        [
            "Usage: wily.py <command> [args]",
            "",
            "Commands:",
            "  init [goal]",
            "  status",
            "  next",
            "  start <stage-id>/<phase-id>",
            "  complete <stage-id>/<phase-id>",
            "  block <stage-id>/<phase-id> [reason]",
            "  release <stage-id>/<phase-id>",
            "  live-heartbeat <stage-id>/<phase-id> [--interval seconds] [--count n] [--note text]",
            "  live-worked [<stage-id>/<phase-id>|item-id] [--session id] [--agent name] [--from-hook]",
            "  checkpoint-sync <stage-id>/<phase-id> [--status-board path]",
            "  board check [--hooks-path file] [--probe]",
            "  board sync-local <stage-id>",
            "  hooks install --target codex|claude",
            "  codex-bridge --session id [--fixture jsonl]",
            "  retry <stage-id>/<phase-id>",
            "  replan [reason]",
            "  issues [--add-to-roadmap]",
            "  decompose-stage <stage-id> [--dry-run|--from-json <path>|--apply-fixture]",
            "  migrate-state --to wily-roadmap-v2 (--dry-run|--apply|--prune-legacy)",
            "  run <stage-id>/<phase-id> [--runner <id>] [--autonomy <mode>] [--dry-run]",
            "  land <stage-id>/<phase-id> [--base branch] [--direct|--pr]",
            "  clean [--yes]",
            "  update [--check|--migrate|--yes]",
            "  watch",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if not argv:
        print(usage(), file=sys.stderr)
        return 2

    command, *args = argv
    if command == "init":
        return command_init(root, args)
    if command == "status":
        return command_status(root)
    if command == "next":
        return command_next(root)
    if command == "start":
        return command_start(root, args)
    if command == "complete":
        return command_complete(root, args)
    if command == "block":
        return command_block(root, args)
    if command == "release":
        return command_release(root, args)
    if command == "live-heartbeat":
        return command_live_heartbeat(root, args)
    if command == "live-worked":
        return command_live_worked(root, args)
    if command == "checkpoint-sync":
        return command_checkpoint_sync(root, args)
    if command == "board":
        return command_board(root, args)
    if command == "hooks":
        return command_hooks(root, args)
    if command == "codex-bridge":
        return command_codex_bridge(root, args)
    if command == "retry":
        return command_start(root, args, retry=True)
    if command == "replan":
        return command_replan(root, args)
    if command == "issues":
        return command_issues(root, args)
    if command == "decompose-stage":
        return command_decompose_stage(root, args)
    if command == "migrate-state":
        return command_migrate_state(root, args)
    if command == "run":
        return command_run(root, args)
    if command == "land":
        return command_land(root, args)
    if command == "clean":
        return command_clean(root, args)
    if command == "update":
        return command_update(root, args)
    if command == "watch":
        return command_watch(root, args)

    print(f"Unknown command: {command}", file=sys.stderr)
    print(usage(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
