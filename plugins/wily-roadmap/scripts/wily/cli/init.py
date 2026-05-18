"""`wily init` - interview-driven bootstrap and brownfield adoption."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from ..analysis import analyze_repo
from ..config import save_actors, save_tasks
from ..interview import (
    Draft,
    add_task_candidate,
    assign_task_candidate,
    discard_draft,
    drop_task_candidate,
    load_or_init_draft,
    pop_last_answer,
    record_answer,
    revise_answer,
    revise_task_candidate,
    save_draft,
)
from ..models import Actor, Task
from ..paths import WilyPaths, WilyRootNotFound, find_wily_root
from ..questions import next_question, question_text, ready_for_tasks
from ..transitions import DependencyError, check_dependencies
from . import _common


def main(args: list[str]) -> int:
    explicit_mode = "greenfield" if "--new" in args else "brownfield" if "--adopt" in args else None
    args = [arg for arg in args if arg not in {"--new", "--adopt"}]
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound:
        root = Path.cwd()
        (root / ".wily").mkdir(parents=True, exist_ok=True)
    paths = WilyPaths(root)
    if not args:
        return _start(paths, root, explicit_mode)
    sub, rest = args[0], args[1:]
    if sub == "answer":
        return _answer(paths, root, rest)
    if sub == "back":
        return _back(paths, root)
    if sub == "revise":
        return _revise(paths, rest)
    if sub == "show":
        return _show(paths)
    if sub == "suggest":
        return _suggest(paths)
    if sub == "add-task":
        return _add_task(paths, rest)
    if sub == "revise-task":
        return _revise_task(paths, rest)
    if sub == "drop-task":
        return _drop_task(paths, rest)
    if sub == "assign":
        return _assign(paths, rest)
    if sub == "commit":
        return _commit(paths, root)
    if sub == "cancel":
        return _cancel(paths)
    if sub == "adopt-legacy":
        return _adopt_legacy(paths)
    _common.emit_error(f"unknown init subcommand: {sub}")
    return _common.EXIT_USAGE


def _mode(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    snapshot = analyze_repo(root)
    return "brownfield" if snapshot.commit_count or snapshot.readme_excerpt else "greenfield"


def _start(paths: WilyPaths, root: Path, explicit_mode: str | None) -> int:
    if paths.init_draft.exists():
        draft = load_or_init_draft(paths, mode="greenfield")
    else:
        draft = load_or_init_draft(paths, mode=_mode(root, explicit_mode))
        if draft.mode == "brownfield":
            snapshot = analyze_repo(root)
            draft.answers["_analysis"] = yaml.safe_dump(
                {
                    "commit_count": snapshot.commit_count,
                    "authors": snapshot.authors,
                    "top_level_files": snapshot.top_level_files,
                    "readme_excerpt": snapshot.readme_excerpt,
                    "legacy_wily_detected": snapshot.legacy_wily_detected,
                },
                sort_keys=False,
                allow_unicode=True,
            )
        save_draft(paths, draft)
        _common.emit_text(f"wily init started (mode: {draft.mode})")
    return _question(paths, draft)


def _question(paths: WilyPaths, draft: Draft) -> int:
    if draft.mode == "brownfield" and "analysis_confirm" not in draft.answers:
        _common.emit_text("=== 자동 분석 결과 ===")
        _common.emit_text(draft.answers.get("_analysis", ""))
    key = next_question(draft)
    if key is None:
        _common.emit_text("모든 질문이 끝났음. `wily init suggest` 또는 `wily init commit`.")
        return _common.EXIT_OK
    _common.emit_text(f"[{key}] {question_text(key)}")
    return _common.EXIT_OK


def _answer(paths: WilyPaths, root: Path, args: list[str]) -> int:
    text = " ".join(arg for arg in args if arg != "--multi").strip()
    if "--multi" in args:
        import sys

        text = sys.stdin.read().rstrip("\n")
    if not text:
        _common.emit_error("usage: wily init answer <text>")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    key = next_question(draft)
    if key is None:
        _common.emit_error("no current question")
        return _common.EXIT_USAGE
    record_answer(draft, key=key, text=text)
    save_draft(paths, draft)
    _common.emit_text(f"saved {key}.")
    return _question(paths, draft)


def _back(paths: WilyPaths, root: Path) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    popped = pop_last_answer(draft)
    save_draft(paths, draft)
    _common.emit_text(f"removed last answer: {popped}" if popped else "nothing to roll back")
    return _question(paths, draft)


def _revise(paths: WilyPaths, args: list[str]) -> int:
    if len(args) < 2:
        _common.emit_error("usage: wily init revise <key> <text>")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    try:
        revise_answer(draft, key=args[0], text=" ".join(args[1:]))
    except KeyError:
        _common.emit_error(f"no prior answer for {args[0]}")
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"revised {args[0]}.")
    return _common.EXIT_OK


def _show(paths: WilyPaths) -> int:
    if not paths.init_draft.exists():
        _common.emit_text("(no draft in progress)")
        return _common.EXIT_OK
    draft = load_or_init_draft(paths, mode="greenfield")
    _common.emit_text(f"mode: {draft.mode}")
    for key in draft.history:
        _common.emit_text(f"  {key}: {draft.answers[key]}")
    if draft.task_candidates:
        _common.emit_text("task candidates:")
        for task in draft.task_candidates:
            _common.emit_text(f"  {task['id']} {task['title']!r} assignee={task.get('assignee') or '-'}")
    return _common.EXIT_OK


def _suggest(paths: WilyPaths) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    if not ready_for_tasks(draft):
        _common.emit_error(f"missing answer: {next_question(draft)}")
        return _common.EXIT_FAILURE
    if not draft.task_candidates:
        _common.emit_text("no task candidates yet; use `wily init add-task`")
    for task in draft.task_candidates:
        _common.emit_text(f"{task['id']} {task['title']!r}")
    return _common.EXIT_OK


def _add_task(paths: WilyPaths, args: list[str]) -> int:
    title = " ".join(args).strip()
    if not title:
        _common.emit_error("usage: wily init add-task <title>")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    task_id = add_task_candidate(draft, title=title)
    save_draft(paths, draft)
    _common.emit_text(f"added {task_id}: {title!r}")
    return _common.EXIT_OK


def _revise_task(paths: WilyPaths, args: list[str]) -> int:
    if len(args) < 3:
        _common.emit_error("usage: wily init revise-task <id> <field> <value>")
        return _common.EXIT_USAGE
    task_id, field, raw = args[0], args[1], " ".join(args[2:])
    value: Any = [item.strip() for item in raw.split(",") if item.strip()] if field in {"scope", "depends_on"} else raw
    draft = load_or_init_draft(paths, mode="greenfield")
    try:
        revise_task_candidate(draft, task_id, field, value)
    except KeyError:
        _common.emit_error(f"task candidate not found: {task_id}")
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"{task_id}.{field} updated")
    return _common.EXIT_OK


def _drop_task(paths: WilyPaths, args: list[str]) -> int:
    if len(args) != 1:
        _common.emit_error("usage: wily init drop-task <id>")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    drop_task_candidate(draft, args[0])
    save_draft(paths, draft)
    _common.emit_text(f"dropped {args[0]}")
    return _common.EXIT_OK


def _assign(paths: WilyPaths, args: list[str]) -> int:
    if len(args) != 2:
        _common.emit_error("usage: wily init assign <id> <actor>")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    try:
        assign_task_candidate(draft, args[0], args[1])
    except KeyError:
        _common.emit_error(f"task candidate not found: {args[0]}")
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"{args[0]}.assignee = {args[1]}")
    return _common.EXIT_OK


def _commit(paths: WilyPaths, root: Path) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    if not ready_for_tasks(draft):
        _common.emit_error(f"missing answer: {next_question(draft)}")
        return _common.EXIT_FAILURE
    tasks = [Task.from_dict(item) for item in draft.task_candidates]
    try:
        check_dependencies(tasks)
    except DependencyError as exc:
        _common.emit_error(f"dependency check failed: {exc}")
        return _common.EXIT_FAILURE
    actors = _parse_actors(draft.answers.get("actors_setup", ""))
    title = (
        draft.answers.get("purpose")
        or draft.answers.get("purpose_revise")
        or "Wily Roadmap"
    ).splitlines()[0]
    save_tasks(paths, title, tasks)
    save_actors(paths, actors)
    _write_project(paths, draft)
    _write_agent_instruction_files(root)
    discard_draft(paths)
    _common.emit_text(f"init committed: {len(tasks)} task(s), {len(actors)} actor(s)")
    _common.emit_text("agent instructions updated: AGENTS.md, CLAUDE.md")
    return _common.EXIT_OK


def _cancel(paths: WilyPaths) -> int:
    discard_draft(paths)
    _common.emit_text("init draft discarded")
    return _common.EXIT_OK


def _adopt_legacy(paths: WilyPaths) -> int:
    if not (paths.wily_dir / "roadmap.yaml").exists():
        _common.emit_error("no legacy roadmap.yaml found in .wily/")
        return _common.EXIT_FAILURE
    paths.archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    dest = paths.archive_dir / f"legacy-{stamp}"
    index = 2
    while dest.exists():
        dest = paths.archive_dir / f"legacy-{stamp}-{index}"
        index += 1
    dest.mkdir(parents=True)
    for child in list(paths.wily_dir.iterdir()):
        if child.name in {"archive", "init"}:
            continue
        shutil.move(str(child), str(dest / child.name))
    _common.emit_text(f"legacy .wily/ archived to {dest.relative_to(paths.root)}")
    return _common.EXIT_OK


def _parse_actors(text: str) -> list[Actor]:
    actors: list[Actor] = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        emails: list[str] = []
        names: list[str] = []
        if "emails=" in chunk:
            chunk, _, email_part = chunk.partition("emails=")
            emails = [item.strip() for item in email_part.split(",") if item.strip()]
            chunk = chunk.rstrip(" ,")
        if "names=" in chunk:
            chunk, _, name_part = chunk.partition("names=")
            names = [item.strip() for item in name_part.split(",") if item.strip()]
            chunk = chunk.rstrip(" ,")
        parts = chunk.split(None, 1)
        if parts:
            actor_id = parts[0]
            actors.append(Actor(id=actor_id, display=parts[1] if len(parts) > 1 else actor_id, git_author_emails=emails, git_author_names=names))
    return actors or [Actor(id="wily", display="Wily")]


def _write_project(paths: WilyPaths, draft: Draft) -> None:
    title = draft.answers.get("purpose") or draft.answers.get("purpose_revise") or "Wily Roadmap"
    lines = [f"# {title}", ""]
    labels = {
        "users": "Users / Stakeholders",
        "success": "Success Conditions",
        "non_goals": "Non-goals / Constraints",
        "purpose_revise": "Brownfield Notes",
    }
    for key, label in labels.items():
        if draft.answers.get(key):
            lines.extend([f"## {label}", draft.answers[key], ""])
    paths.project_md.write_text("\n".join(lines), encoding="utf-8")


AGENT_INSTRUCTION_SECTIONS = """## Wily Roadmap

