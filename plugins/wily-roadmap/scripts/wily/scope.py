"""Repo-aware task scope helpers."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScopeEntry:
    repo: str
    path: str
    source: Any


def normalize_scope_entries(
    values: list[Any],
    *,
    default_repo: str = "parent",
    coordination: bool = False,
) -> list[ScopeEntry]:
    entries: list[ScopeEntry] = []
    for value in values:
        entries.append(_normalize_scope_entry(value, default_repo=default_repo, coordination=coordination))
    return entries


def scope_to_yaml(entries: list[ScopeEntry]) -> list[Any]:
    values: list[Any] = []
    for entry in entries:
        if isinstance(entry.source, str):
            values.append(entry.source)
        elif isinstance(entry.source, dict):
            values.append({"repo": entry.repo, "path": entry.path})
        else:
            values.append(f"{entry.repo}:{entry.path}")
    return values


def file_matches_scope(entries: list[ScopeEntry], *, repo_id: str, path: str) -> bool:
    return any(entry.repo == repo_id and fnmatch.fnmatch(path, entry.path) for entry in entries)


def files_outside_scope(entries: list[ScopeEntry], *, repo_id: str, paths: list[str]) -> list[str]:
    return [path for path in paths if not file_matches_scope(entries, repo_id=repo_id, path=path)]


def _normalize_scope_entry(value: Any, *, default_repo: str, coordination: bool) -> ScopeEntry:
    if isinstance(value, dict):
        repo = str(value.get("repo") or default_repo).strip()
        path = str(value.get("path") or "").strip()
        if not repo:
            repo = default_repo
        if not path:
            raise ValueError("scope mapping requires path")
        return ScopeEntry(repo=repo, path=path, source=dict(value))
    text = str(value or "").strip()
    if not text:
        raise ValueError("scope entry must not be empty")
    if coordination and ":" in text:
        repo, path = text.split(":", 1)
        repo = repo.strip()
        path = path.strip()
        if repo and path:
            return ScopeEntry(repo=repo, path=path, source=text)
    return ScopeEntry(repo=default_repo, path=text, source=text)
