#!/usr/bin/env python3
"""Local Wily roadmap helper."""

from __future__ import annotations

import json
import os
import re
import select
import shlex
import shutil
import subprocess
import sys
import termios
import time
import tty
from datetime import datetime
from pathlib import Path
from typing import Any

import wily_state_summary
import wily_watch_ui


Phase = dict[str, Any]
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


def state_dir(root: Path) -> Path:
    return root / ".wily"


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
                "phases: []",
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
    for name in ("phases", "sessions", "revisions"):
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


def ready_phase(roadmap: dict[str, Any]) -> Phase | None:
    phases = roadmap.get("phases") or []
    ready = wily_state_summary.executable_phases(phases)
    return ready[0] if ready else None


def command_next(root: Path) -> int:
    roadmap = load_roadmap(root)
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
        if key == "phases":
            continue
        lines.extend(serialize_mapping_entry("", key, value))

    phases = roadmap.get("phases") or []
    if not phases:
        lines.append("phases: []")
        return "\n".join(lines) + "\n"

    lines.append("phases:")
    for phase in phases:
        first = True
        for key, value in phase.items():
            prefix = "  - " if first else "    "
            lines.extend(serialize_mapping_entry(prefix, key, value))
            first = False
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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
    print(f"Usage: wily.py {command} <phase-id>", file=sys.stderr)
    return None


def command_start(root: Path, args: list[str], *, retry: bool = False) -> int:
    phase_id = require_phase_id(args, "retry" if retry else "start")
    if not phase_id:
        return 2
    roadmap = load_roadmap(root)
    phase = find_phase(roadmap, phase_id)
    if not phase:
        print(f"Phase not found: {phase_id}", file=sys.stderr)
        return 1

    attempt = next_attempt(root, phase_id)
    session = create_session(root, phase, attempt)
    phase["status"] = "in_progress"
    phase["current_session"] = relative_session_path(root, session)
    if "blocker" in phase:
        del phase["blocker"]
    save_roadmap(root, roadmap)

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
        print(f"Phase not found: {phase_id}", file=sys.stderr)
        return 1
    phase["status"] = "done"
    phase.pop("blocker", None)
    update_session_status(root, phase, "verified")
    snapshot_runner_session(root, phase, "done")
    save_roadmap(root, roadmap)
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
        print(f"Phase not found: {phase_id}", file=sys.stderr)
        return 1
    phase["status"] = "blocked"
    phase["blocker"] = reason
    update_session_status(root, phase, "blocked", reason)
    snapshot_runner_session(root, phase, "blocked")
    save_roadmap(root, roadmap)
    print(f"Blocked phase {phase_id}: {reason}")
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
            "  start <phase-id>",
            "  complete <phase-id>",
            "  block <phase-id> [reason]",
            "  retry <phase-id>",
            "  replan [reason]",
            "  issues [--add-to-roadmap]",
            "  run <phase-id> [--runner <id>] [--autonomy <mode>]",
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
    if command == "retry":
        return command_start(root, args, retry=True)
    if command == "replan":
        return command_replan(root, args)
    if command == "issues":
        return command_issues(root, args)
    if command == "run":
        return command_run(root, args)
    if command == "update":
        return command_update(root, args)
    if command == "watch":
        return command_watch(root, args)

    print(f"Unknown command: {command}", file=sys.stderr)
    print(usage(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
