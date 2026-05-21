"""`wily done <id>` - mark a task done and write result.md."""

from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from pathlib import Path

from ..config import load_actors, load_tasks, save_tasks
from ..coordination import ProjectContext, nested_repo_exclusions, resolve_project_context
from ..hooks.drift_guard import ensure_drift_stub
from ..observation import changed_files_since_by_actor, head_sha, list_commits_since_fork, match_actor, repo_snapshot
from ..paths import WilyRootNotFound, touch_wily
from ..progress import AcCheck, append_event, cp_summary, read_ac_checks
from ..scope import file_matches_scope, normalize_scope_entries
from ..transitions import TransitionError, apply_done
from . import _common

DESCRIPTION = "mark a task done and write result.md"
USAGE = "usage: wily done <task-id> [--note <text>] [--ac-check <n=pass|fail:note>] [--observed] [--force] [--add-scope|--stub-drift] [--json]"
HELP = "\n".join(
    [
        "Options:",
        "  --note <text>       add a completion note",
        "  --ac-check <value>  record acceptance evidence, e.g. 1=pass or 2=fail:reason",
        "  --observed          infer actor from observed commits",
        "  --force             bypass transition or scope checks",
        "  --add-scope         add detected changed files to task scope",
        "  --stub-drift        create/reuse a drift task for out-of-scope files",
        "  --json              emit the updated task as JSON",
    ]
)


