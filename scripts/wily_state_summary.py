#!/usr/bin/env python3
"""Summarize Wily roadmap state for Codex."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


Phase = dict[str, Any]

STATUS_LABELS = {
    "pending": "대기",
    "ready": "준비됨",
    "in_progress": "진행 중",
    "needs_review": "검토 필요",
    "done": "완료",
    "blocked": "차단",
    "superseded": "대체됨",
}


def repo_root(start: Path) -> Path:
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return start.resolve()
        current = current.parent


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def git_status(root: Path) -> str:
    if not (root / ".git").exists():
        return "not a git repo"

    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return f"unavailable: {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return f"error: {detail}" if detail else "error"
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return f"{len(lines)} changed file(s)"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def parse_key_value(line: str) -> tuple[str, Any] | None:
    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    return key.strip(), parse_scalar(value.strip())


def parse_roadmap(content: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    phases: list[Phase] = []
    current_phase: Phase | None = None
    in_phases = False

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.strip().startswith("#"):
            continue

        if line == "phases:":
            in_phases = True
            data["phases"] = phases
            continue

        if not in_phases:
            parsed = parse_key_value(line)
            if parsed:
                key, value = parsed
                data[key] = value
            continue

        stripped = line.strip()
        if stripped.startswith("- "):
            current_phase = {}
            phases.append(current_phase)
            parsed = parse_key_value(stripped[2:])
            if parsed:
                key, value = parsed
                current_phase[key] = value
            continue

        if current_phase is not None:
            parsed = parse_key_value(stripped)
            if parsed:
                key, value = parsed
                current_phase[key] = value

    data.setdefault("phases", phases)
    return data


def phase_label(phase: Phase) -> str:
    return f"{phase.get('id', 'unknown')} {phase.get('title', 'Untitled phase')}"


def dependency_label(phase: Phase) -> str:
    depends_on = phase.get("depends_on") or []
    if not depends_on:
        return "의존: 없음"
    return f"의존: {', '.join(str(value) for value in depends_on)}"


def parallel_label(phase: Phase) -> str:
    parallel_group = phase.get("parallel_group")
    if not parallel_group:
        return "병렬: 없음"
    return f"병렬: {parallel_group}"


def status_label(phase: Phase, ready_ids: set[str]) -> str:
    phase_id = str(phase.get("id"))
    if phase_id in ready_ids:
        return "실행 가능"
    return STATUS_LABELS.get(str(phase.get("status", "unknown")), str(phase.get("status", "unknown")))


def phase_summary_line(phase: Phase, ready_ids: set[str]) -> str:
    phase_id = phase.get("id", "unknown")
    status = status_label(phase, ready_ids)
    title = phase.get("title", "Untitled phase")
    return f"  - {phase_id} [{status}] {title} ({dependency_label(phase)}, {parallel_label(phase)})"


def phase_node_line(phase: Phase, ready_ids: set[str], *, branch: bool = False) -> str:
    phase_id = phase.get("id", "unknown")
    status = status_label(phase, ready_ids)
    title = phase.get("title", "Untitled phase")
    prefix = "  +-->" if branch else " "
    return f"{prefix} [{phase_id} {status}] {title}"


def phase_detail_lines(phase: Phase) -> list[str]:
    lines: list[str] = []
    depends_on = phase.get("depends_on") or []
    if depends_on:
        lines.append(f"    의존: {', '.join(str(value) for value in depends_on)}")
        if len(depends_on) > 1:
            lines.extend(f"    ^-- {dependency}" for dependency in depends_on)
    parallel_group = phase.get("parallel_group")
    if parallel_group:
        lines.append(f"    병렬: {parallel_group}")
    return lines


def phase_index(phases: list[Phase]) -> dict[str, Phase]:
    return {str(phase.get("id")): phase for phase in phases if phase.get("id") is not None}


def dependencies_done(phase: Phase, phases: list[Phase]) -> bool:
    by_id = phase_index(phases)
    for dependency in phase.get("depends_on") or []:
        dependency_phase = by_id.get(str(dependency))
        if not dependency_phase or dependency_phase.get("status") != "done":
            return False
    return True


def is_executable_phase(phase: Phase, phases: list[Phase]) -> bool:
    status = phase.get("status")
    if status == "ready":
        return True
    return status == "pending" and dependencies_done(phase, phases)


def executable_phases(phases: list[Phase]) -> list[Phase]:
    return [phase for phase in phases if is_executable_phase(phase, phases)]


def phase_stage_map(phases: list[Phase]) -> dict[str, int]:
    by_id = phase_index(phases)
    stages: dict[str, int] = {}
    visiting: set[str] = set()

    def stage_for(phase: Phase) -> int:
        phase_id = str(phase.get("id"))
        if phase_id in stages:
            return stages[phase_id]
        if phase_id in visiting:
            return 1

        visiting.add(phase_id)
        dependency_stages = [
            stage_for(by_id[str(dependency)])
            for dependency in phase.get("depends_on") or []
            if str(dependency) in by_id
        ]
        visiting.remove(phase_id)

        stages[phase_id] = max(dependency_stages, default=0) + 1
        return stages[phase_id]

    for phase in phases:
        stage_for(phase)

    return stages


def stage_groups(phases: list[Phase]) -> dict[int, list[Phase]]:
    stages = phase_stage_map(phases)
    grouped: dict[int, list[Phase]] = {}
    for phase in phases:
        phase_id = str(phase.get("id"))
        grouped.setdefault(stages.get(phase_id, 1), []).append(phase)
    return grouped


def phase_flow_lines(phases: list[Phase], ready: list[Phase]) -> list[str]:
    lines = ["Roadmap:"]
    if not phases:
        lines.append("  없음")
        return lines

    ready_ids = {str(phase.get("id")) for phase in ready}
    grouped = stage_groups(phases)
    ordered_stages = sorted(grouped)
    for index, stage in enumerate(ordered_stages):
        lines.append(f"Stage {stage}:")
        stage_phases = grouped[stage]
        branch = len(stage_phases) > 1
        for phase in stage_phases:
            lines.append(phase_node_line(phase, ready_ids, branch=branch))
            lines.extend(phase_detail_lines(phase))
        if index < len(ordered_stages) - 1 and len(stage_phases) == 1:
            lines.append("  |")
    return lines


def status_counts(phases: list[Phase], ready: list[Phase]) -> dict[str, int]:
    statuses = ["done", "ready", "in_progress", "blocked", "superseded"]
    counts = {status: sum(1 for phase in phases if phase.get("status") == status) for status in statuses}
    counts["ready"] = len(ready)
    return counts


def phases_with_status(phases: list[Phase], status: str) -> list[Phase]:
    return [phase for phase in phases if phase.get("status") == status]


def blocked_phase_lines(phase: Phase) -> list[str]:
    lines = [f"  - {phase_label(phase)} ({dependency_label(phase)})"]
    blocker = phase.get("blocker")
    if blocker:
        lines.append(f"    blocker: {blocker}")
    return lines


def summarize_roadmap(root: Path, state_dir: Path, roadmap: dict[str, Any]) -> str:
    phases = roadmap.get("phases") or []
    ready = executable_phases(phases)
    counts = status_counts(phases, ready)
    blocked = phases_with_status(phases, "blocked")
    superseded = phases_with_status(phases, "superseded")
    replacements = [phase for phase in phases if phase.get("replaces")]
    next_phase = ready[0] if ready else None

    lines = [
        f"저장소: {root}",
        f"상태 디렉터리: {state_dir.name}",
        f"Git: {git_status(root)}",
        f"로드맵 버전: {roadmap.get('roadmap_version', 'unknown')}",
    ]

    goal = roadmap.get("goal")
    if goal:
        lines.append(f"목표: {goal}")

    lines.append(
        "진행: "
        f"완료 {counts['done']}, "
        f"실행 가능 {counts['ready']}, "
        f"진행 중 {counts['in_progress']}, "
        f"차단 {counts['blocked']}, "
        f"대체됨 {counts['superseded']}"
    )

    if next_phase:
        lines.append(f"다음 단계: {next_phase.get('id')} - {next_phase.get('title', 'Untitled phase')}")
    else:
        lines.append("다음 단계: 없음")

    lines.extend(phase_flow_lines(phases, ready))

    lines.append("실행 가능 단계:")
    if ready:
        lines.extend(f"  - {phase_label(phase)}" for phase in ready)
    else:
        lines.append("  없음")

    lines.append("차단된 단계:")
    if blocked:
        for phase in blocked:
            lines.extend(blocked_phase_lines(phase))
    else:
        lines.append("  없음")

    if replacements:
        lines.append("대체:")
        for phase in replacements:
            replaced = ", ".join(str(value) for value in phase.get("replaces") or [])
            lines.append(f"  - {phase.get('id')} 대체: {replaced}")

    if superseded:
        lines.append("대체된 단계:")
        lines.extend(f"  - {phase_label(phase)}" for phase in superseded)

    return "\n".join(lines)


def summarize_state(root: Path, state_dir: Path) -> str:
    roadmap_path = state_dir / "roadmap.yaml"
    if not roadmap_path.exists():
        return "\n".join(
            [
                f"저장소: {root}",
                f"상태 디렉터리: {state_dir.name}",
                f"Git: {git_status(root)}",
                "로드맵: 없음",
            ]
        )

    roadmap = parse_roadmap(read_text(roadmap_path))
    return summarize_roadmap(root, state_dir, roadmap)


def main() -> int:
    root = repo_root(Path.cwd())
    state_dir = root / ".wily"
    if state_dir.exists():
        print(summarize_state(root, state_dir))
        return 0

    print(f"저장소: {root}")
    print("상태 디렉터리: 없음")
    print(f"Git: {git_status(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