- Treat `.wily/` as the local project/task ledger.
- Prefer `wily next`, `wily claim <id>`, `wily go <id>`, `wily done <id>`, and `wily watch` for Wily-managed work.
- When using Custom Workflow, sync checkpoint status back with `wily cp <id> import-status agent-handoffs/<slug>-status.md`.
- Keep remote or destructive actions approval-first.

## Agent Behavior

- State assumptions when requirements are ambiguous.
- Choose the simplest implementation that satisfies the task.
- Keep edits surgical; do not refactor unrelated code.
- Define success with tests or concrete verification before calling work done.
"""


def _write_agent_instruction_files(root: Path) -> None:
    for name in ("AGENTS.md", "CLAUDE.md"):
        _upsert_agent_instruction_sections(root / name)


def _upsert_agent_instruction_sections(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    cleaned = _remove_markdown_section(existing, "Wily Roadmap")
    cleaned = _remove_markdown_section(cleaned, "Agent Behavior").strip()
    parts = [part for part in (cleaned, AGENT_INSTRUCTION_SECTIONS.strip()) if part]
    path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def _remove_markdown_section(text: str, title: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    index = 0
    target = f"## {title}"
    while index < len(lines):
        if lines[index].strip() == target:
            index += 1
            while index < len(lines) and not lines[index].startswith("## "):
                index += 1
            continue
        output.append(lines[index])
        index += 1
    return "\n".join(output)