def main(args: list[str]) -> int:
    args, as_json = _common.consume_json_flag(args)
    missing = _common.missing_value_flag(args, {"--note", "--ac-check"})
    if missing:
        _common.emit_error(f"{missing} requires a value")
        return _common.EXIT_USAGE
    force = "--force" in args
    observed = "--observed" in args
    add_scope = "--add-scope" in args
    stub_drift = "--stub-drift" in args
    note = _common.extract_value(args, "--note")
    ac_checks = _common.extract_values(args, "--ac-check")
    positional = _common.positionals(args, value_flags={"--note", "--ac-check"})
    if len(positional) != 1:
        _common.emit_error("usage: wily done <task-id> [--note <text>] [--observed] [--force] [--add-scope|--stub-drift]")
        return _common.EXIT_USAGE
    if add_scope and stub_drift:
        _common.emit_error("choose only one of --add-scope or --stub-drift")
        return _common.EXIT_USAGE
    task_id = positional[0]
    try:
        context = resolve_project_context(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    root = context.paths.root
    paths = context.paths
    project_title, tasks = load_tasks(paths)
    task = next((item for item in tasks if item.id == task_id), None)
    if task is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    current_sha = "?"
    changed: list[str] = []
    if context.active_mode == "coordination" and task.claim_snapshot:
        current_sha = "coordination"
        changed = _coordination_changed_files(context, task.claim_snapshot)
    else:
        try:
            current_sha = head_sha(root)
            if task.claim_sha:
                actor = next((item for item in load_actors(paths) if item.id == task.actor), None)
                changed = changed_files_since_by_actor(root, task.claim_sha, actor=actor)
        except Exception:
            changed = []
    outside_scope = _outside_scope(task.scope, changed, context=context)
    if outside_scope and not force:
        if add_scope:
            task.scope = _extend_scope(task.scope, outside_scope)
        elif stub_drift:
            ensure_drift_stub(root, paths, project_title, tasks, outside_scope)
        else:
            _emit_scope_drift_error(task_id, outside_scope)
            return _common.EXIT_TRANSITION
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        updated = apply_done(task, at=now, force=force)
    except TransitionError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_TRANSITION
    if observed:
        actor_id = _observed_actor(root, paths, task.claim_sha)
        if actor_id:
            updated.actor = actor_id
    summary = cp_summary(paths, task_id)
    for check in _parse_ac_checks(ac_checks, actor=updated.actor or "wily", ts=now):
        append_event(paths, task_id, check.to_event())
    parsed_ac_checks = read_ac_checks(paths, task_id)
    paths.task_dir(task_id).mkdir(parents=True, exist_ok=True)
    paths.result_md(task_id).write_text(
        _format_result(updated, done_at=now, current_sha=current_sha, changed=changed, cp_total=summary.total, cp_done=summary.done, note=note, observed=observed, ac_checks=parsed_ac_checks, context=context),
        encoding="utf-8",
    )
    save_tasks(paths, project_title, [updated if item.id == task_id else item for item in tasks])
    touch_wily(paths)
    if as_json:
        _common.emit_json(
            {
                "active_mode": context.active_mode,
                "task": updated.to_dict(),
                "changed_files": changed,
                "cp": {"done": summary.done, "total": summary.total},
                "result_md": str(paths.result_md(task_id).relative_to(root)),
            }
        )
        return _common.EXIT_OK
    _common.emit_text(f"{task_id}: {task.status.value} -> done")
    _common.emit_text(
        f"result.md written (changed {len(changed)} files, {summary.done}/{summary.total} cp, commit range {(task.claim_sha or '?')[:7]}..{current_sha[:7]})"
    )
    return _common.EXIT_OK


def _observed_actor(root: Path, paths: WilyPaths, claim_sha: str | None) -> str | None:
    if not claim_sha:
        return None
    actors = load_actors(paths)
    for commit in list_commits_since_fork(root, claim_sha, limit=20):
        actor = match_actor(actors, email=commit.author_email, name=commit.author_name)
        if actor:
            return actor.id
    return None


def _coordination_changed_files(context: ProjectContext, claim_snapshot: dict[str, object]) -> list[str]:
    if context.coordination is None:
        return []
    baseline_repos = claim_snapshot.get("repos") if isinstance(claim_snapshot.get("repos"), dict) else {}
    changed: list[str] = []
    for repo in context.coordination.all_repos:
        baseline = baseline_repos.get(repo.id) if isinstance(baseline_repos, dict) else None
        baseline_fingerprints = {}
        if isinstance(baseline, dict) and isinstance(baseline.get("fingerprints"), dict):
            baseline_fingerprints = baseline["fingerprints"]
        current = repo_snapshot(repo.path, exclude_paths=nested_repo_exclusions(context.coordination, repo))
        for path in current.get("changed_files") or []:
            if not isinstance(path, str):
                continue
            current_fingerprints = current.get("fingerprints") if isinstance(current.get("fingerprints"), dict) else {}
            if baseline_fingerprints.get(path) == current_fingerprints.get(path):
                continue
            changed.append(f"{repo.id}:{path}")
    return changed


def _format_result(
    task,
    *,
    done_at: str,
    current_sha: str,
    changed: list[str],
    cp_total: int,
    cp_done: int,
    note: str | None,
    observed: bool,
    ac_checks: list[AcCheck],
    context: ProjectContext | None = None,
) -> str:
    drift = _drift_summary(task.scope, changed, context=context)
    lines = [
        f"# {task.id}: {task.title} — done",
        "",
        f"- actor: {task.actor or '-'}{' (observed)' if observed else ''}",
        f"- claim: {task.claim_at or '-'} (sha {(task.claim_sha or '-')[:7]})",
        f"- done: {done_at}",
        f"- commit range: {(task.claim_sha or '?')[:7]}..{current_sha[:7]}",
        f"- changed files: {len(changed)}",
        f"- cp count: {cp_done}/{cp_total}",
        f"- scope drift: {drift}",
    ]
    if note:
        lines.append(f"- note: {note}")
    if ac_checks:
        items = {index: item for index, item in enumerate(task.acceptance_items, start=1)}
        lines.extend(["", "## Acceptance Checks", "", "| # | Status | Acceptance | Evidence |", "| --- | --- | --- | --- |"])
        for check in ac_checks:
            acceptance = items.get(check.index)
            lines.append(f"| {check.index} | {check.status} | {acceptance.text if acceptance else ''} | {check.evidence} |")
    if changed:
        lines.extend(["", "## Changed Files", ""])
        lines.extend(f"- {file}" for file in changed)
    lines.append("")
    return "\n".join(lines)


def _parse_ac_checks(values: list[str], *, actor: str, ts: str) -> list[AcCheck]:
    checks: list[AcCheck] = []
    for value in values:
        raw_index, _, raw_rest = value.partition("=")
        if not raw_index.isdigit() or not raw_rest:
            continue
        status, _, evidence = raw_rest.partition(":")
        checks.append(AcCheck(ts=ts, actor=actor, index=int(raw_index), status=status.strip().lower(), evidence=evidence.strip()))
    return checks


def _drift_summary(scope: list[str], changed: list[str], *, context: ProjectContext | None = None) -> str:
    outside = _outside_scope(scope, changed, context=context)
    if not scope:
        return "(no scope declared)" if outside else "0 files outside scope"
    if not outside:
        return "0 files outside scope"
    return f"{len(outside)} files outside scope (first: {outside[0]})"


def _outside_scope(scope: list[str], changed: list[str], *, context: ProjectContext | None = None) -> list[str]:
    if not scope:
        return list(changed)
    if context and context.coordination:
        entries = normalize_scope_entries(scope, default_repo=context.coordination.parent.id, coordination=True)
        outside = []
        for file in changed:
            repo_id, sep, path = file.partition(":")
            if not sep or not file_matches_scope(entries, repo_id=repo_id, path=path):
                outside.append(file)
        return outside
    return [file for file in changed if not any(fnmatch.fnmatch(file, pattern) for pattern in scope)]


def _extend_scope(scope: list[str], files: list[str]) -> list[str]:
    result = list(scope)
    for file in files:
        if file not in result:
            result.append(file)
    return result


def _emit_scope_drift_error(task_id: str, outside_scope: list[str]) -> None:
    _common.emit_error(f"scope drift detected for {task_id}: {len(outside_scope)} file(s) outside scope")
    for file in outside_scope[:10]:
        _common.emit_error(f"  - {file}")
    if len(outside_scope) > 10:
        _common.emit_error(f"  ... {len(outside_scope) - 10} more")
    _common.emit_error("rerun with --add-scope to include them in this task, or --stub-drift to create/reuse a drift helper task")
