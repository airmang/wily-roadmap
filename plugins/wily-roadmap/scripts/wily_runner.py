#!/usr/bin/env python3
"""Prepare Wily phases for external workflow execution without bundling a runner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import wily
import wily_state_summary


Phase = dict[str, Any]
ALLOWED_AUTONOMY_MODES = {"conservative", "goal_scoped", "yolo"}


def parse_args(args: list[str]) -> tuple[str | None, str, str, str | None]:
    phase_id: str | None = None
    workflow = "external"
    autonomy_mode = "goal_scoped"
    error: str | None = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--runner":
            try:
                workflow = args[index + 1]
            except IndexError:
                error = "Missing value for --runner"
                break
            index += 2
            continue
        if arg == "--autonomy":
            try:
                autonomy_mode = args[index + 1]
            except IndexError:
                error = "Missing value for --autonomy"
                break
            index += 2
            continue
        if arg.startswith("--"):
            error = f"Unknown option: {arg}"
            break
        if phase_id is None:
            phase_id = arg
        else:
            error = f"Unexpected argument: {arg}"
            break
        index += 1
    return phase_id, workflow, autonomy_mode, error


def validate_autonomy(autonomy_mode: str) -> str | None:
    if autonomy_mode not in ALLOWED_AUTONOMY_MODES:
        return f"Unsupported autonomy mode: {autonomy_mode}"
    return None


def phase_executable(phase: Phase, phases: list[Phase]) -> bool:
    status = str(phase.get("status") or "pending")
    if status in {"ready", "in_progress"}:
        return True
    return status == "pending" and wily_state_summary.dependencies_done(phase, phases)


def ensure_session(root: Path, phase: Phase, roadmap: dict[str, Any]) -> Path:
    session = wily.current_session_path(root, phase)
    if str(phase.get("status")) == "in_progress" and session is not None and session.exists():
        return session

    phase_id = str(phase.get("id", "unknown"))
    attempt = wily.next_attempt(root, phase_id)
    session = wily.create_session(root, phase, attempt)
    phase["status"] = "in_progress"
    phase["current_session"] = wily.relative_session_path(root, session)
    phase.pop("blocker", None)
    wily.save_roadmap(root, roadmap)
    return session


def slugify_phase(phase: Phase) -> str:
    phase_id = str(phase.get("id", "phase"))
    title = str(phase.get("title", "phase"))
    return f"{wily.phase_slug(phase_id)}-{wily.slugify_title(title)}"


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def native_goal_command(phase: Phase, workflow: str, autonomy_mode: str, handoff_path: Path, root: Path) -> str:
    phase_id = str(phase.get("id", "unknown"))
    title = str(phase.get("title", "Untitled phase"))
    handoff_ref = relative_to_root(root, handoff_path)
    return (
        f"/goal Execute Wily phase {phase_id}: {title}. "
        f"Use external workflow {workflow} with {autonomy_mode} autonomy. "
        f"Read {handoff_ref}. Do not mark the Wily phase done; "
        "record verification evidence and finish with a recommended Wily status."
    )


def render_handoff(phase: Phase, workflow: str, autonomy_mode: str, session: Path, root: Path) -> str:
    phase_id = str(phase.get("id", "unknown"))
    title = str(phase.get("title", "Untitled phase"))
    phase_folder = root / ".wily" / str(phase.get("path"))
    phase_context, _planner = wily.phase_context_bundle(phase_id, title, phase_folder)
    return "\n".join(
        [
            "# Wily External Workflow Handoff",
            "",
            f"- Phase ID: `{phase_id}`",
            f"- Phase title: `{title}`",
            f"- External workflow: `{workflow}`",
            f"- Autonomy mode: `{autonomy_mode}`",
            f"- Wily session: `{relative_to_root(root, session)}`",
            f"- Git status: `{wily_state_summary.git_status(root)}`",
            "",
            "## Contract",
            "",
            "- This handoff is reference-only.",
            "- Wily does not bundle or execute the external workflow.",
            "- Do not mark the Wily phase done from the external workflow.",
            "- After verification evidence exists, complete the phase with `python3 scripts/wily.py complete <phase-id>`.",
            '- If blocked, use `python3 scripts/wily.py block <phase-id> "<reason>"`.',
            "",
            "## Phase Context",
            "",
            phase_context.strip(),
            "",
        ]
    )


def write_external_handoff(
    root: Path,
    phase: Phase,
    workflow: str,
    autonomy_mode: str,
    session: Path,
) -> dict[str, Path]:
    handoffs_dir = root / "agent-handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify_phase(phase)
    external_handoff = handoffs_dir / f"{slug}-external-workflow.md"
    session_handoff = session / "external-workflow-handoff.md"
    handoff_text = render_handoff(phase, workflow, autonomy_mode, session, root)
    external_handoff.write_text(handoff_text, encoding="utf-8")
    session_handoff.write_text(handoff_text, encoding="utf-8")
    return {
        "session": session,
        "external_handoff": external_handoff,
        "session_handoff": session_handoff,
    }


def snapshot_runner_artifacts(root: Path, phase: Phase, recommended_status: str) -> None:
    return None


def command_run(root: Path, args: list[str]) -> int:
    phase_id, workflow, autonomy_mode, error = parse_args(args)
    if error:
        print(error, file=sys.stderr)
        return 2
    if not phase_id:
        print(
            "Usage: wily.py run <phase-id> [--runner <external-workflow-id>] "
            "[--autonomy conservative|goal_scoped|yolo]",
            file=sys.stderr,
        )
        return 2

    autonomy_error = validate_autonomy(autonomy_mode)
    if autonomy_error:
        print(autonomy_error, file=sys.stderr)
        return 2

    roadmap = wily.load_roadmap(root)
    phases = roadmap.get("phases") or []
    phase = wily.find_phase(roadmap, phase_id)
    if phase is None:
        print(f"Phase not found: {phase_id}", file=sys.stderr)
        return 1
    if not phase_executable(phase, phases):
        print(f"Phase is not executable: {phase_id}", file=sys.stderr)
        return 1

    session = ensure_session(root, phase, roadmap)
    artifacts = write_external_handoff(root, phase, workflow, autonomy_mode, session)
    goal_command = native_goal_command(phase, workflow, autonomy_mode, artifacts["external_handoff"], root)

    print(f"Prepared phase {phase_id} for external workflow")
    print(f"Workflow: {workflow}")
    print(f"Autonomy: {autonomy_mode}")
    print(f"Session: {session}")
    print(f"Reference-only handoff: {artifacts['external_handoff']}")
    print("Native goal command:")
    print(goal_command)
    return 0


def main(argv: list[str] | None = None) -> int:
    return command_run(Path.cwd(), list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
