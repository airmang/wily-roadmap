"""Resolve `.wily/` roots and compose canonical v3 paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil


class WilyRootNotFound(Exception):
    """Raised when no `.wily/` directory exists at or above a path."""


def find_wily_root(start: Path) -> Path:
    current = start.resolve()
    while True:
        if (current / ".wily").is_dir():
            return current
        if current.parent == current:
            raise WilyRootNotFound(f"no .wily/ directory at or above {start}")
        current = current.parent


@dataclass(frozen=True)
class WilyPaths:
    root: Path

    @property
    def wily_dir(self) -> Path:
        return self.root / ".wily"

    @property
    def tasks_yaml(self) -> Path:
        return self.wily_dir / "tasks.yaml"

    @property
    def actors_yaml(self) -> Path:
        return self.wily_dir / "actors.yaml"

    @property
    def project_md(self) -> Path:
        return self.wily_dir / "project.md"

    @property
    def tasks_dir(self) -> Path:
        return self.wily_dir / "tasks"

    def task_dir(self, task_id: str) -> Path:
        return self.tasks_dir / task_id

    def progress_jsonl(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "progress.jsonl"

    def result_md(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "result.md"

    def acceptance_md(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "acceptance.md"

    @property
    def handoffs_dir(self) -> Path:
        return self.wily_dir / "handoffs"

    def handoff_dir(self, task_id: str) -> Path:
        return self.handoffs_dir / task_id

    def handoff_status_md(self, task_id: str) -> Path:
        return self.handoff_dir(task_id) / "status.md"

    @property
    def touch_file(self) -> Path:
        return self.wily_dir / ".touch"

    @property
    def init_dir(self) -> Path:
        return self.wily_dir / "init"

    @property
    def init_draft(self) -> Path:
        return self.init_dir / "draft.yaml"

    @property
    def replan_draft(self) -> Path:
        return self.init_dir / "replan-draft.yaml"

    @property
    def archive_dir(self) -> Path:
        return self.wily_dir / "archive"


def migrate_legacy_handoffs(paths: WilyPaths) -> int:
    legacy_dir = paths.root / "agent-handoffs"
    if not legacy_dir.is_dir():
        return 0
    copied = 0
    for source in sorted(path for path in legacy_dir.rglob("*") if path.is_file()):
        destination = _legacy_handoff_destination(paths, source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            continue
        shutil.copy2(source, destination)
        copied += 1
    return copied


def touch_wily(paths: WilyPaths) -> None:
    paths.wily_dir.mkdir(parents=True, exist_ok=True)
    paths.touch_file.touch()


def _handoff_task_id(name: str) -> str:
    match = re.search(r"(?i)\bt\d+\b", name)
    if match:
        return match.group(0).upper()
    match = re.match(r"(?i)t(\d+)[-_]", name)
    if match:
        return f"T{match.group(1)}"
    return "legacy"


def _legacy_handoff_destination(paths: WilyPaths, name: str) -> Path:
    task_id = _handoff_task_id(name)
    if task_id == "legacy":
        return paths.handoff_dir("legacy") / name
    if _is_status_handoff(name):
        return paths.handoff_status_md(task_id)
    return paths.handoff_dir(task_id) / name


def _is_status_handoff(name: str) -> bool:
    lower = name.lower()
    return lower == "status.md" or lower.endswith("-status.md")
