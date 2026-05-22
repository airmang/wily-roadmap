"""Parent-owned coordination project discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .paths import WilyPaths, WilyRootNotFound, find_wily_root
from .workspace import WorkspaceManifestError, discover_workspace_manifest

SCHEMA_VERSION = "wily-coordination-v1"


class CoordinationConfigError(Exception):
    """Raised when `.wily/coordination.yaml` is missing or invalid."""


@dataclass(frozen=True)
class CoordinationRepo:
    id: str
    path: Path
    title: str | None = None


@dataclass(frozen=True)
class CoordinationVisibility:
    kind: str
    owner: str


@dataclass(frozen=True)
class CoordinationConfig:
    title: str
    parent: CoordinationRepo
    repos: list[CoordinationRepo]
    manifest_path: Path
    visibility: CoordinationVisibility

    @property
    def all_repos(self) -> list[CoordinationRepo]:
        return [self.parent, *self.repos]


@dataclass(frozen=True)
class ProjectContext:
    active_mode: str
    paths: WilyPaths
    coordination: CoordinationConfig | None = None
    workspace_manifest: Path | None = None

    @property
    def root(self) -> Path:
        return self.paths.root

    @property
    def parent_repo_id(self) -> str:
        if self.coordination is None:
            return "root"
        return self.coordination.parent.id

    def repo_id_for_path(self, path: Path) -> str | None:
        target = path.resolve()
        repos = self.coordination.all_repos if self.coordination else [CoordinationRepo(id="root", path=self.root)]
        matches = [
            repo
            for repo in repos
            if target == repo.path or _is_relative_to(target, repo.path)
        ]
        if not matches:
            return None
        return max(matches, key=lambda repo: len(repo.path.parts)).id


def nested_repo_exclusions(coordination: CoordinationConfig, repo: CoordinationRepo) -> list[str]:
    """Return registered repo paths nested under this repo, relative to this repo."""

    exclusions: list[str] = []
    for candidate in coordination.all_repos:
        if candidate.id == repo.id:
            continue
        try:
            relative = candidate.path.relative_to(repo.path)
        except ValueError:
            continue
        if relative.parts:
            exclusions.append(relative.as_posix())
    return exclusions


def load_coordination_config(manifest_path: Path) -> CoordinationConfig:
    manifest_path = manifest_path.resolve()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise CoordinationConfigError(f"coordination config must be a mapping: {manifest_path}")
    schema = data.get("schema")
    if schema != SCHEMA_VERSION:
        raise CoordinationConfigError(f"unsupported coordination schema {schema!r}")
    base = manifest_path.parent.parent if manifest_path.parent.name == ".wily" else manifest_path.parent
    parent = _repo_from_dict(data.get("parent") or {"id": "parent", "path": "."}, base=base, label="parent")
    repos_data = data.get("repos") or []
    if not isinstance(repos_data, list):
        raise CoordinationConfigError("coordination repos must be a list")
    repos = [_repo_from_dict(item, base=base, label=f"repo {index + 1}") for index, item in enumerate(repos_data)]
    _validate_repo_ids([parent, *repos])
    return CoordinationConfig(
        title=str(data.get("title") or "Wily Coordination"),
        parent=parent,
        repos=repos,
        manifest_path=manifest_path,
        visibility=_visibility_from_dict(data.get("visibility")),
    )


def resolve_project_context(start: Path) -> ProjectContext:
    try:
        root = find_wily_root(start)
    except WilyRootNotFound:
        raise
    paths = WilyPaths(root)
    coordination_path = paths.wily_dir / "coordination.yaml"
    if coordination_path.is_file():
        return ProjectContext(
            active_mode="coordination",
            paths=paths,
            coordination=load_coordination_config(coordination_path),
            workspace_manifest=_optional_workspace_manifest(start),
        )
    return ProjectContext(
        active_mode="single_repo",
        paths=paths,
        workspace_manifest=_optional_workspace_manifest(start),
    )


def _repo_from_dict(item: Any, *, base: Path, label: str) -> CoordinationRepo:
    if not isinstance(item, dict):
        raise CoordinationConfigError(f"coordination {label} must be a mapping")
    repo_id = str(item.get("id") or "").strip()
    path_value = str(item.get("path") or "").strip()
    if not repo_id:
        raise CoordinationConfigError(f"coordination {label} is missing id")
    if not path_value:
        raise CoordinationConfigError(f"coordination {label} is missing path")
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = base / path
    return CoordinationRepo(
        id=repo_id,
        path=path.resolve(),
        title=str(item["title"]) if item.get("title") else None,
    )


def _visibility_from_dict(raw: Any) -> CoordinationVisibility:
    if raw is None:
        return CoordinationVisibility(kind="collab", owner="R-W-LAB")
    if not isinstance(raw, dict):
        raise CoordinationConfigError("coordination visibility must be a mapping")
    kind = str(raw.get("kind") or "collab").strip()
    owner = str(raw.get("owner") or ("R-W-LAB" if kind == "collab" else "")).strip()
    if kind not in {"collab", "personal"}:
        raise CoordinationConfigError("coordination visibility kind must be collab or personal")
    if kind == "personal" and not owner:
        raise CoordinationConfigError("personal coordination visibility requires owner")
    return CoordinationVisibility(kind=kind, owner=owner)


def _validate_repo_ids(repos: list[CoordinationRepo]) -> None:
    seen: set[str] = set()
    for repo in repos:
        if repo.id in seen:
            raise CoordinationConfigError(f"duplicate coordination repo id: {repo.id}")
        seen.add(repo.id)

def _optional_workspace_manifest(start: Path) -> Path | None:
    try:
        return discover_workspace_manifest(start)
    except WorkspaceManifestError:
        return None


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False
