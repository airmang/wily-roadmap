"""Repository registry watched by wily-agent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegisteredRepo:
    path: Path
    repo: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"path": str(self.path), "repo": self.repo}


def load_registry(path: Path) -> list[RegisteredRepo]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    repos = data.get("repos", []) if isinstance(data, dict) else []
    return [
        RegisteredRepo(path=Path(str(item.get("path", ""))).expanduser(), repo=str(item.get("repo", "")))
        for item in repos
        if isinstance(item, dict) and item.get("path")
    ]


def save_registry(path: Path, repos: list[RegisteredRepo]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"repos": [repo.to_dict() for repo in repos]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_repo(path: Path, repo: str, registry_path: Path) -> RegisteredRepo:
    root = path.resolve()
    if not (root / ".wily").is_dir():
        raise ValueError(f"not a Wily repo: {root}")
    current = load_registry(registry_path)
    entry = RegisteredRepo(path=root, repo=repo)
    merged = [item for item in current if item.path.resolve() != root]
    merged.append(entry)
    save_registry(registry_path, merged)
    return entry


def unregister_repo(path: Path, registry_path: Path) -> bool:
    root = path.resolve()
    current = load_registry(registry_path)
    kept = [item for item in current if item.path.resolve() != root]
    if len(kept) == len(current):
        return False
    save_registry(registry_path, kept)
    return True
