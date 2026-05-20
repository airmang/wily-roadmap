"""`wily land <id>` - commit local task changes with a Wily trailer."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

from ..config import load_tasks
from ..models import TaskStatus
from ..paths import WilyPaths, WilyRootNotFound, find_wily_root
from . import _common

DESCRIPTION = "commit local task changes with a Wily trailer"
USAGE = "usage: wily land <task-id> [--push|--no-push] [--force] [--include-ledger-closure]"
HELP = "\n".join(
    [
        "Options:",
        "  --push                    push after committing",
        "  --no-push                 skip push after committing",
        "  --force                   include out-of-scope files or land before done",
        "  --include-ledger-closure  include Wily ledger closure files outside task scope",
    ]
)


def main(args: list[str]) -> int:
    force = "--force" in args
    include_ledger_closure = "--include-ledger-closure" in args
    push = "--push" in args
    no_push = "--no-push" in args
    if push and no_push:
        _common.emit_error("choose only one of --push or --no-push")
        return _common.EXIT_USAGE
    positional = [arg for arg in args if not arg.startswith("--")]
    if len(positional) != 1:
        _common.emit_error(USAGE)
        return _common.EXIT_USAGE
    task_id = positional[0]
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    _, tasks = load_tasks(paths)
    task = next((item for item in tasks if item.id == task_id), None)
    if task is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    if task.status != TaskStatus.DONE and not force:
        _common.emit_error(f"{task_id} is {task.status.value}; run wily done first")
        return _common.EXIT_TRANSITION
    changed = _changed(root)
    if not changed:
        _common.emit_error("nothing to commit")
        return _common.EXIT_FAILURE
    in_scope, out_scope = _split(changed, task.scope)
    ledger_out_scope = [file for file in out_scope if _is_ledger_closure_file(file)]
    ordinary_out_scope = [file for file in out_scope if file not in ledger_out_scope]
    if ledger_out_scope and not force and not include_ledger_closure:
        _common.emit_error("ledger closure changes detected outside task scope:")
        for file in ledger_out_scope:
            _common.emit_error(f"  {file}")
        _common.emit_error("rerun with --include-ledger-closure to commit Wily ledger metadata with this task")
        return _common.EXIT_TRANSITION
    files = changed if force or not out_scope else _dedupe(in_scope + ledger_out_scope)
    if out_scope and not force:
        if ordinary_out_scope:
            _common.emit_text(f"warning: {len(ordinary_out_scope)} file(s) outside scope; use --force to include")
        if ledger_out_scope and include_ledger_closure:
            _common.emit_text(f"including {len(ledger_out_scope)} Wily ledger closure file(s)")
    if not files:
        _common.emit_error("no in-scope files to commit")
        return _common.EXIT_FAILURE
    subprocess.run(["git", "add", *files], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", _message(paths, task.id, task.title, pre_done=task.status != TaskStatus.DONE)], cwd=root, check=True)
    _common.emit_text(f"committed: {task.id}: {task.title}")
    if no_push or not push:
        _common.emit_text("(push skipped: --no-push)")
        return _common.EXIT_OK
    return _common.EXIT_OK if _do_push(root) else _common.EXIT_FAILURE


def _changed(root: Path) -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain=v2"], cwd=root, capture_output=True, text=True, check=True).stdout
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip() or line.startswith("? "):
            if line.startswith("? "):
                files.extend(_expand_untracked(root, line[2:]))
            continue
        parts = line.split("\t")
        head = parts[0].split()
        if line.startswith("1 ") and len(head) >= 9:
            files.append(" ".join(head[8:]))
        elif line.startswith("2 ") and len(parts) >= 2:
            files.append(parts[0].split()[-1])
    return files


def _expand_untracked(root: Path, path: str) -> list[str]:
    full_path = root / path
    if not full_path.is_dir():
        return [path]
    return [item.relative_to(root).as_posix() for item in sorted(full_path.rglob("*")) if item.is_file()]


def _split(files: list[str], scope: list[str]) -> tuple[list[str], list[str]]:
    if not scope:
        return files, []
    inside = [file for file in files if any(fnmatch.fnmatch(file, pattern) for pattern in scope)]
    outside = [file for file in files if file not in inside]
    return inside, outside


def _is_ledger_closure_file(file: str) -> bool:
    if file == ".wily/tasks.yaml":
        return True
    if not file.startswith(".wily/tasks/"):
        return False
    return file.endswith("/result.md") or file.endswith("/progress.jsonl")


def _dedupe(files: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for file in files:
        if file in seen:
            continue
        result.append(file)
        seen.add(file)
    return result


def _message(paths: WilyPaths, task_id: str, title: str, *, pre_done: bool = False) -> str:
    body = ""
    result = paths.result_md(task_id)
    if result.exists():
        bullets = [line for line in result.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
        body = "\n".join(bullets[:6])
    pre_done_line = "Wily-Pre-Done: true\n" if pre_done else ""
    return f"{task_id}: {title}\n\n{body}\n\nWily-Task: {task_id}\n{pre_done_line}"


def _do_push(root: Path) -> bool:
    return subprocess.run(["git", "push"], cwd=root, check=False).returncode == 0
