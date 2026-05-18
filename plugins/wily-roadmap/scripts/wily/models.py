"""Domain models for Wily v3."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class TaskStatus(str, enum.Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class Task:
    id: str
    title: str
    intent: str = ""
    acceptance: str = ""
    acceptance_file: str | None = None
    scope: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    parallel_lane: str | None = None
    priority: int | None = None
    capacity_hint: int | None = None
    status: TaskStatus = TaskStatus.READY
    assignee: str | None = None
    actor: str | None = None
    claim_sha: str | None = None
    claim_at: str | None = None
    done_at: str | None = None
    blocker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "intent": self.intent,
            "acceptance": self.acceptance,
            "scope": list(self.scope),
            "depends_on": list(self.depends_on),
            "status": self.status.value,
            "assignee": self.assignee,
            "actor": self.actor,
            "claim_sha": self.claim_sha,
            "claim_at": self.claim_at,
            "done_at": self.done_at,
            "blocker": self.blocker,
        }
        if self.acceptance_file:
            data["acceptance_file"] = self.acceptance_file
        if self.parallel_lane:
            data["parallel_lane"] = self.parallel_lane
        if self.priority is not None:
            data["priority"] = self.priority
        if self.capacity_hint is not None:
            data["capacity_hint"] = self.capacity_hint
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            intent=str(data.get("intent") or ""),
            acceptance=str(data.get("acceptance") or ""),
            acceptance_file=data.get("acceptance_file"),
            scope=list(data.get("scope") or []),
            depends_on=list(data.get("depends_on") or []),
            parallel_lane=str(data["parallel_lane"]) if data.get("parallel_lane") else None,
            priority=_optional_int(data.get("priority")),
            capacity_hint=_optional_int(data.get("capacity_hint")),
            status=TaskStatus(data.get("status") or "ready"),
            assignee=data.get("assignee"),
            actor=data.get("actor"),
            claim_sha=data.get("claim_sha"),
            claim_at=data.get("claim_at"),
            done_at=data.get("done_at"),
            blocker=data.get("blocker"),
        )


@dataclass
class Actor:
    id: str
    display: str
    git_author_emails: list[str] = field(default_factory=list)
    git_author_names: list[str] = field(default_factory=list)
    capacity: int = 1

    def matches(self, *, email: str = "", name: str = "") -> bool:
        if email and email.lower() in {e.lower() for e in self.git_author_emails}:
            return True
        if name and name in self.git_author_names:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "display": self.display,
            "git_author_emails": list(self.git_author_emails),
            "git_author_names": list(self.git_author_names),
        }
        if self.capacity != 1:
            data["capacity"] = self.capacity
        return data

    @classmethod
    def from_dict(cls, id_: str, data: dict[str, Any]) -> "Actor":
        return cls(
            id=id_,
            display=str(data.get("display") or id_),
            git_author_emails=list(data.get("git_author_emails") or []),
            git_author_names=list(data.get("git_author_names") or []),
            capacity=max(_optional_int(data.get("capacity")) or 1, 1),
        )


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
