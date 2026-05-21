"""Git observation helpers for Wily v3."""

from __future__ import annotations

import fnmatch
import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import Actor, Task


@dataclass
class CommitInfo:
    sha: str
    author_email: str
    author_name: str
    subject: str
    body: str
    trailers: dict[str, str] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
    )


def head_sha(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def initial_commit(repo: Path) -> str:
    out = _git(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
    return out.splitlines()[0] if out else head_sha(repo)


def observation_base(repo: Path) -> str:
    branch = _git(repo, "branch", "--show-current", check=False).stdout.strip()
    if branch:
        remote_ref = f"origin/{branch}"
        result = _git(repo, "rev-parse", "--verify", remote_ref, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return remote_ref
    return head_sha(repo)


def fetch_observation_remote(repo: Path) -> str | None:
    branch = _git(repo, "branch", "--show-current", check=False).stdout.strip()
    if not branch:
        return None
    remote_check = _git(repo, "remote", "get-url", "origin", check=False)
    if remote_check.returncode != 0:
        return None
    _git(repo, "fetch", "origin", branch, check=False)
    remote_ref = f"origin/{branch}"
    result = _git(repo, "rev-parse", "--verify", remote_ref, check=False)
    if result.returncode == 0 and result.stdout.strip():
        return remote_ref
    return None


def changed_files_since(repo: Path, sha: str) -> list[str]:
    out = _git(repo, "diff", "--name-only", f"{sha}...HEAD").stdout
    return [line for line in out.splitlines() if line.strip()]


def changed_files_since_by_actor(repo: Path, sha: str, *, actor: Actor | None) -> list[str]:
    if actor is None:
        return changed_files_since(repo, sha)
    files: list[str] = []
    seen: set[str] = set()
    for commit in list_commits_since_fork(repo, sha, limit=200):
        if not actor.matches(email=commit.author_email, name=commit.author_name):
            continue
        for file in commit.files:
            if file not in seen:
                seen.add(file)
                files.append(file)
    return files


def parse_trailers(message: str) -> dict[str, str]:
    lines = message.rstrip().splitlines()
    block: list[str] = []
    for line in reversed(lines):
        if not line.strip() or ":" not in line:
            break
        key, _, value = line.partition(":")
        if not key or any(ch.isspace() for ch in key):
            break
        block.append(f"{key.strip()}: {value.strip()}")
    trailers: dict[str, str] = {}
    for entry in block:
        key, _, value = entry.partition(":")
        trailers[key] = value
    return trailers


def match_actor(actors: Iterable[Actor], *, email: str, name: str) -> Actor | None:
    for actor in actors:
        if actor.matches(email=email, name=name):
            return actor
    return None


def guess_task_id(tasks: Iterable[Task], changed_files: list[str]) -> str | None:
    scores: dict[str, int] = {}
    for task in tasks:
        if not task.scope:
            continue
        hits = 0
        for file in changed_files:
            if any(fnmatch.fnmatch(file, pattern) for pattern in task.scope):
                hits += 1
        if hits:
            scores[task.id] = hits
    if not scores:
        return None
    return max(scores.items(), key=lambda item: item[1])[0]


def list_commits_since_fork(repo: Path, base_sha: str, *, limit: int = 50) -> list[CommitInfo]:
    return _list_commits_in_range(repo, f"{base_sha}..HEAD", limit=limit)


def list_remote_commits(repo: Path, remote_ref: str, *, limit: int = 50) -> list[CommitInfo]:
    return _list_commits_in_range(repo, f"HEAD..{remote_ref}", limit=limit)


def _list_commits_in_range(repo: Path, rev_range: str, *, limit: int = 50) -> list[CommitInfo]:
    result = _git(
        repo,
        "log",
        f"--max-count={limit}",
        "--pretty=format:%H%x1f%ae%x1f%an%x1f%s%x1f%b%x1e",
        rev_range,
        check=False,
    )
    if result.returncode != 0:
        return []
    commits: list[CommitInfo] = []
    for record in result.stdout.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 5:
            continue
        sha, email, name, subject, body = parts[:5]
        message = f"{subject}\n\n{body}" if body else subject
        files_out = _git(repo, "show", "--name-only", "--pretty=format:", sha, check=False)
        files = [line for line in files_out.stdout.splitlines() if line.strip()]
        commits.append(
            CommitInfo(
                sha=sha,
                author_email=email,
                author_name=name,
                subject=subject,
                body=body,
                trailers=parse_trailers(message),
                files=files,
            )
        )
    return commits


def git_config_identity(repo: Path) -> tuple[str, str]:
    email = _git(repo, "config", "user.email", check=False).stdout.strip()
    name = _git(repo, "config", "user.name", check=False).stdout.strip()
    return email, name


def claim_snapshot_for_repos(
    repos: Iterable[tuple[str, Path]],
    *,
    exclude_paths_by_repo: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    exclude_paths_by_repo = exclude_paths_by_repo or {}
    return {
        "schema": "wily-claim-snapshot-v1",
        "repos": {repo_id: repo_snapshot(path, exclude_paths=exclude_paths_by_repo.get(repo_id)) for repo_id, path in repos},
    }


def repo_snapshot(repo: Path, *, exclude_paths: Iterable[str] | None = None) -> dict[str, Any]:
    repo = repo.resolve()
    if not _is_git_repo(repo):
        return {
            "path": str(repo),
            "git_available": False,
            "branch": None,
            "sha": None,
            "dirty": False,
            "changed_files": [],
            "fingerprints": {},
        }
    branch = _git(repo, "branch", "--show-current", check=False).stdout.strip() or None
    sha_result = _git(repo, "rev-parse", "HEAD", check=False)
    sha = sha_result.stdout.strip() if sha_result.returncode == 0 else None
    changed = worktree_changed_files(repo, exclude_paths=exclude_paths)
    return {
        "path": str(repo),
        "git_available": True,
        "branch": branch,
        "sha": sha,
        "dirty": bool(changed),
        "changed_files": changed,
        "fingerprints": {path: file_fingerprint(repo / path) for path in changed},
    }


def worktree_changed_files(repo: Path, *, exclude_paths: Iterable[str] | None = None) -> list[str]:
    exclusions = _normalize_exclude_paths(exclude_paths)
    out = _git(repo, "status", "--porcelain=v2", check=False).stdout
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        if line.startswith("? "):
            path = line[2:]
            if _is_excluded(path, exclusions):
                continue
            files.extend(_expand_untracked(repo, path, exclusions))
            continue
        parts = line.split("\t")
        head = parts[0].split()
        if line.startswith("1 ") and len(head) >= 9:
            files.append(" ".join(head[8:]))
        elif line.startswith("2 ") and len(parts) >= 2:
            files.append(parts[0].split()[-1])
    return _dedupe([file for file in files if not _is_excluded(file, exclusions)])


def file_fingerprint(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
    except OSError:
        return {"kind": "missing"}
    if not path.is_file():
        return {"kind": "other", "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "kind": "file",
        "sha256": digest,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _is_git_repo(repo: Path) -> bool:
    result = _git(repo, "rev-parse", "--show-toplevel", check=False)
    return result.returncode == 0


def _expand_untracked(root: Path, path: str, exclude_paths: Iterable[str]) -> list[str]:
    full_path = root / path
    if not full_path.is_dir():
        return [path]
    return [
        item.relative_to(root).as_posix()
        for item in sorted(full_path.rglob("*"))
        if item.is_file() and not _is_excluded(item.relative_to(root).as_posix(), exclude_paths)
    ]


def _normalize_exclude_paths(paths: Iterable[str] | None) -> list[str]:
    if not paths:
        return []
    result: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/").strip("/")
        if normalized:
            result.append(normalized)
    return result


def _is_excluded(path: str, exclude_paths: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    for exclude in exclude_paths:
        if normalized == exclude or normalized.startswith(f"{exclude}/"):
            return True
    return False


def _dedupe(files: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for file in files:
        if file in seen:
            continue
        result.append(file)
        seen.add(file)
    return result
