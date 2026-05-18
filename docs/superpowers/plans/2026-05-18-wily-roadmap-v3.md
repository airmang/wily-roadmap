# Wily Roadmap v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace wily-roadmap v2 (Stage/Phase/Session 3-layer, 16 skills, board integration) with v3 (Project + flat goal-sized Task list, 10 commands + 1 meta skill, no board), adopt v3 onto this repo's own `.wily/` via brownfield migration.

**Architecture:** Module split. `plugins/wily-roadmap/scripts/wily.py` becomes thin entry that imports from new `wily/` package. Each command in its own `cli/<cmd>.py`. Pure functions for state transitions, git observation, progress tracking, interview engine, repo analysis. wily never calls custom-workflow directly — it emits goal text and Claude/Codex agents do the orchestration. Board code deleted wholesale. All v2 skills replaced.

**Tech Stack:** Python 3.11+ stdlib, PyYAML (already a v2 dep), `subprocess` for git, `rich` for watch UI (v2 already uses it via `.venv-watch`). Unit tests via `unittest` (existing convention in `plugins/wily-roadmap/tests/`).

**Spec reference:** `docs/superpowers/specs/2026-05-18-wily-redesign-design.md` (commit `da9b2d3`). Decisions D1–D10 in spec §2 are non-negotiable.

**Execution conventions:**
- All paths are absolute or relative to repo root `/Users/wilycastle/Code/projects/wily-roadmap`.
- Test runner: `python3 -m unittest discover -s plugins/wily-roadmap/tests -v` (or `-p test_<name>.py`).
- Commit after each task. Use `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer only when handing off through Claude Code; pure Codex commits use Codex's own convention.
- Do NOT push during this work. Push is a separate manual action.

---

## Phase 0 — Branch + scaffolding

### Task 0.1: Create feature branch

**Files:** none (git only)

- [ ] **Step 1: Verify clean state for v3 work**

```bash
git status --short
```

Expected: existing dirty files (`README.md`, `plugins/wily-roadmap/tests/test_wily_cli.py`, untracked `wily`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`) may be present. They are unrelated to v3 — leave them alone.

- [ ] **Step 2: Create feature branch from main**

```bash
git checkout -b feat/wily-v3-redesign
```

Expected: `Switched to a new branch 'feat/wily-v3-redesign'`.

- [ ] **Step 3: Stash dirty unrelated files if present**

```bash
git stash push -m "v2 dirty before v3 work" -- README.md plugins/wily-roadmap/tests/test_wily_cli.py
```

If nothing to stash, skip. Untracked files (`wily`, agent-handoffs) stay in place — they don't conflict with v3 work.

- [ ] **Step 4: Verify branch state**

```bash
git status --short
git log --oneline -3
```

Expected: working tree only has untracked files (`wily`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`). HEAD points at `da9b2d3` (spec commit).

- [ ] **Step 5: Commit branch marker (empty commit)**

```bash
git commit --allow-empty -m "chore: open wily v3 redesign branch"
```

Reason: gives a clear branch base for `git diff feat/wily-v3-redesign..main` if needed later.

---

### Task 0.2: Create new package skeleton

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/__init__.py`
- Create: `plugins/wily-roadmap/scripts/wily/cli/__init__.py`
- Create: `plugins/wily-roadmap/scripts/wily/ui/__init__.py`
- Create: `plugins/wily-roadmap/tests/v3/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `plugins/wily-roadmap/tests/v3/test_package_import.py`:

```python
import unittest


class PackageImportTest(unittest.TestCase):
    def test_wily_package_imports(self) -> None:
        import wily  # noqa: F401

    def test_wily_cli_package_imports(self) -> None:
        from wily import cli  # noqa: F401

    def test_wily_ui_package_imports(self) -> None:
        from wily import ui  # noqa: F401
```

The existing test infra at `plugins/wily-roadmap/tests/test_wily_cli.py` already inserts `plugins/wily-roadmap/scripts` on `sys.path`. New tests need the same. Add at top of `test_package_import.py`:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_package_import -v
```

Expected: `ModuleNotFoundError: No module named 'wily'`.

- [ ] **Step 3: Create empty package files**

```bash
mkdir -p plugins/wily-roadmap/scripts/wily/cli plugins/wily-roadmap/scripts/wily/ui plugins/wily-roadmap/tests/v3
touch plugins/wily-roadmap/scripts/wily/__init__.py
touch plugins/wily-roadmap/scripts/wily/cli/__init__.py
touch plugins/wily-roadmap/scripts/wily/ui/__init__.py
touch plugins/wily-roadmap/tests/v3/__init__.py
```

Add to `plugins/wily-roadmap/scripts/wily/__init__.py`:

```python
"""wily-roadmap v3 — Project + flat Task manager.

See docs/superpowers/specs/2026-05-18-wily-redesign-design.md for design.
"""
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_package_import -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/ plugins/wily-roadmap/tests/v3/
git commit -m "feat(wily): scaffold v3 package skeleton"
```

---

## Phase 1 — Data layer

### Task 1.1: `paths.py` — resolve `.wily/` root

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/paths.py`
- Test: `plugins/wily-roadmap/tests/v3/test_paths.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_paths.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.paths import WilyPaths, find_wily_root, WilyRootNotFound  # noqa: E402


class WilyPathsTest(unittest.TestCase):
    def test_find_root_at_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            self.assertEqual(find_wily_root(project), project)

    def test_find_root_walks_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            sub = project / "a" / "b"
            sub.mkdir(parents=True)
            self.assertEqual(find_wily_root(sub), project)

    def test_find_root_missing_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WilyRootNotFound):
                find_wily_root(Path(tmp))

    def test_paths_compose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            paths = WilyPaths(project)
            self.assertEqual(paths.tasks_yaml, project / ".wily" / "tasks.yaml")
            self.assertEqual(paths.actors_yaml, project / ".wily" / "actors.yaml")
            self.assertEqual(paths.project_md, project / ".wily" / "project.md")
            self.assertEqual(paths.task_dir("T05"), project / ".wily" / "tasks" / "T05")
            self.assertEqual(paths.progress_jsonl("T05"), project / ".wily" / "tasks" / "T05" / "progress.jsonl")
            self.assertEqual(paths.result_md("T05"), project / ".wily" / "tasks" / "T05" / "result.md")
            self.assertEqual(paths.init_draft, project / ".wily" / "init" / "draft.yaml")
            self.assertEqual(paths.archive_dir, project / ".wily" / "archive")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_paths -v
```

Expected: `ModuleNotFoundError: No module named 'wily.paths'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/paths.py`:

```python
"""Resolve .wily/ root and compose canonical paths.

A .wily/ directory marks the project root. Subcommands walk up from CWD
until they find one. All schema artifacts (tasks.yaml, actors.yaml,
project.md, tasks/<id>/...) live under it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class WilyRootNotFound(Exception):
    """Raised when no .wily/ directory exists at or above the given path."""


def find_wily_root(start: Path) -> Path:
    """Walk up from `start` to find the first ancestor containing `.wily/`."""
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
    def init_dir(self) -> Path:
        return self.wily_dir / "init"

    @property
    def init_draft(self) -> Path:
        return self.init_dir / "draft.yaml"

    @property
    def archive_dir(self) -> Path:
        return self.wily_dir / "archive"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_paths -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/paths.py plugins/wily-roadmap/tests/v3/test_paths.py
git commit -m "feat(wily): v3 paths module"
```

---

### Task 1.2: `models.py` — Task and Actor dataclasses

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/models.py`
- Test: `plugins/wily-roadmap/tests/v3/test_models.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_models.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.models import Task, Actor, TaskStatus  # noqa: E402


class TaskModelTest(unittest.TestCase):
    def test_task_defaults(self) -> None:
        t = Task(id="T01", title="Foo")
        self.assertEqual(t.id, "T01")
        self.assertEqual(t.title, "Foo")
        self.assertEqual(t.status, TaskStatus.READY)
        self.assertIsNone(t.actor)
        self.assertIsNone(t.assignee)
        self.assertEqual(t.depends_on, [])
        self.assertEqual(t.scope, [])

    def test_task_to_dict_round_trip(self) -> None:
        t = Task(
            id="T05",
            title="Lifecycle CLI",
            intent="implement claim/go/done",
            acceptance="status transitions correctly",
            scope=["plugins/wily-roadmap/scripts/wily.py"],
            depends_on=["T01"],
            status=TaskStatus.IN_PROGRESS,
            assignee="wily",
            actor="wily",
            claim_sha="abc123",
            claim_at="2026-05-18T11:00:00Z",
        )
        data = t.to_dict()
        restored = Task.from_dict(data)
        self.assertEqual(restored, t)

    def test_task_status_values(self) -> None:
        self.assertEqual(TaskStatus.READY.value, "ready")
        self.assertEqual(TaskStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(TaskStatus.DONE.value, "done")
        self.assertEqual(TaskStatus.BLOCKED.value, "blocked")


class ActorModelTest(unittest.TestCase):
    def test_actor_match_by_email(self) -> None:
        a = Actor(
            id="wily",
            display="Wily 박사",
            git_author_emails=["kokyuhyun@goedu.kr"],
            git_author_names=["kokyuhyun"],
        )
        self.assertTrue(a.matches(email="kokyuhyun@goedu.kr", name="anything"))
        self.assertFalse(a.matches(email="someone@else.com", name="anything"))

    def test_actor_match_by_name_when_email_misses(self) -> None:
        a = Actor(
            id="right",
            display="Right",
            git_author_emails=[],
            git_author_names=["right-dev"],
        )
        self.assertTrue(a.matches(email="unmatched@x.com", name="right-dev"))

    def test_actor_to_dict_round_trip(self) -> None:
        a = Actor(
            id="wily",
            display="Wily 박사",
            git_author_emails=["kokyuhyun@goedu.kr"],
            git_author_names=["kokyuhyun", "wilycastle"],
        )
        self.assertEqual(Actor.from_dict("wily", a.to_dict()), a)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_models -v
```

Expected: `ModuleNotFoundError: No module named 'wily.models'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/models.py`:

```python
"""Domain models for wily v3.

Task: a goal-sized unit of work, owned by wily and managed via the
lifecycle commands (claim/go/done/block).

Actor: a person (or agent) who can be a task assignee or claim actor.
Mapped to git authors so we can attribute commits to actors.

TaskStatus: the four-state machine: ready → in_progress → done, with
blocked as a side state. No verifying/partial/superseded — keep it boring.
"""

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
    status: TaskStatus = TaskStatus.READY
    assignee: str | None = None
    actor: str | None = None
    claim_sha: str | None = None
    claim_at: str | None = None
    done_at: str | None = None
    blocker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
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
            out["acceptance_file"] = self.acceptance_file
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            intent=data.get("intent", ""),
            acceptance=data.get("acceptance", ""),
            acceptance_file=data.get("acceptance_file"),
            scope=list(data.get("scope") or []),
            depends_on=list(data.get("depends_on") or []),
            status=TaskStatus(data.get("status", "ready")),
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

    def matches(self, email: str, name: str) -> bool:
        if email and email.lower() in {e.lower() for e in self.git_author_emails}:
            return True
        if name and name in self.git_author_names:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "display": self.display,
            "git_author_emails": list(self.git_author_emails),
            "git_author_names": list(self.git_author_names),
        }

    @classmethod
    def from_dict(cls, id_: str, data: dict[str, Any]) -> "Actor":
        return cls(
            id=id_,
            display=data.get("display", id_),
            git_author_emails=list(data.get("git_author_emails") or []),
            git_author_names=list(data.get("git_author_names") or []),
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_models -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/models.py plugins/wily-roadmap/tests/v3/test_models.py
git commit -m "feat(wily): v3 Task and Actor models"
```

---

### Task 1.3: `config.py` — load/save tasks.yaml + actors.yaml

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/config.py`
- Test: `plugins/wily-roadmap/tests/v3/test_config.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_config.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.config import (  # noqa: E402
    load_tasks,
    save_tasks,
    load_actors,
    save_actors,
    repo_mode,
    SCHEMA_VERSION,
)
from wily.models import Task, Actor, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


class TasksYamlTest(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = WilyPaths(Path(tmp))
            paths.wily_dir.mkdir()
            tasks = [
                Task(id="T01", title="First", status=TaskStatus.DONE, assignee="wily"),
                Task(id="T02", title="Second", depends_on=["T01"]),
            ]
            save_tasks(paths, "demo", tasks)
            project_title, restored = load_tasks(paths)
            self.assertEqual(project_title, "demo")
            self.assertEqual(restored, tasks)

    def test_load_missing_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = WilyPaths(Path(tmp))
            paths.wily_dir.mkdir()
            project_title, tasks = load_tasks(paths)
            self.assertEqual(project_title, "")
            self.assertEqual(tasks, [])


class ActorsYamlTest(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = WilyPaths(Path(tmp))
            paths.wily_dir.mkdir()
            actors = [
                Actor(id="wily", display="Wily", git_author_emails=["a@b"]),
                Actor(id="right", display="Right", git_author_names=["right"]),
            ]
            save_actors(paths, actors)
            restored = load_actors(paths)
            self.assertEqual(restored, actors)

    def test_repo_mode_solo_when_single_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = WilyPaths(Path(tmp))
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            self.assertEqual(repo_mode(paths), "solo")

    def test_repo_mode_collab_when_multi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = WilyPaths(Path(tmp))
            paths.wily_dir.mkdir()
            save_actors(
                paths,
                [Actor(id="wily", display="Wily"), Actor(id="right", display="Right")],
            )
            self.assertEqual(repo_mode(paths), "collab")


class SchemaVersionTest(unittest.TestCase):
    def test_schema_constant(self) -> None:
        self.assertEqual(SCHEMA_VERSION, "wily-v3")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_config -v
```

Expected: `ModuleNotFoundError: No module named 'wily.config'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/config.py`:

```python
"""Load and save tasks.yaml / actors.yaml.

These two files are the canonical v3 state. project.md is freeform
text edited by init/replan; everything machine-readable lives here.

PyYAML is the dependency (already used by v2). We use safe_load and
preserve a stable ordering on save so diffs stay clean.
"""

from __future__ import annotations

from typing import Iterable

import yaml

from .models import Actor, Task
from .paths import WilyPaths

SCHEMA_VERSION = "wily-v3"


def load_tasks(paths: WilyPaths) -> tuple[str, list[Task]]:
    """Return (project_title, tasks). Empty result if file is missing."""
    if not paths.tasks_yaml.exists():
        return "", []
    with paths.tasks_yaml.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if data.get("schema") and data["schema"] != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported tasks.yaml schema {data['schema']!r}; expected {SCHEMA_VERSION!r}"
        )
    project_title = data.get("project_title", "")
    tasks = [Task.from_dict(item) for item in data.get("tasks") or []]
    return project_title, tasks


def save_tasks(paths: WilyPaths, project_title: str, tasks: Iterable[Task]) -> None:
    paths.wily_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": SCHEMA_VERSION,
        "project_title": project_title,
        "tasks": [t.to_dict() for t in tasks],
    }
    with paths.tasks_yaml.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=True)


def load_actors(paths: WilyPaths) -> list[Actor]:
    if not paths.actors_yaml.exists():
        return []
    with paths.actors_yaml.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if data.get("schema") and data["schema"] != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported actors.yaml schema {data['schema']!r}; expected {SCHEMA_VERSION!r}"
        )
    actors_data = data.get("actors") or {}
    return [Actor.from_dict(aid, ad) for aid, ad in actors_data.items()]


def save_actors(paths: WilyPaths, actors: Iterable[Actor]) -> None:
    paths.wily_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": SCHEMA_VERSION,
        "actors": {a.id: a.to_dict() for a in actors},
    }
    with paths.actors_yaml.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=True)


def repo_mode(paths: WilyPaths) -> str:
    """Return 'solo' if 0/1 actors, 'collab' if 2+."""
    actors = load_actors(paths)
    return "collab" if len(actors) >= 2 else "solo"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_config -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/config.py plugins/wily-roadmap/tests/v3/test_config.py
git commit -m "feat(wily): v3 tasks.yaml/actors.yaml load and save"
```

---

## Phase 2 — State transitions

### Task 2.1: `transitions.py` — claim/done/block state machine

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/transitions.py`
- Test: `plugins/wily-roadmap/tests/v3/test_transitions.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_transitions.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.models import Task, TaskStatus  # noqa: E402
from wily.transitions import (  # noqa: E402
    TransitionError,
    apply_claim,
    apply_done,
    apply_block,
    check_dependencies,
    DependencyError,
)


def _task(**overrides) -> Task:
    base = dict(id="T01", title="t")
    base.update(overrides)
    return Task(**base)


class ClaimTransitionTest(unittest.TestCase):
    def test_claim_from_ready(self) -> None:
        t = _task()
        result = apply_claim(t, actor="wily", sha="abc", at="2026-05-18T11:00:00Z")
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.actor, "wily")
        self.assertEqual(result.claim_sha, "abc")
        self.assertEqual(result.claim_at, "2026-05-18T11:00:00Z")
        self.assertIsNone(result.blocker)

    def test_claim_from_blocked_clears_blocker(self) -> None:
        t = _task(status=TaskStatus.BLOCKED, blocker="net down")
        result = apply_claim(t, actor="wily", sha="abc", at="2026-05-18T11:00:00Z")
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNone(result.blocker)

    def test_claim_from_in_progress_rejects(self) -> None:
        t = _task(status=TaskStatus.IN_PROGRESS, actor="right")
        with self.assertRaises(TransitionError):
            apply_claim(t, actor="wily", sha="abc", at="2026-05-18T11:00:00Z")

    def test_claim_force_overrides_in_progress(self) -> None:
        t = _task(status=TaskStatus.IN_PROGRESS, actor="right")
        result = apply_claim(t, actor="wily", sha="abc", at="2026-05-18T11:00:00Z", force=True)
        self.assertEqual(result.actor, "wily")
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)

    def test_claim_from_done_rejects(self) -> None:
        t = _task(status=TaskStatus.DONE)
        with self.assertRaises(TransitionError):
            apply_claim(t, actor="wily", sha="abc", at="2026-05-18T11:00:00Z")


class DoneTransitionTest(unittest.TestCase):
    def test_done_from_in_progress(self) -> None:
        t = _task(status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha="abc")
        result = apply_done(t, at="2026-05-18T13:00:00Z")
        self.assertEqual(result.status, TaskStatus.DONE)
        self.assertEqual(result.done_at, "2026-05-18T13:00:00Z")

    def test_done_from_ready_rejects(self) -> None:
        t = _task()
        with self.assertRaises(TransitionError):
            apply_done(t, at="2026-05-18T13:00:00Z")

    def test_done_force_from_blocked(self) -> None:
        t = _task(status=TaskStatus.BLOCKED, blocker="x")
        result = apply_done(t, at="2026-05-18T13:00:00Z", force=True)
        self.assertEqual(result.status, TaskStatus.DONE)


class BlockTransitionTest(unittest.TestCase):
    def test_block_from_ready(self) -> None:
        t = _task()
        result = apply_block(t, reason="net down")
        self.assertEqual(result.status, TaskStatus.BLOCKED)
        self.assertEqual(result.blocker, "net down")

    def test_block_from_in_progress(self) -> None:
        t = _task(status=TaskStatus.IN_PROGRESS, actor="wily")
        result = apply_block(t, reason="api 401")
        self.assertEqual(result.status, TaskStatus.BLOCKED)

    def test_block_from_done_rejects(self) -> None:
        t = _task(status=TaskStatus.DONE)
        with self.assertRaises(TransitionError):
            apply_block(t, reason="x")


class DependencyValidationTest(unittest.TestCase):
    def test_dependencies_satisfied(self) -> None:
        tasks = [
            _task(id="T01", status=TaskStatus.DONE),
            _task(id="T02", depends_on=["T01"]),
        ]
        check_dependencies(tasks)  # no raise

    def test_missing_dependency_id_raises(self) -> None:
        tasks = [_task(id="T02", depends_on=["TX"])]
        with self.assertRaises(DependencyError):
            check_dependencies(tasks)

    def test_cycle_detected(self) -> None:
        tasks = [
            _task(id="T01", depends_on=["T02"]),
            _task(id="T02", depends_on=["T01"]),
        ]
        with self.assertRaises(DependencyError):
            check_dependencies(tasks)

    def test_self_loop_detected(self) -> None:
        tasks = [_task(id="T01", depends_on=["T01"])]
        with self.assertRaises(DependencyError):
            check_dependencies(tasks)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_transitions -v
```

Expected: `ModuleNotFoundError: No module named 'wily.transitions'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/transitions.py`:

```python
"""Task state transitions and dependency validation.

Pure functions: input Task, output new Task (or raise). Callers persist
the result via wily.config. No I/O here.

Transition rules (D8 in spec):
  - ready    -> in_progress   via apply_claim
  - blocked  -> in_progress   via apply_claim (blocker cleared)
  - in_progress -> in_progress via apply_claim(force=True) (steal)
  - in_progress -> done       via apply_done
  - blocked  -> done          via apply_done(force=True)
  - ready/in_progress -> blocked via apply_block
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import Task, TaskStatus


class TransitionError(Exception):
    """Raised when a state transition is not allowed."""


class DependencyError(Exception):
    """Raised when depends_on references are inconsistent (cycle/missing)."""


def apply_claim(
    task: Task,
    *,
    actor: str,
    sha: str,
    at: str,
    force: bool = False,
) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(
            f"{task.id} is done; cannot claim. Use replan to revive."
        )
    if task.status == TaskStatus.IN_PROGRESS and not force:
        raise TransitionError(
            f"{task.id} is already in_progress by {task.actor or '?'}; "
            "use --force to steal."
        )
    return replace(
        task,
        status=TaskStatus.IN_PROGRESS,
        actor=actor,
        claim_sha=sha,
        claim_at=at,
        blocker=None,
    )


def apply_done(task: Task, *, at: str, force: bool = False) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(f"{task.id} is already done.")
    if task.status != TaskStatus.IN_PROGRESS and not force:
        raise TransitionError(
            f"{task.id} is {task.status.value}; claim first or use --force."
        )
    return replace(task, status=TaskStatus.DONE, done_at=at)


def apply_block(task: Task, *, reason: str) -> Task:
    if task.status == TaskStatus.DONE:
        raise TransitionError(f"{task.id} is done; cannot block.")
    return replace(task, status=TaskStatus.BLOCKED, blocker=reason)


def check_dependencies(tasks: Iterable[Task]) -> None:
    tasks_list = list(tasks)
    by_id = {t.id: t for t in tasks_list}

    # Missing references and self-loops.
    for t in tasks_list:
        for dep in t.depends_on:
            if dep == t.id:
                raise DependencyError(f"{t.id} depends on itself")
            if dep not in by_id:
                raise DependencyError(f"{t.id} depends on missing task {dep!r}")

    # Cycle detection via DFS with WHITE/GRAY/BLACK marking.
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {t.id: WHITE for t in tasks_list}

    def visit(tid: str, stack: list[str]) -> None:
        if color[tid] == GRAY:
            cycle = " -> ".join(stack + [tid])
            raise DependencyError(f"dependency cycle: {cycle}")
        if color[tid] == BLACK:
            return
        color[tid] = GRAY
        for dep in by_id[tid].depends_on:
            visit(dep, stack + [tid])
        color[tid] = BLACK

    for t in tasks_list:
        if color[t.id] == WHITE:
            visit(t.id, [])
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_transitions -v
```

Expected: 13 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/transitions.py plugins/wily-roadmap/tests/v3/test_transitions.py
git commit -m "feat(wily): v3 state transitions and dependency validation"
```

---

## Phase 3 — Progress tracking

### Task 3.1: `progress.py` — append/read cp events

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/progress.py`
- Test: `plugins/wily-roadmap/tests/v3/test_progress.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_progress.py`:

```python
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.paths import WilyPaths  # noqa: E402
from wily.progress import (  # noqa: E402
    init_progress,
    append_event,
    read_events,
    cp_summary,
    CpEvent,
)


class ProgressTest(unittest.TestCase):
    def _paths(self, tmp: Path) -> WilyPaths:
        paths = WilyPaths(tmp)
        paths.wily_dir.mkdir()
        return paths

    def test_init_creates_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(Path(tmp))
            init_progress(paths, "T01")
            target = paths.progress_jsonl("T01")
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "")

    def test_append_and_read_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(Path(tmp))
            init_progress(paths, "T01")
            append_event(paths, "T01", CpEvent(ts="2026-05-18T11:00:00Z", actor="wily", cp="plan", event="start"))
            append_event(paths, "T01", CpEvent(ts="2026-05-18T11:05:00Z", actor="wily", cp="plan", event="done"))
            events = read_events(paths, "T01")
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0].cp, "plan")
            self.assertEqual(events[1].event, "done")

    def test_read_ignores_corrupt_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(Path(tmp))
            init_progress(paths, "T01")
            target = paths.progress_jsonl("T01")
            with target.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": "2026-05-18T11:00:00Z", "actor": "wily", "cp": "a", "event": "start"}) + "\n")
                fh.write("not-json garbage\n")
                fh.write(json.dumps({"ts": "2026-05-18T11:05:00Z", "actor": "wily", "cp": "a", "event": "done"}) + "\n")
            events = read_events(paths, "T01")
            self.assertEqual(len(events), 2)

    def test_cp_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(Path(tmp))
            init_progress(paths, "T01")
            for cp in ("a", "b", "c"):
                append_event(paths, "T01", CpEvent(ts="2026-05-18T11:00:00Z", actor="wily", cp=cp, event="start"))
            append_event(paths, "T01", CpEvent(ts="2026-05-18T11:05:00Z", actor="wily", cp="a", event="done"))
            append_event(paths, "T01", CpEvent(ts="2026-05-18T11:05:00Z", actor="wily", cp="b", event="done"))
            summary = cp_summary(paths, "T01")
            self.assertEqual(summary.total, 3)
            self.assertEqual(summary.done, 2)
            self.assertEqual(summary.in_progress, 1)
            self.assertEqual(summary.current_cp, "c")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_progress -v
```

Expected: `ModuleNotFoundError: No module named 'wily.progress'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/progress.py`:

```python
"""Per-task progress.jsonl read/write.

custom-workflow appends a line per cp start/done. wily watch/status reads
it to render a [3/5 cp] gauge. Corrupted lines are warn-and-skip; we
never raise on parse errors because cw is the writer and we are a
best-effort observer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from .paths import WilyPaths

EventKind = Literal["start", "done", "note"]


@dataclass
class CpEvent:
    ts: str
    actor: str
    cp: str
    event: EventKind
    note: str | None = None

    def to_json(self) -> str:
        payload = {"ts": self.ts, "actor": self.actor, "cp": self.cp, "event": self.event}
        if self.note:
            payload["note"] = self.note
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "CpEvent":
        data = json.loads(line)
        return cls(
            ts=data["ts"],
            actor=data["actor"],
            cp=data["cp"],
            event=data["event"],
            note=data.get("note"),
        )


@dataclass
class CpSummary:
    total: int
    done: int
    in_progress: int
    current_cp: str | None


def init_progress(paths: WilyPaths, task_id: str) -> None:
    target = paths.progress_jsonl(task_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
    # Empty file represents "claim recorded, no cp yet."


def append_event(paths: WilyPaths, task_id: str, event: CpEvent) -> None:
    target = paths.progress_jsonl(task_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(event.to_json() + "\n")


def read_events(paths: WilyPaths, task_id: str) -> list[CpEvent]:
    target = paths.progress_jsonl(task_id)
    if not target.exists():
        return []
    events: list[CpEvent] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(CpEvent.from_json(line))
        except (json.JSONDecodeError, KeyError):
            # Corrupt or partial line — skip.
            continue
    return events


def cp_summary(paths: WilyPaths, task_id: str) -> CpSummary:
    events = read_events(paths, task_id)
    started: dict[str, bool] = {}
    done: dict[str, bool] = {}
    for e in events:
        if e.event == "start":
            started.setdefault(e.cp, True)
        elif e.event == "done":
            done[e.cp] = True
    in_progress_set = set(started) - set(done)
    # current = most recent started-but-not-done; fall back to most recent overall.
    current: str | None = None
    for e in reversed(events):
        if e.event == "start" and e.cp in in_progress_set:
            current = e.cp
            break
    return CpSummary(
        total=len(started),
        done=len(done),
        in_progress=len(in_progress_set),
        current_cp=current,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_progress -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/progress.py plugins/wily-roadmap/tests/v3/test_progress.py
git commit -m "feat(wily): v3 progress.jsonl read/write and cp summary"
```

---

## Phase 4 — Git observation

### Task 4.1: `observation.py` — git wrappers + actor/task attribution

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/observation.py`
- Test: `plugins/wily-roadmap/tests/v3/test_observation.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_observation.py`:

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.models import Actor, Task  # noqa: E402
from wily.observation import (  # noqa: E402
    CommitInfo,
    head_sha,
    changed_files_since,
    parse_trailers,
    match_actor,
    guess_task_id,
    list_commits_since_fork,
)


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def _commit(path: Path, files: dict[str, str], message: str, author_email: str | None = None) -> str:
    for rel, content in files.items():
        full = path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    env = None
    if author_email:
        env = {"GIT_AUTHOR_EMAIL": author_email, "GIT_COMMITTER_EMAIL": author_email,
               "GIT_AUTHOR_NAME": "alt", "GIT_COMMITTER_NAME": "alt"}
        import os
        env = {**os.environ, **env}
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=path, check=True, env=env)
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True)
    return out.stdout.strip()


class GitObservationTest(unittest.TestCase):
    def test_head_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            sha = _commit(repo, {"a.txt": "x"}, "init")
            self.assertEqual(head_sha(repo), sha)

    def test_changed_files_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            base = _commit(repo, {"a.txt": "1"}, "a")
            _commit(repo, {"b.txt": "1", "a.txt": "2"}, "b")
            files = changed_files_since(repo, base)
            self.assertIn("a.txt", files)
            self.assertIn("b.txt", files)
            self.assertEqual(len(files), 2)

    def test_parse_trailers(self) -> None:
        message = "T05: foo\n\nbody line\n\nWily-Task: T05\nWily-CP: implement-parser"
        trailers = parse_trailers(message)
        self.assertEqual(trailers.get("Wily-Task"), "T05")
        self.assertEqual(trailers.get("Wily-CP"), "implement-parser")


class ActorMatchTest(unittest.TestCase):
    def test_match_actor_by_email(self) -> None:
        actors = [
            Actor(id="wily", display="Wily", git_author_emails=["kokyuhyun@goedu.kr"]),
            Actor(id="right", display="Right", git_author_emails=["right@x.com"]),
        ]
        self.assertEqual(
            match_actor(actors, email="right@x.com", name="someone"),
            actors[1],
        )

    def test_match_actor_returns_none_when_unknown(self) -> None:
        actors = [Actor(id="wily", display="Wily", git_author_emails=["a@b"])]
        self.assertIsNone(match_actor(actors, email="x@y", name="z"))


class TaskGuessTest(unittest.TestCase):
    def _t(self, tid: str, scope: list[str]) -> Task:
        return Task(id=tid, title=tid, scope=scope)

    def test_scope_match_exact(self) -> None:
        tasks = [
            self._t("T01", ["plugins/a.py"]),
            self._t("T02", ["plugins/b.py"]),
        ]
        self.assertEqual(guess_task_id(tasks, ["plugins/b.py"]), "T02")

    def test_scope_match_glob(self) -> None:
        tasks = [self._t("T01", ["plugins/wily-roadmap/scripts/wily/*.py"])]
        self.assertEqual(guess_task_id(tasks, ["plugins/wily-roadmap/scripts/wily/init.py"]), "T01")

    def test_no_match_returns_none(self) -> None:
        tasks = [self._t("T01", ["docs/*.md"])]
        self.assertIsNone(guess_task_id(tasks, ["src/x.py"]))

    def test_multi_match_returns_most_files_winner(self) -> None:
        tasks = [
            self._t("T01", ["plugins/a/*"]),
            self._t("T02", ["plugins/b/*"]),
        ]
        files = ["plugins/a/x.py", "plugins/a/y.py", "plugins/b/z.py"]
        self.assertEqual(guess_task_id(tasks, files), "T01")


class CommitListTest(unittest.TestCase):
    def test_list_commits_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            base = _commit(repo, {"a.txt": "1"}, "first\n\nWily-Task: T01")
            second = _commit(repo, {"b.txt": "1"}, "second\n\nWily-Task: T02")
            commits = list_commits_since_fork(repo, base, limit=10)
            shas = [c.sha for c in commits]
            self.assertIn(second, shas)
            self.assertNotIn(base, shas)
            second_info = next(c for c in commits if c.sha == second)
            self.assertEqual(second_info.trailers.get("Wily-Task"), "T02")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_observation -v
```

Expected: `ModuleNotFoundError: No module named 'wily.observation'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/observation.py`:

```python
"""Git observation: actor identification, commit attribution, scope drift.

wily never writes git state — only reads. All commands invoke git via
subprocess. Tests use real `git init` in temp dirs (no mocking).
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

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


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def head_sha(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").strip()


def changed_files_since(repo: Path, sha: str) -> list[str]:
    out = _git(repo, "diff", "--name-only", f"{sha}...HEAD")
    return [line for line in out.splitlines() if line.strip()]


def parse_trailers(message: str) -> dict[str, str]:
    """Extract `Key: value` trailers from the message footer.

    A trailer is a contiguous block of `Key: value` lines at the end
    of the commit message, separated by a blank line from the body.
    We accept any case-sensitive Key with non-whitespace value.
    """
    lines = message.rstrip().splitlines()
    trailer_block: list[str] = []
    for line in reversed(lines):
        if not line.strip():
            break
        if ":" not in line:
            break
        key, _, value = line.partition(":")
        if not key or " " in key or "\t" in key:
            break
        trailer_block.append(f"{key.strip()}: {value.strip()}")
    trailers: dict[str, str] = {}
    for entry in trailer_block:
        key, _, value = entry.partition(":")
        trailers[key.strip()] = value.strip()
    return trailers


def match_actor(actors: Iterable[Actor], *, email: str, name: str) -> Actor | None:
    for actor in actors:
        if actor.matches(email=email, name=name):
            return actor
    return None


def guess_task_id(tasks: Iterable[Task], changed_files: list[str]) -> str | None:
    """Pick the task whose `scope` globs match the most files, or None."""
    scores: dict[str, int] = {}
    for task in tasks:
        if not task.scope:
            continue
        count = 0
        for file in changed_files:
            for pattern in task.scope:
                if fnmatch.fnmatch(file, pattern):
                    count += 1
                    break
        if count:
            scores[task.id] = count
    if not scores:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]


def list_commits_since_fork(repo: Path, base_sha: str, *, limit: int = 50) -> list[CommitInfo]:
    """Return commits reachable from HEAD but not from base_sha.

    Output is ordered newest-first. Author email/name and trailers are
    parsed. File list per commit is fetched separately (cheap for typical
    PR-sized ranges).
    """
    format_spec = "%H%x1f%ae%x1f%an%x1f%s%x1f%b%x1e"
    out = _git(
        repo,
        "log",
        f"--max-count={limit}",
        f"--pretty=format:{format_spec}",
        f"{base_sha}..HEAD",
    )
    commits: list[CommitInfo] = []
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 5:
            continue
        sha, email, name, subject, body = parts[0], parts[1], parts[2], parts[3], parts[4]
        message = f"{subject}\n\n{body}" if body else subject
        trailers = parse_trailers(message)
        files_out = _git(repo, "show", "--name-only", "--pretty=format:", sha)
        files = [line for line in files_out.splitlines() if line.strip()]
        commits.append(
            CommitInfo(
                sha=sha,
                author_email=email,
                author_name=name,
                subject=subject,
                body=body,
                trailers=trailers,
                files=files,
            )
        )
    return commits
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_observation -v
```

Expected: 10 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/observation.py plugins/wily-roadmap/tests/v3/test_observation.py
git commit -m "feat(wily): v3 git observation, trailer parsing, scope guessing"
```

---

## Phase 5 — CLI scaffold

### Task 5.1: `cli/_common.py` + entry dispatcher

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/cli/_common.py`
- Create: `plugins/wily-roadmap/scripts/wily/cli/__main__.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_dispatch.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_dispatch.py`:

```python
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli._common import (  # noqa: E402
    EXIT_OK,
    EXIT_FAILURE,
    EXIT_USAGE,
    EXIT_TRANSITION,
    emit_json,
    emit_text,
)


class ExitCodeTest(unittest.TestCase):
    def test_exit_constants(self) -> None:
        self.assertEqual(EXIT_OK, 0)
        self.assertEqual(EXIT_FAILURE, 1)
        self.assertEqual(EXIT_USAGE, 2)
        self.assertEqual(EXIT_TRANSITION, 3)


class EmitTest(unittest.TestCase):
    def test_emit_text(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit_text("hello")
        self.assertEqual(buf.getvalue().rstrip(), "hello")

    def test_emit_json(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit_json({"a": 1, "b": [2, 3]})
        import json
        self.assertEqual(json.loads(buf.getvalue()), {"a": 1, "b": [2, 3]})


class DispatchTest(unittest.TestCase):
    def test_unknown_subcommand_returns_usage(self) -> None:
        from wily.cli.__main__ import main
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = main(["nonexistent"])
        self.assertEqual(rc, EXIT_USAGE)
        self.assertIn("nonexistent", stderr.getvalue())

    def test_no_args_prints_help(self) -> None:
        from wily.cli.__main__ import main
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = main([])
        self.assertEqual(rc, EXIT_USAGE)
        # Help mentions some core commands
        text = stdout.getvalue() + stderr.getvalue()
        for cmd in ("init", "next", "claim", "go", "done", "block", "replan", "land", "watch", "status"):
            self.assertIn(cmd, text)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_dispatch -v
```

Expected: import error on `wily.cli._common` or `wily.cli.__main__`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/_common.py`:

```python
"""Shared CLI primitives: exit codes, output helpers, common arg parsing."""

from __future__ import annotations

import json as _json
import sys
from typing import Any

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_TRANSITION = 3


def emit_text(message: str) -> None:
    print(message)


def emit_json(payload: Any) -> None:
    _json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def emit_error(message: str) -> None:
    print(message, file=sys.stderr)


COMMANDS = (
    "init",
    "next",
    "claim",
    "go",
    "done",
    "block",
    "replan",
    "land",
    "watch",
    "status",
)


def print_help() -> None:
    emit_text("wily v3 — Project + flat goal-sized Task manager")
    emit_text("")
    emit_text("Usage: wily <command> [args]")
    emit_text("")
    emit_text("Commands:")
    for cmd in COMMANDS:
        emit_text(f"  {cmd}")
    emit_text("")
    emit_text("See `plugins/wily-roadmap/skills/wily-<command>/SKILL.md` for details.")
```

`plugins/wily-roadmap/scripts/wily/cli/__main__.py`:

```python
"""Entry dispatch for the wily v3 CLI.

Called from `plugins/wily-roadmap/scripts/wily.py` (the legacy launcher
file, which becomes a thin shim once v3 lands). Exit code convention:
  0  success
  1  command-level failure (git, IO, etc.)
  2  usage error (unknown subcommand, bad args)
  3  state transition rejected
"""

from __future__ import annotations

import sys
from typing import Callable

from . import _common


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        _common.print_help()
        return _common.EXIT_USAGE if not args else _common.EXIT_OK

    cmd, rest = args[0], args[1:]
    handler = _load_handler(cmd)
    if handler is None:
        _common.emit_error(f"unknown command: {cmd!r}")
        _common.emit_error(f"available: {', '.join(_common.COMMANDS)}")
        return _common.EXIT_USAGE
    return handler(rest)


def _load_handler(cmd: str) -> Callable[[list[str]], int] | None:
    if cmd not in _common.COMMANDS:
        return None
    # Import lazily so unrelated commands don't slow startup.
    module = __import__(f"wily.cli.{cmd}", fromlist=["main"])
    return getattr(module, "main", None)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

The dispatch test imports `wily.cli.init`, `wily.cli.next`, etc. — they don't exist yet. Add stub modules so dispatch can resolve:

```bash
for cmd in init next claim go done block replan land watch status; do
  cat > "plugins/wily-roadmap/scripts/wily/cli/${cmd}.py" <<EOF
"""Stub for \`wily ${cmd}\` — replaced in later tasks."""
from . import _common


def main(args: list[str]) -> int:
    _common.emit_error("not implemented yet")
    return _common.EXIT_FAILURE
EOF
done
```

Then:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_dispatch -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/ plugins/wily-roadmap/tests/v3/test_cli_dispatch.py
git commit -m "feat(wily): v3 cli dispatch and command stubs"
```

---

## Phase 6 — Lifecycle commands

### Task 6.1: `cli/next.py` — find next ready task

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/next.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_next.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_next.py`:

```python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import next as next_cmd  # noqa: E402
from wily.config import save_tasks, save_actors  # noqa: E402
from wily.models import Task, TaskStatus, Actor  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _scaffold(tmp: Path) -> WilyPaths:
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily")])
    return paths


class NextCommandTest(unittest.TestCase):
    def test_picks_first_ready_with_satisfied_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="a", status=TaskStatus.DONE),
                Task(id="T02", title="b", status=TaskStatus.READY, depends_on=["T01"]),
                Task(id="T03", title="c", status=TaskStatus.READY, depends_on=["T02"]),
            ])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = next_cmd.main([])
            self.assertEqual(rc, 0)
            self.assertIn("T02", buf.getvalue())
            self.assertNotIn("T03", buf.getvalue())

    def test_no_ready_returns_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="a", status=TaskStatus.DONE),
            ])
            with chdir(tmp):
                rc = next_cmd.main([])
            self.assertEqual(rc, 1)

    def test_mine_filter_only_assignee_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="for right", assignee="right"),
                Task(id="T02", title="for wily", assignee="wily"),
            ])
            buf = io.StringIO()
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            subprocess.run(["git", "config", "user.email", "kokyuhyun@goedu.kr"], cwd=tmp, check=True)
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["kokyuhyun@goedu.kr"])])
            with chdir(tmp), redirect_stdout(buf):
                rc = next_cmd.main(["--mine"])
            self.assertEqual(rc, 0)
            self.assertIn("T02", buf.getvalue())
            self.assertNotIn("T01", buf.getvalue())

    def test_json_output_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = next_cmd.main(["--json"])
            self.assertEqual(rc, 0)
            import json
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["id"], "T01")
            self.assertEqual(payload["title"], "x")
            self.assertEqual(payload["status"], "ready")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_next -v
```

Expected: tests fail because stub returns "not implemented".

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/next.py`:

```python
"""`wily next` — find the next ready task with satisfied dependencies."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import load_actors, load_tasks
from ..models import Actor, Task, TaskStatus
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from . import _common


def main(args: list[str]) -> int:
    mine = "--mine" in args
    as_json = "--json" in args
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE

    paths = WilyPaths(root)
    _project_title, tasks = load_tasks(paths)
    actors = load_actors(paths)
    me: Actor | None = _resolve_me(root, actors) if mine else None
    candidate = _next_task(tasks, mine_actor_id=me.id if me else None)
    if candidate is None:
        _common.emit_error("no ready task with satisfied dependencies")
        return _common.EXIT_FAILURE
    if as_json:
        _common.emit_json(candidate.to_dict())
    else:
        deps = ",".join(candidate.depends_on) if candidate.depends_on else "-"
        _common.emit_text(
            f"{candidate.id} ready  {candidate.title!r}  "
            f"assignee={candidate.assignee or '-'}  depends_on=[{deps}]"
        )
    return _common.EXIT_OK


def _next_task(tasks: list[Task], *, mine_actor_id: str | None) -> Task | None:
    done_ids = {t.id for t in tasks if t.status == TaskStatus.DONE}
    for t in tasks:
        if t.status != TaskStatus.READY:
            continue
        if mine_actor_id and t.assignee and t.assignee != mine_actor_id:
            continue
        if all(dep in done_ids for dep in t.depends_on):
            return t
    return None


def _resolve_me(repo: Path, actors: list[Actor]) -> Actor | None:
    try:
        email = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        email = ""
    for actor in actors:
        if email and email.lower() in {e.lower() for e in actor.git_author_emails}:
            return actor
    return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_next -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/next.py plugins/wily-roadmap/tests/v3/test_cli_next.py
git commit -m "feat(wily): wily next picks first ready task with satisfied deps"
```

---

### Task 6.2: `cli/claim.py` — claim a task

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/claim.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_claim.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_claim.py`:

```python
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import claim as claim_cmd  # noqa: E402
from wily.config import load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _repo(tmp: Path) -> WilyPaths:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "kokyuhyun@goedu.kr"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    (tmp / "seed.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["kokyuhyun@goedu.kr"])])
    return paths


class ClaimCommandTest(unittest.TestCase):
    def test_claim_ready_sets_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = claim_cmd.main(["T01"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.IN_PROGRESS)
            self.assertEqual(tasks[0].actor, "wily")
            self.assertTrue(tasks[0].claim_sha)
            self.assertTrue(tasks[0].claim_at)
            self.assertTrue(paths.progress_jsonl("T01").exists())

    def test_claim_blocked_clears_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.BLOCKED, blocker="net"),
            ])
            with chdir(tmp):
                rc = claim_cmd.main(["T01"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertIsNone(tasks[0].blocker)

    def test_claim_in_progress_rejects_with_exit_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="right"),
            ])
            stderr = io.StringIO()
            with chdir(tmp), redirect_stderr(stderr):
                rc = claim_cmd.main(["T01"])
            self.assertEqual(rc, 3)
            self.assertIn("right", stderr.getvalue())

    def test_claim_force_steals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="right"),
            ])
            with chdir(tmp):
                rc = claim_cmd.main(["T01", "--force"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].actor, "wily")

    def test_claim_missing_actor_mapping_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_actors(paths, [Actor(id="right", display="Right", git_author_emails=["x@y"])])
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            stderr = io.StringIO()
            with chdir(tmp), redirect_stderr(stderr):
                rc = claim_cmd.main(["T01"])
            self.assertEqual(rc, 1)
            self.assertIn("no actor", stderr.getvalue().lower())
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_claim -v
```

Expected: 5 failures (stub returns "not implemented").

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/claim.py`:

```python
"""`wily claim <id>` — take a task to in_progress."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..config import load_actors, load_tasks, save_tasks
from ..models import Actor, TaskStatus
from ..observation import head_sha
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from ..progress import init_progress
from ..transitions import apply_claim, TransitionError
from . import _common


def main(args: list[str]) -> int:
    force = "--force" in args
    positional = [a for a in args if not a.startswith("--")]
    if len(positional) != 1:
        _common.emit_error("usage: wily claim <task-id> [--force]")
        return _common.EXIT_USAGE
    task_id = positional[0]

    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    project_title, tasks = load_tasks(paths)
    actors = load_actors(paths)

    me = _resolve_me(root, actors)
    if me is None:
        _common.emit_error(
            "no actor matches git config user.email; "
            "run `wily init` or update actors.yaml via replan."
        )
        return _common.EXIT_FAILURE

    target = next((t for t in tasks if t.id == task_id), None)
    if target is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE

    try:
        sha = head_sha(root)
    except subprocess.CalledProcessError as exc:
        _common.emit_error(f"git HEAD failed: {exc}")
        return _common.EXIT_FAILURE

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        updated = apply_claim(target, actor=me.id, sha=sha, at=now, force=force)
    except TransitionError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_TRANSITION

    if target.assignee and target.assignee != me.id:
        _common.emit_text(
            f"warning: task assignee is {target.assignee!r}, you are {me.id!r}"
        )

    new_tasks = [updated if t.id == task_id else t for t in tasks]
    save_tasks(paths, project_title, new_tasks)
    init_progress(paths, task_id)

    _common.emit_text(f"{task_id}: {target.status.value} -> in_progress")
    _common.emit_text(f"actor: {me.id} ({_first_or_blank(me.git_author_emails)})")
    _common.emit_text(f"claim_sha: {sha[:7]}")
    _common.emit_text(f"progress.jsonl initialized: {paths.progress_jsonl(task_id).relative_to(root)}")
    return _common.EXIT_OK


def _resolve_me(repo: Path, actors: list[Actor]) -> Actor | None:
    try:
        email = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        email = ""
    try:
        name = subprocess.run(
            ["git", "config", "user.name"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        name = ""
    for actor in actors:
        if actor.matches(email=email, name=name):
            return actor
    return None


def _first_or_blank(items: list[str]) -> str:
    return items[0] if items else "-"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_claim -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/claim.py plugins/wily-roadmap/tests/v3/test_cli_claim.py
git commit -m "feat(wily): wily claim — task entry transition"
```

---

### Task 6.3: `cli/go.py` — emit goal text for custom-workflow

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/go.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_go.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_go.py`:

```python
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import go as go_cmd  # noqa: E402
from wily.config import save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _scaffold(tmp: Path) -> WilyPaths:
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily")])
    return paths


class GoCommandTest(unittest.TestCase):
    def test_text_output_contains_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(
                    id="T05",
                    title="Lifecycle CLI",
                    intent="claim/go/done flow",
                    acceptance="status transitions work",
                    scope=["plugins/x.py"],
                    status=TaskStatus.IN_PROGRESS,
                    actor="wily",
                ),
            ])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = go_cmd.main(["T05"])
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("Wily Task T05", out)
            self.assertIn("## Intent", out)
            self.assertIn("claim/go/done flow", out)
            self.assertIn("## Acceptance", out)
            self.assertIn("status transitions work", out)
            self.assertIn("## Scope", out)
            self.assertIn("plugins/x.py", out)
            self.assertIn("## Progress", out)
            self.assertIn(".wily/tasks/T05/progress.jsonl", out)
            self.assertIn("Wily-Task: T05", out)

    def test_go_rejects_when_not_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = go_cmd.main(["T01"])
            self.assertEqual(rc, 3)

    def test_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", intent="a", acceptance="b", scope=["s"],
                     status=TaskStatus.IN_PROGRESS, actor="wily"),
            ])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = go_cmd.main(["T01", "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["task_id"], "T01")
            self.assertIn("goal_text", payload)
            self.assertIn("Wily-Task: T01", payload["goal_text"])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_go -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/go.py`:

```python
"""`wily go <id>` — emit the goal text to hand to custom-workflow."""

from __future__ import annotations

from pathlib import Path

from ..config import load_tasks
from ..models import TaskStatus
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from . import _common


def main(args: list[str]) -> int:
    as_json = "--json" in args
    positional = [a for a in args if not a.startswith("--")]
    if len(positional) != 1:
        _common.emit_error("usage: wily go <task-id>")
        return _common.EXIT_USAGE
    task_id = positional[0]

    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    _project_title, tasks = load_tasks(paths)
    target = next((t for t in tasks if t.id == task_id), None)
    if target is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    if target.status != TaskStatus.IN_PROGRESS:
        _common.emit_error(
            f"{task_id} is {target.status.value}; claim it first with `wily claim {task_id}`."
        )
        return _common.EXIT_TRANSITION

    acceptance = target.acceptance
    if not acceptance and target.acceptance_file:
        acc_path = root / target.acceptance_file
        if acc_path.exists():
            acceptance = acc_path.read_text(encoding="utf-8")

    progress_path = paths.progress_jsonl(target.id).relative_to(root)
    scope = "\n".join(f"- {s}" for s in target.scope) if target.scope else "(no scope declared)"

    goal_text = (
        f"# Wily Task {target.id}: {target.title}\n\n"
        f"## Intent\n{target.intent or '(no intent)'}\n\n"
        f"## Acceptance\n{acceptance or '(no acceptance)'}\n\n"
        f"## Scope (allowed change paths)\n{scope}\n\n"
        f"## Progress recording\n"
        f"- {progress_path} (append one JSON line per cp start/done)\n"
        f"- commit trailer: Wily-Task: {target.id}, Wily-CP: <cp-name>\n\n"
        f"## After cw finishes\n"
        f"- Compare result against each acceptance item.\n"
        f"- Report scope drift if any file outside the Scope list was modified.\n"
        f"- Hand back to Wily 박사 for `wily done {target.id}`.\n"
    )

    if as_json:
        _common.emit_json({
            "task_id": target.id,
            "goal_text": goal_text,
            "progress_jsonl": str(progress_path),
        })
    else:
        _common.emit_text(
            f"==== copy below into custom-workflow-skillset:plan-goal-runner ====\n"
            f"{goal_text}"
            f"===================================================================="
        )
    return _common.EXIT_OK
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_go -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/go.py plugins/wily-roadmap/tests/v3/test_cli_go.py
git commit -m "feat(wily): wily go emits goal text for custom-workflow"
```

---

### Task 6.4: `cli/done.py` — mark done + write result.md

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/done.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_done.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_done.py`:

```python
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import done as done_cmd  # noqa: E402
from wily.config import load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _repo(tmp: Path) -> tuple[WilyPaths, str]:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "kokyuhyun@goedu.kr"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    (tmp / "a.txt").write_text("1")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp, capture_output=True, text=True, check=True
    ).stdout.strip()
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["kokyuhyun@goedu.kr"])])
    return paths, sha


class DoneCommandTest(unittest.TestCase):
    def test_done_writes_result_md_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, sha = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="wily",
                     claim_sha=sha, claim_at="2026-05-18T11:00:00Z"),
            ])
            (Path(tmp) / "a.txt").write_text("2")
            subprocess.run(["git", "add", "."], cwd=tmp, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "work"], cwd=tmp, check=True)
            with chdir(tmp):
                rc = done_cmd.main(["T01"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.DONE)
            self.assertTrue(tasks[0].done_at)
            self.assertTrue(paths.result_md("T01").exists())
            result_text = paths.result_md("T01").read_text(encoding="utf-8")
            self.assertIn("T01: x — done", result_text)
            self.assertIn("changed files: 1", result_text)

    def test_done_with_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, sha = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="wily",
                     claim_sha=sha, claim_at="2026-05-18T11:00:00Z"),
            ])
            with chdir(tmp):
                rc = done_cmd.main(["T01", "--note", "verified locally"])
            self.assertEqual(rc, 0)
            result_text = paths.result_md("T01").read_text(encoding="utf-8")
            self.assertIn("verified locally", result_text)

    def test_done_rejects_ready_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, _ = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = done_cmd.main(["T01"])
            self.assertEqual(rc, 3)

    def test_done_observed_records_external_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, sha = _repo(Path(tmp))
            save_actors(paths, [
                Actor(id="wily", display="Wily", git_author_emails=["kokyuhyun@goedu.kr"]),
                Actor(id="right", display="Right", git_author_emails=["right@x.com"]),
            ])
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="right",
                     claim_sha=sha, claim_at="2026-05-18T11:00:00Z"),
            ])
            with chdir(tmp):
                rc = done_cmd.main(["T01", "--observed"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].actor, "right")
            self.assertEqual(tasks[0].status, TaskStatus.DONE)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_done -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/done.py`:

```python
"""`wily done <id>` — mark a claimed task done and write result.md."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..config import load_tasks, save_tasks
from ..models import TaskStatus
from ..observation import changed_files_since, head_sha
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from ..progress import cp_summary
from ..transitions import apply_done, TransitionError
from . import _common


def main(args: list[str]) -> int:
    force = "--force" in args
    observed = "--observed" in args
    note = _extract_value(args, "--note")
    positional = [
        a for a in args if not a.startswith("--") and not _is_value_for(args, a)
    ]
    if len(positional) != 1:
        _common.emit_error("usage: wily done <task-id> [--note <text>] [--observed] [--force]")
        return _common.EXIT_USAGE
    task_id = positional[0]

    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    project_title, tasks = load_tasks(paths)
    target = next((t for t in tasks if t.id == task_id), None)
    if target is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        updated = apply_done(target, at=now, force=force)
    except TransitionError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_TRANSITION

    # Stats for result.md
    try:
        current_sha = head_sha(root)
    except subprocess.CalledProcessError:
        current_sha = "?"
    changed: list[str] = []
    if target.claim_sha and target.claim_sha != "?":
        try:
            changed = changed_files_since(root, target.claim_sha)
        except subprocess.CalledProcessError:
            changed = []
    summary = cp_summary(paths, task_id)

    paths.task_dir(task_id).mkdir(parents=True, exist_ok=True)
    paths.result_md(task_id).write_text(
        _format_result_md(
            target,
            done_at=now,
            current_sha=current_sha,
            changed=changed,
            cp_total=summary.total,
            cp_done=summary.done,
            note=note,
            observed=observed,
        ),
        encoding="utf-8",
    )

    new_tasks = [updated if t.id == task_id else t for t in tasks]
    save_tasks(paths, project_title, new_tasks)

    _common.emit_text(f"{task_id}: in_progress -> done")
    _common.emit_text(
        f"result.md written (changed {len(changed)} files, "
        f"{summary.done}/{summary.total} cp, "
        f"commit range {(target.claim_sha or '?')[:7]}..{current_sha[:7]})"
    )
    return _common.EXIT_OK


def _extract_value(args: list[str], flag: str) -> str | None:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None


def _is_value_for(args: list[str], token: str) -> bool:
    for flag in ("--note",):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args) and args[idx + 1] == token:
                return True
    return False


def _format_result_md(
    task,
    *,
    done_at: str,
    current_sha: str,
    changed: list[str],
    cp_total: int,
    cp_done: int,
    note: str | None,
    observed: bool,
) -> str:
    range_str = f"{(task.claim_sha or '?')[:7]}..{current_sha[:7]}"
    drift = "(no scope drift check — scope empty)" if not task.scope else _drift_summary(task.scope, changed)
    lines = [
        f"# {task.id}: {task.title} — done",
        "",
        f"- actor: {task.actor or '-'}{' (observed)' if observed else ''}",
        f"- claim: {task.claim_at or '-'} (sha {(task.claim_sha or '-')[:7]})",
        f"- done: {done_at}",
        f"- commit range: {range_str}",
        f"- changed files: {len(changed)}",
        f"- cp count: {cp_done}/{cp_total}",
        f"- scope drift: {drift}",
    ]
    if note:
        lines.append(f"- note: {note}")
    lines.append("")
    return "\n".join(lines)


def _drift_summary(scope: list[str], changed: list[str]) -> str:
    import fnmatch
    outside = [
        f for f in changed
        if not any(fnmatch.fnmatch(f, pat) for pat in scope)
    ]
    if not outside:
        return "0 files outside scope"
    return f"{len(outside)} files outside scope (first: {outside[0]})"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_done -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/done.py plugins/wily-roadmap/tests/v3/test_cli_done.py
git commit -m "feat(wily): wily done flips status and writes result.md"
```

---

### Task 6.5: `cli/block.py` — block with reason

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/block.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_block.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_block.py`:

```python
import sys
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import block as block_cmd  # noqa: E402
from wily.config import load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _scaffold(tmp: Path) -> WilyPaths:
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily")])
    return paths


class BlockCommandTest(unittest.TestCase):
    def test_block_ready_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = block_cmd.main(["T01", "needs upstream fix"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.BLOCKED)
            self.assertEqual(tasks[0].blocker, "needs upstream fix")

    def test_block_in_progress_keeps_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.IN_PROGRESS, actor="wily"),
            ])
            with chdir(tmp):
                rc = block_cmd.main(["T01", "blocked on cw"])
            self.assertEqual(rc, 0)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.BLOCKED)
            self.assertEqual(tasks[0].actor, "wily")

    def test_block_done_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x", status=TaskStatus.DONE)])
            with chdir(tmp):
                rc = block_cmd.main(["T01", "x"])
            self.assertEqual(rc, 3)

    def test_block_missing_reason_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = block_cmd.main(["T01"])
            self.assertEqual(rc, 2)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_block -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/block.py`:

```python
"""`wily block <id> <reason>` — record a blocker on a task."""

from __future__ import annotations

from pathlib import Path

from ..config import load_tasks, save_tasks
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from ..transitions import apply_block, TransitionError
from . import _common


def main(args: list[str]) -> int:
    if len(args) < 2:
        _common.emit_error("usage: wily block <task-id> <reason...>")
        return _common.EXIT_USAGE
    task_id, *reason_parts = args
    reason = " ".join(reason_parts).strip()
    if not reason:
        _common.emit_error("blocker reason required")
        return _common.EXIT_USAGE

    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    project_title, tasks = load_tasks(paths)
    target = next((t for t in tasks if t.id == task_id), None)
    if target is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE

    try:
        updated = apply_block(target, reason=reason)
    except TransitionError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_TRANSITION

    new_tasks = [updated if t.id == task_id else t for t in tasks]
    save_tasks(paths, project_title, new_tasks)

    _common.emit_text(f"{task_id}: {target.status.value} -> blocked")
    _common.emit_text(f"blocker: {reason}")
    return _common.EXIT_OK
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_block -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/block.py plugins/wily-roadmap/tests/v3/test_cli_block.py
git commit -m "feat(wily): wily block records blocker on task"
```

---

## Phase 7 — Status + watch

### Task 7.1: `ui/watch_render.py` — pure renderer

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
- Test: `plugins/wily-roadmap/tests/v3/test_watch_render.py`

Renderer is pure (Tasks + Actors + observed commits → text). Keeps the polling loop trivial and the renderer fully testable without timing.

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_watch_render.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.observation import CommitInfo  # noqa: E402
from wily.progress import CpSummary  # noqa: E402
from wily.ui.watch_render import (  # noqa: E402
    WatchRow,
    render_watch,
    build_rows,
)


class BuildRowsTest(unittest.TestCase):
    def test_done_task_row(self) -> None:
        tasks = [Task(id="T01", title="a", status=TaskStatus.DONE, actor="wily")]
        rows = build_rows(tasks, actors=[Actor(id="wily", display="Wily")],
                          observed_commits=[], cp_summaries={})
        self.assertEqual(rows[0].glyph, "✓ done")
        self.assertEqual(rows[0].task_id, "T01")
        self.assertEqual(rows[0].actor_display, "wily")

    def test_in_progress_with_cp(self) -> None:
        tasks = [Task(id="T03", title="c", status=TaskStatus.IN_PROGRESS, actor="wily")]
        cp = {"T03": CpSummary(total=5, done=3, in_progress=1, current_cp="implement-parser")}
        rows = build_rows(tasks, actors=[Actor(id="wily", display="Wily")],
                          observed_commits=[], cp_summaries=cp)
        self.assertIn("3/5 cp", rows[0].cp_gauge)
        self.assertIn("implement-parser", rows[0].cp_gauge)

    def test_observed_commit_row(self) -> None:
        actors = [
            Actor(id="wily", display="Wily", git_author_emails=["w@x"]),
            Actor(id="right", display="Right", git_author_emails=["r@x"]),
        ]
        tasks = [
            Task(id="T05", title="a", scope=["plugins/right/*"]),
        ]
        commits = [
            CommitInfo(
                sha="abc1234567",
                author_email="r@x",
                author_name="right",
                subject="fix",
                body="",
                trailers={},
                files=["plugins/right/x.py"],
            )
        ]
        rows = build_rows(tasks, actors=actors, observed_commits=commits, cp_summaries={})
        observed = [r for r in rows if r.glyph == "⏵ observed"]
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0].actor_display, "right")
        self.assertIn("T05", observed[0].guessed_text or "")


class RenderWatchTest(unittest.TestCase):
    def test_render_includes_project_title_and_glyphs(self) -> None:
        tasks = [
            Task(id="T01", title="a", status=TaskStatus.DONE, actor="wily"),
            Task(id="T02", title="b", status=TaskStatus.IN_PROGRESS, actor="wily"),
            Task(id="T03", title="c"),
        ]
        text = render_watch(
            project_title="redesign",
            tasks=tasks,
            actors=[Actor(id="wily", display="Wily")],
            observed_commits=[],
            cp_summaries={},
            mode="solo",
        )
        self.assertIn("redesign", text)
        self.assertIn("✓ done", text)
        self.assertIn("▶ in_progress", text)
        self.assertIn("ready", text)
        self.assertIn("T01", text)
        self.assertIn("T02", text)
        self.assertIn("T03", text)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_watch_render -v
```

Expected: `ModuleNotFoundError: No module named 'wily.ui.watch_render'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/ui/watch_render.py`:

```python
"""Pure renderer for `wily watch` and `wily status`.

Takes parsed inputs (Tasks, Actors, observed commits, cp summaries) and
returns text. Polling and git work happens in the CLI layer.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

from ..models import Actor, Task, TaskStatus
from ..observation import CommitInfo
from ..progress import CpSummary

GLYPHS = {
    TaskStatus.DONE: "✓ done",
    TaskStatus.IN_PROGRESS: "▶ in_progress",
    TaskStatus.READY: "ready",
    TaskStatus.BLOCKED: "blocked",
}


@dataclass
class WatchRow:
    task_id: str
    glyph: str
    actor_display: str
    title: str
    cp_gauge: str = ""
    blocker: str | None = None
    guessed_text: str | None = None


def build_rows(
    tasks: list[Task],
    *,
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
) -> list[WatchRow]:
    actor_by_id = {a.id: a for a in actors}
    rows: list[WatchRow] = []
    for t in tasks:
        actor_display = (
            actor_by_id[t.actor].id if t.actor and t.actor in actor_by_id
            else (t.actor or "-")
        )
        gauge = ""
        cp = cp_summaries.get(t.id)
        if cp and (cp.total or cp.done):
            blocks = "▓" * cp.done + "░" * (cp.total - cp.done)
            current = f"  cp:{cp.current_cp}" if cp.current_cp else ""
            gauge = f"[{blocks} {cp.done}/{cp.total} cp]{current}"
        rows.append(WatchRow(
            task_id=t.id,
            glyph=GLYPHS[t.status],
            actor_display=actor_display,
            title=t.title,
            cp_gauge=gauge,
            blocker=t.blocker,
        ))

    for commit in observed_commits:
        actor = _match_actor(actors, commit.author_email, commit.author_name)
        # Skip commits we can already attribute to a known wily-managed task via trailer.
        if commit.trailers.get("Wily-Task"):
            continue
        guessed = _guess_task(tasks, commit.files)
        rows.append(WatchRow(
            task_id="-",
            glyph="⏵ observed",
            actor_display=(actor.id if actor else "unknown"),
            title=commit.subject,
            guessed_text=(f"guessed task: {guessed} (no trailer)" if guessed else "no scope match"),
        ))
    return rows


def render_watch(
    *,
    project_title: str,
    tasks: list[Task],
    actors: list[Actor],
    observed_commits: list[CommitInfo],
    cp_summaries: dict[str, CpSummary],
    mode: str,
) -> str:
    lines: list[str] = []
    lines.append(f"Project: {project_title or '(untitled)'}")
    lines.append("─" * 69)
    rows = build_rows(
        tasks,
        actors=actors,
        observed_commits=observed_commits,
        cp_summaries=cp_summaries,
    )
    for row in rows:
        primary = (
            f"{row.task_id:<5} "
            f"{row.glyph:<14} "
            f"{row.actor_display:<6} "
            f"{row.title}"
        )
        if row.cp_gauge:
            primary += "  " + row.cp_gauge
        lines.append(primary)
        if row.blocker:
            lines.append(f"     blocker: {row.blocker}")
        if row.guessed_text:
            lines.append(f"     └ {row.guessed_text}")
    lines.append("")
    actor_summary = "  ·  ".join(
        f"{a.id} {a.git_author_emails[0]}" if a.git_author_emails else a.id
        for a in actors
    )
    lines.append(f"actors: {actor_summary}")
    lines.append(f"mode: {mode}")
    return "\n".join(lines)


def _match_actor(actors: list[Actor], email: str, name: str) -> Actor | None:
    for a in actors:
        if a.matches(email=email, name=name):
            return a
    return None


def _guess_task(tasks: list[Task], files: list[str]) -> str | None:
    scores: dict[str, int] = {}
    for t in tasks:
        if not t.scope:
            continue
        hit = sum(
            1 for f in files
            if any(fnmatch.fnmatch(f, pat) for pat in t.scope)
        )
        if hit:
            scores[t.id] = hit
    if not scores:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_watch_render -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/ui/watch_render.py plugins/wily-roadmap/tests/v3/test_watch_render.py
git commit -m "feat(wily): v3 watch renderer with cp gauge and observed rows"
```

---

### Task 7.2: `cli/status.py` — single snapshot

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/status.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_status.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_status.py`:

```python
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import status as status_cmd  # noqa: E402
from wily.config import save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _repo(tmp: Path) -> WilyPaths:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "w@x"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    (tmp / "a.txt").write_text("1")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["w@x"])])
    return paths


class StatusCommandTest(unittest.TestCase):
    def test_all_done_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x", status=TaskStatus.DONE)])
            with chdir(tmp):
                rc = status_cmd.main([])
            self.assertEqual(rc, 0)

    def test_ready_or_in_progress_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = status_cmd.main([])
            self.assertEqual(rc, 1)

    def test_blocked_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.BLOCKED, blocker="net"),
            ])
            with chdir(tmp):
                rc = status_cmd.main([])
            self.assertEqual(rc, 2)

    def test_json_payload_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="x", status=TaskStatus.DONE),
                Task(id="T02", title="y"),
            ])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                status_cmd.main(["--json"])
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["project_title"], "p")
            self.assertEqual(payload["mode"], "solo")
            ids = [t["id"] for t in payload["tasks"]]
            self.assertEqual(ids, ["T01", "T02"])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_status -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/status.py`:

```python
"""`wily status` — single snapshot of project + tasks.

Exit code reflects health:
  0  all tasks done
  1  ready/in_progress tasks remain
  2  one or more blocked tasks
"""

from __future__ import annotations

from pathlib import Path

from ..config import load_actors, load_tasks, repo_mode
from ..models import TaskStatus
from ..observation import head_sha, list_commits_since_fork
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from ..progress import cp_summary
from ..ui.watch_render import render_watch
from . import _common


def main(args: list[str]) -> int:
    as_json = "--json" in args
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE

    paths = WilyPaths(root)
    project_title, tasks = load_tasks(paths)
    actors = load_actors(paths)
    mode = repo_mode(paths)

    cp_summaries = {t.id: cp_summary(paths, t.id) for t in tasks}
    observed: list = []  # commit observation deferred to watch loop; status is task-state focused.

    # If any actor exists, optionally fetch observed commits from default branch.
    # Status keeps it cheap: skip git observation if HEAD is unreachable or repo absent.
    try:
        head_sha(root)
        # For status we look at the last 20 commits as a quick sanity check.
        # Empty observation is fine — status focuses on task state.
        observed = list_commits_since_fork(root, _initial_commit_or_head(root), limit=20)
    except Exception:
        observed = []

    if as_json:
        _common.emit_json({
            "project_title": project_title,
            "mode": mode,
            "tasks": [t.to_dict() for t in tasks],
            "cp": {tid: cp_summaries[tid].__dict__ for tid in cp_summaries},
            "actors": [a.to_dict() | {"id": a.id} for a in actors],
        })
    else:
        text = render_watch(
            project_title=project_title,
            tasks=tasks,
            actors=actors,
            observed_commits=observed,
            cp_summaries=cp_summaries,
            mode=mode,
        )
        _common.emit_text(text)

    if any(t.status == TaskStatus.BLOCKED for t in tasks):
        return 2
    if any(t.status in {TaskStatus.READY, TaskStatus.IN_PROGRESS} for t in tasks):
        return 1
    return 0


def _initial_commit_or_head(repo: Path) -> str:
    """Return the first commit reachable from HEAD (so observation list isn't empty)."""
    import subprocess
    try:
        return subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip().splitlines()[0]
    except (subprocess.CalledProcessError, IndexError):
        return head_sha(repo)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_status -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/status.py plugins/wily-roadmap/tests/v3/test_cli_status.py
git commit -m "feat(wily): wily status snapshot with health-coded exit"
```

---

### Task 7.3: `cli/watch.py` — polling loop around the renderer

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/watch.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_watch.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_watch.py`:

```python
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import watch as watch_cmd  # noqa: E402
from wily.config import save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _repo(tmp: Path) -> WilyPaths:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "w@x"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    (tmp / "a.txt").write_text("1")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["w@x"])])
    return paths


class WatchCommandTest(unittest.TestCase):
    def test_once_prints_and_returns_status_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x", status=TaskStatus.DONE)])
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = watch_cmd.main(["--once"])
            self.assertEqual(rc, 0)
            self.assertIn("T01", buf.getvalue())

    def test_interval_rejects_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x")])
            with chdir(tmp):
                rc = watch_cmd.main(["--once", "--interval", "0"])
            self.assertEqual(rc, 2)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_watch -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/watch.py`:

```python
"""`wily watch` — polling render loop around the same view as status."""

from __future__ import annotations

import time
from pathlib import Path

from . import _common
from .status import main as status_main


def main(args: list[str]) -> int:
    once = "--once" in args
    interval = _extract_interval(args)
    if interval is None:
        return _common.EXIT_USAGE
    args_for_status = [a for a in args if a not in {"--once"} and not a.startswith("--interval")]
    # Drop the interval value if it was separate
    skip_next = False
    cleaned: list[str] = []
    for a in args_for_status:
        if skip_next:
            skip_next = False
            continue
        if a == "--interval":
            skip_next = True
            continue
        cleaned.append(a)
    args_for_status = cleaned

    while True:
        rc = status_main(args_for_status)
        if once:
            return rc
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            return _common.EXIT_OK


def _extract_interval(args: list[str]) -> float | None:
    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 >= len(args):
            _common.emit_error("--interval requires a value")
            return None
        try:
            value = float(args[idx + 1])
        except ValueError:
            _common.emit_error("--interval value must be a number")
            return None
        if value <= 0:
            _common.emit_error("--interval must be positive")
            return None
        return value
    return 2.0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_watch -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/watch.py plugins/wily-roadmap/tests/v3/test_cli_watch.py
git commit -m "feat(wily): wily watch loop around status renderer"
```

---

## Phase 8 — Land + Replan

### Task 8.1: `cli/land.py` — commit + push

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/land.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_land.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_land.py`:

```python
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr, chdir
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import land as land_cmd  # noqa: E402
from wily.config import save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _repo(tmp: Path) -> tuple[WilyPaths, Path]:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "w@x"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    src = tmp / "src"
    src.mkdir()
    (src / "a.py").write_text("# seed")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["w@x"])])
    return paths, src


class LandCommandTest(unittest.TestCase):
    def test_land_done_task_creates_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, src = _repo(Path(tmp))
            save_tasks(paths, "p", [
                Task(
                    id="T01", title="Lifecycle CLI",
                    status=TaskStatus.DONE,
                    scope=["src/*"],
                    actor="wily",
                    done_at="2026-05-18T13:00:00Z",
                ),
            ])
            paths.task_dir("T01").mkdir(parents=True)
            paths.result_md("T01").write_text("# T01: Lifecycle CLI — done\n", encoding="utf-8")
            (src / "a.py").write_text("# changed")
            with chdir(tmp), patch.object(land_cmd, "_confirm", return_value=True), \
                 patch.object(land_cmd, "_do_push", return_value=True):
                rc = land_cmd.main(["T01", "--no-push"])
            self.assertEqual(rc, 0)
            log = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=tmp,
                                 capture_output=True, text=True, check=True).stdout
            self.assertIn("T01: Lifecycle CLI", log)
            self.assertIn("Wily-Task: T01", log)

    def test_land_rejects_non_done_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, src = _repo(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="x", scope=["src/*"])])
            with chdir(tmp):
                rc = land_cmd.main(["T01", "--no-push"])
            self.assertEqual(rc, 3)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_land -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/land.py`:

```python
"""`wily land <id>` — stage scope changes, commit with Wily-Task trailer, push."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

from ..config import load_tasks
from ..models import TaskStatus
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from . import _common


def main(args: list[str]) -> int:
    force = "--force" in args
    no_push = "--no-push" in args
    positional = [a for a in args if not a.startswith("--")]
    if len(positional) != 1:
        _common.emit_error("usage: wily land <task-id> [--no-push] [--force]")
        return _common.EXIT_USAGE
    task_id = positional[0]

    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)
    _project_title, tasks = load_tasks(paths)
    target = next((t for t in tasks if t.id == task_id), None)
    if target is None:
        _common.emit_error(f"task not found: {task_id}")
        return _common.EXIT_FAILURE
    if target.status != TaskStatus.DONE and not force:
        _common.emit_error(
            f"{task_id} is {target.status.value}; run `wily done` first or pass --force."
        )
        return _common.EXIT_TRANSITION

    changed = _collect_changed(root)
    if not changed:
        _common.emit_error("nothing to commit (working tree clean)")
        return _common.EXIT_FAILURE

    in_scope, out_of_scope = _split_by_scope(changed, target.scope)
    if out_of_scope and not force:
        _common.emit_text(f"warning: {len(out_of_scope)} files outside scope; first: {out_of_scope[0]}")
        _common.emit_text("(use --force to include them anyway)")
        files_to_add = in_scope
    else:
        files_to_add = changed

    if not files_to_add:
        _common.emit_error("no files within scope to commit")
        return _common.EXIT_FAILURE

    body = _result_summary(paths, target.id)
    message = _build_message(target.id, target.title, body)

    subprocess.run(["git", "add", *files_to_add], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True)
    _common.emit_text(f"committed: {task_id}: {target.title}")

    if no_push:
        _common.emit_text("(push skipped: --no-push)")
        return _common.EXIT_OK
    if not _confirm("push to origin? [y/N] "):
        _common.emit_text("(push skipped by user)")
        return _common.EXIT_OK
    if _do_push(root):
        _common.emit_text("pushed.")
        return _common.EXIT_OK
    _common.emit_error("push failed")
    return _common.EXIT_FAILURE


def _collect_changed(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # Status format: XY <path>
        path = line[3:]
        files.append(path)
    return files


def _split_by_scope(files: list[str], scope: list[str]) -> tuple[list[str], list[str]]:
    if not scope:
        return files, []
    inside: list[str] = []
    outside: list[str] = []
    for f in files:
        if any(fnmatch.fnmatch(f, pat) for pat in scope):
            inside.append(f)
        else:
            outside.append(f)
    return inside, outside


def _build_message(task_id: str, title: str, body: str) -> str:
    head = f"{task_id}: {title}"
    if body:
        return f"{head}\n\n{body}\n\nWily-Task: {task_id}\n"
    return f"{head}\n\nWily-Task: {task_id}\n"


def _result_summary(paths: WilyPaths, task_id: str) -> str:
    result = paths.result_md(task_id)
    if not result.exists():
        return ""
    lines = result.read_text(encoding="utf-8").splitlines()
    # Take bullet lines after the title (skip empty leading lines).
    bullets = [ln.strip() for ln in lines if ln.strip().startswith("- ")]
    if not bullets:
        return ""
    return "\n".join(bullets[:6])


def _confirm(prompt: str) -> bool:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer in {"y", "yes"}


def _do_push(root: Path) -> bool:
    try:
        subprocess.run(["git", "push"], cwd=root, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_land -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/land.py plugins/wily-roadmap/tests/v3/test_cli_land.py
git commit -m "feat(wily): wily land commits scope changes with Wily-Task trailer"
```

---

### Task 8.2: `cli/replan.py` — add/revise/drop/assign/project/commit/cancel

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/replan.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_replan.py`

Reuses the same draft mechanism as `init` (Phase 9). Tasks are mutated in `.wily/init/draft.yaml` (we reuse the same file — the kind of edit makes it unambiguous). `replan commit` validates the dependency graph then writes `tasks.yaml` / `project.md`.

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_replan.py`:

```python
import sys
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import replan as replan_cmd  # noqa: E402
from wily.config import load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _scaffold(tmp: Path) -> WilyPaths:
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    save_actors(paths, [Actor(id="wily", display="Wily")])
    return paths


class ReplanTest(unittest.TestCase):
    def test_add_then_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="a")])
            with chdir(tmp):
                self.assertEqual(replan_cmd.main(["add", "New task"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T02", "intent", "do the thing"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T02", "scope", "src/*.py"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T02", "depends_on", "T01"]), 0)
                self.assertEqual(replan_cmd.main(["commit"]), 0)
            _, tasks = load_tasks(paths)
            ids = [t.id for t in tasks]
            self.assertEqual(ids, ["T01", "T02"])
            t2 = next(t for t in tasks if t.id == "T02")
            self.assertEqual(t2.intent, "do the thing")
            self.assertEqual(t2.scope, ["src/*.py"])
            self.assertEqual(t2.depends_on, ["T01"])

    def test_drop_ready_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [
                Task(id="T01", title="a", status=TaskStatus.DONE),
                Task(id="T02", title="b"),
            ])
            with chdir(tmp):
                # Cannot drop a done task
                self.assertNotEqual(replan_cmd.main(["drop", "T01"]), 0)
                self.assertEqual(replan_cmd.main(["drop", "T02"]), 0)
                self.assertEqual(replan_cmd.main(["commit"]), 0)
            _, tasks = load_tasks(paths)
            self.assertEqual([t.id for t in tasks], ["T01"])

    def test_commit_rejects_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="a")])
            with chdir(tmp):
                self.assertEqual(replan_cmd.main(["add", "Two"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T01", "depends_on", "T02"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T02", "depends_on", "T01"]), 0)
                rc = replan_cmd.main(["commit"])
            self.assertEqual(rc, 1)

    def test_cancel_discards_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _scaffold(Path(tmp))
            save_tasks(paths, "p", [Task(id="T01", title="a")])
            with chdir(tmp):
                self.assertEqual(replan_cmd.main(["add", "scratch"]), 0)
                self.assertEqual(replan_cmd.main(["cancel"]), 0)
            _, tasks = load_tasks(paths)
            self.assertEqual([t.id for t in tasks], ["T01"])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_replan -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/replan.py`:

```python
"""`wily replan` — manage tasks.yaml mutations through commands only.

Mutations stage in `.wily/init/draft.yaml` (same draft file as init; the
draft has a `mode` field discriminating which one wrote it). `commit`
validates and persists; `cancel` discards.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..config import load_tasks, save_tasks
from ..models import Task, TaskStatus
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
from ..transitions import check_dependencies, DependencyError
from . import _common

DRAFT_MODE = "replan"


def main(args: list[str]) -> int:
    if not args:
        return _show(args)
    sub, rest = args[0], args[1:]
    try:
        root = find_wily_root(Path.cwd())
    except WilyRootNotFound as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    paths = WilyPaths(root)

    if sub == "show":
        return _show(rest, paths=paths)
    if sub == "add":
        return _add(paths, rest)
    if sub == "revise-task":
        return _revise(paths, rest)
    if sub == "drop":
        return _drop(paths, rest)
    if sub == "assign":
        return _assign(paths, rest)
    if sub == "commit":
        return _commit(paths)
    if sub == "cancel":
        return _cancel(paths)
    _common.emit_error(f"unknown replan subcommand: {sub}")
    return _common.EXIT_USAGE


def _draft_load(paths: WilyPaths) -> dict:
    if paths.init_draft.exists():
        return yaml.safe_load(paths.init_draft.read_text(encoding="utf-8")) or {}
    return {"mode": DRAFT_MODE, "tasks": []}


def _draft_save(paths: WilyPaths, draft: dict) -> None:
    paths.init_dir.mkdir(parents=True, exist_ok=True)
    paths.init_draft.write_text(
        yaml.safe_dump(draft, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _show(args: list[str], paths: WilyPaths | None = None) -> int:
    if paths is None:
        try:
            paths = WilyPaths(find_wily_root(Path.cwd()))
        except WilyRootNotFound as exc:
            _common.emit_error(str(exc))
            return _common.EXIT_FAILURE
    project_title, tasks = load_tasks(paths)
    _common.emit_text(f"Project: {project_title}")
    for t in tasks:
        _common.emit_text(f"  {t.id}  {t.status.value}  {t.title}")
    if paths.init_draft.exists():
        _common.emit_text("(draft pending: run `wily replan commit` to apply or `cancel` to discard)")
    return _common.EXIT_OK


def _next_id(existing: list[str]) -> str:
    nums: list[int] = []
    for tid in existing:
        if tid.startswith("T") and tid[1:].isdigit():
            nums.append(int(tid[1:]))
    next_n = (max(nums) + 1) if nums else 1
    return f"T{next_n:02d}"


def _apply_draft(paths: WilyPaths) -> tuple[str, list[Task]]:
    project_title, tasks = load_tasks(paths)
    draft = _draft_load(paths)
    new_tasks = [t for t in tasks if t.id not in draft.get("dropped", [])]
    edits: dict[str, dict] = draft.get("edits", {})
    for tid, fields in edits.items():
        existing = next((t for t in new_tasks if t.id == tid), None)
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
    for added in draft.get("added", []):
        new_tasks.append(Task.from_dict(added))
    if "project_title" in draft:
        project_title = draft["project_title"]
    return project_title, new_tasks


def _add(paths: WilyPaths, args: list[str]) -> int:
    title = " ".join(args).strip()
    if not title:
        _common.emit_error("usage: wily replan add \"<title>\"")
        return _common.EXIT_USAGE
    project_title, tasks = load_tasks(paths)
    draft = _draft_load(paths)
    existing_ids = [t.id for t in tasks] + [a["id"] for a in draft.get("added", [])]
    new_id = _next_id(existing_ids)
    draft.setdefault("added", []).append({
        "id": new_id,
        "title": title,
        "intent": "",
        "acceptance": "",
        "scope": [],
        "depends_on": [],
        "status": "ready",
    })
    _draft_save(paths, draft)
    _common.emit_text(f"draft: added {new_id} {title!r}")
    return _common.EXIT_OK


def _revise(paths: WilyPaths, args: list[str]) -> int:
    if len(args) < 3:
        _common.emit_error("usage: wily replan revise-task <id> <field> <value>")
        return _common.EXIT_USAGE
    tid, field, value = args[0], args[1], " ".join(args[2:])
    allowed = {"title", "intent", "acceptance", "scope", "depends_on", "assignee"}
    if field not in allowed:
        _common.emit_error(f"field must be one of: {sorted(allowed)}")
        return _common.EXIT_USAGE

    draft = _draft_load(paths)
    # Try draft.added first (newly proposed task)
    for added in draft.get("added", []):
        if added["id"] == tid:
            added[field] = _parse_field_value(field, value)
            _draft_save(paths, draft)
            _common.emit_text(f"draft: {tid}.{field} updated")
            return _common.EXIT_OK
    # Existing task — stage an edit
    project_title, tasks = load_tasks(paths)
    existing = next((t for t in tasks if t.id == tid), None)
    if existing is None:
        _common.emit_error(f"task not found: {tid}")
        return _common.EXIT_FAILURE
    if existing.status == TaskStatus.DONE and field != "title":
        _common.emit_error(f"{tid} is done; refusing to revise non-cosmetic field {field!r}")
        return _common.EXIT_TRANSITION
    draft.setdefault("edits", {}).setdefault(tid, {})[field] = _parse_field_value(field, value)
    _draft_save(paths, draft)
    _common.emit_text(f"draft: {tid}.{field} updated")
    return _common.EXIT_OK


def _parse_field_value(field: str, raw: str):
    if field in {"scope", "depends_on"}:
        if not raw.strip():
            return []
        return [s.strip() for s in raw.split(",") if s.strip()]
    return raw


def _drop(paths: WilyPaths, args: list[str]) -> int:
    if len(args) != 1:
        _common.emit_error("usage: wily replan drop <task-id>")
        return _common.EXIT_USAGE
    tid = args[0]
    project_title, tasks = load_tasks(paths)
    existing = next((t for t in tasks if t.id == tid), None)
    draft = _draft_load(paths)
    if existing is None:
        draft.setdefault("added", [])
        draft["added"] = [a for a in draft["added"] if a["id"] != tid]
        _draft_save(paths, draft)
        _common.emit_text(f"draft: removed proposed {tid}")
        return _common.EXIT_OK
    if existing.status != TaskStatus.READY:
        _common.emit_error(f"{tid} is {existing.status.value}; only ready tasks can be dropped")
        return _common.EXIT_TRANSITION
    draft.setdefault("dropped", []).append(tid)
    _draft_save(paths, draft)
    _common.emit_text(f"draft: {tid} marked for removal")
    return _common.EXIT_OK


def _assign(paths: WilyPaths, args: list[str]) -> int:
    if len(args) != 2:
        _common.emit_error("usage: wily replan assign <task-id> <actor>")
        return _common.EXIT_USAGE
    tid, actor = args
    return _revise(paths, [tid, "assignee", actor])


def _commit(paths: WilyPaths) -> int:
    if not paths.init_draft.exists():
        _common.emit_error("no draft pending; nothing to commit")
        return _common.EXIT_FAILURE
    try:
        project_title, new_tasks = _apply_draft(paths)
    except (KeyError, ValueError) as exc:
        _common.emit_error(f"draft is malformed: {exc}")
        return _common.EXIT_FAILURE
    try:
        check_dependencies(new_tasks)
    except DependencyError as exc:
        _common.emit_error(f"dependency check failed: {exc}")
        return _common.EXIT_FAILURE
    save_tasks(paths, project_title, new_tasks)
    paths.init_draft.unlink()
    _common.emit_text(f"replan applied: {len(new_tasks)} task(s)")
    return _common.EXIT_OK


def _cancel(paths: WilyPaths) -> int:
    if paths.init_draft.exists():
        paths.init_draft.unlink()
    _common.emit_text("replan draft discarded")
    return _common.EXIT_OK
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_replan -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/replan.py plugins/wily-roadmap/tests/v3/test_cli_replan.py
git commit -m "feat(wily): wily replan add/revise-task/drop/assign/commit/cancel"
```

---

## Phase 9 — Init engine

`wily init` is the largest single feature. Split into: draft store (9.1), question registry (9.2), greenfield interview flow (9.3), brownfield analyzer + flow (9.4), and the CLI dispatcher tying them together (9.5).

### Task 9.1: `interview.py` — draft load/save + answer state

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/interview.py`
- Test: `plugins/wily-roadmap/tests/v3/test_interview.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_interview.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.interview import (  # noqa: E402
    Draft,
    load_or_init_draft,
    save_draft,
    record_answer,
    revise_answer,
    pop_last_answer,
    add_task_candidate,
    revise_task_candidate,
    drop_task_candidate,
    assign_task_candidate,
)
from wily.paths import WilyPaths  # noqa: E402


def _paths(tmp: Path) -> WilyPaths:
    paths = WilyPaths(tmp)
    paths.wily_dir.mkdir()
    return paths


class DraftStoreTest(unittest.TestCase):
    def test_load_or_init_creates_greenfield_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            self.assertEqual(draft.mode, "greenfield")
            self.assertEqual(draft.answers, {})
            self.assertEqual(draft.task_candidates, [])

    def test_record_answer_persists_and_advances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            record_answer(draft, key="purpose", text="rebuild wily")
            save_draft(paths, draft)
            again = load_or_init_draft(paths, mode="greenfield")
            self.assertEqual(again.answers["purpose"], "rebuild wily")
            self.assertIn("purpose", again.history)

    def test_revise_answer_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            record_answer(draft, key="purpose", text="old")
            revise_answer(draft, key="purpose", text="new")
            self.assertEqual(draft.answers["purpose"], "new")

    def test_pop_last_answer_removes_most_recent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            record_answer(draft, key="purpose", text="x")
            record_answer(draft, key="users", text="y")
            popped = pop_last_answer(draft)
            self.assertEqual(popped, "users")
            self.assertNotIn("users", draft.answers)


class TaskCandidateTest(unittest.TestCase):
    def test_add_then_revise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            add_task_candidate(draft, title="First")
            self.assertEqual(draft.task_candidates[0]["id"], "T01")
            revise_task_candidate(draft, "T01", "intent", "do thing")
            self.assertEqual(draft.task_candidates[0]["intent"], "do thing")

    def test_drop_removes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            add_task_candidate(draft, title="A")
            add_task_candidate(draft, title="B")
            drop_task_candidate(draft, "T01")
            self.assertEqual([t["id"] for t in draft.task_candidates], ["T02"])

    def test_assign_sets_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            draft = load_or_init_draft(paths, mode="greenfield")
            add_task_candidate(draft, title="A")
            assign_task_candidate(draft, "T01", "wily")
            self.assertEqual(draft.task_candidates[0]["assignee"], "wily")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_interview -v
```

Expected: `ModuleNotFoundError: No module named 'wily.interview'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/interview.py`:

```python
"""Interview state for `wily init` and (reusing the same storage) `wily replan`.

Draft lives at `.wily/init/draft.yaml`. Schema (loose, mutated by the CLI):

```yaml
mode: greenfield | brownfield | replan
answers:                # key -> string answer
  purpose: "..."
history: [purpose, ...] # ordered keys for back/pop
task_candidates:        # list of task dicts (same shape as tasks.yaml entries)
  - id: T01
    title: "..."
    intent: ""
    acceptance: ""
    scope: []
    depends_on: []
    status: ready
    assignee: null
project_title: "..."    # set during commit
```

All functions take Draft + mutate in place. CLI persists via save_draft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from .paths import WilyPaths


@dataclass
class Draft:
    mode: str
    answers: dict[str, str] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    task_candidates: list[dict[str, Any]] = field(default_factory=list)
    project_title: str = ""


def load_or_init_draft(paths: WilyPaths, *, mode: str) -> Draft:
    if paths.init_draft.exists():
        data = yaml.safe_load(paths.init_draft.read_text(encoding="utf-8")) or {}
        return Draft(
            mode=data.get("mode", mode),
            answers=dict(data.get("answers") or {}),
            history=list(data.get("history") or []),
            task_candidates=list(data.get("task_candidates") or []),
            project_title=data.get("project_title", ""),
        )
    return Draft(mode=mode)


def save_draft(paths: WilyPaths, draft: Draft) -> None:
    paths.init_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": draft.mode,
        "answers": draft.answers,
        "history": draft.history,
        "task_candidates": draft.task_candidates,
        "project_title": draft.project_title,
    }
    paths.init_draft.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def discard_draft(paths: WilyPaths) -> None:
    if paths.init_draft.exists():
        paths.init_draft.unlink()


def record_answer(draft: Draft, *, key: str, text: str) -> None:
    draft.answers[key] = text
    if key in draft.history:
        draft.history.remove(key)
    draft.history.append(key)


def revise_answer(draft: Draft, *, key: str, text: str) -> None:
    if key not in draft.answers:
        raise KeyError(f"no prior answer for {key!r}")
    draft.answers[key] = text


def pop_last_answer(draft: Draft) -> str | None:
    if not draft.history:
        return None
    key = draft.history.pop()
    draft.answers.pop(key, None)
    return key


def _next_candidate_id(draft: Draft) -> str:
    nums: list[int] = []
    for tc in draft.task_candidates:
        tid = tc.get("id", "")
        if tid.startswith("T") and tid[1:].isdigit():
            nums.append(int(tid[1:]))
    next_n = (max(nums) + 1) if nums else 1
    return f"T{next_n:02d}"


def add_task_candidate(draft: Draft, *, title: str) -> str:
    tid = _next_candidate_id(draft)
    draft.task_candidates.append({
        "id": tid,
        "title": title,
        "intent": "",
        "acceptance": "",
        "scope": [],
        "depends_on": [],
        "status": "ready",
        "assignee": None,
    })
    return tid


def revise_task_candidate(draft: Draft, tid: str, field: str, value: Any) -> None:
    for tc in draft.task_candidates:
        if tc["id"] == tid:
            tc[field] = value
            return
    raise KeyError(f"no candidate {tid}")


def drop_task_candidate(draft: Draft, tid: str) -> None:
    draft.task_candidates = [t for t in draft.task_candidates if t["id"] != tid]


def assign_task_candidate(draft: Draft, tid: str, actor: str) -> None:
    revise_task_candidate(draft, tid, "assignee", actor)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_interview -v
```

Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/interview.py plugins/wily-roadmap/tests/v3/test_interview.py
git commit -m "feat(wily): v3 init draft store and task candidate ops"
```

---

### Task 9.2: `questions.py` — greenfield + brownfield question registries

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/questions.py`
- Test: `plugins/wily-roadmap/tests/v3/test_questions.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_questions.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.interview import Draft, record_answer  # noqa: E402
from wily.questions import (  # noqa: E402
    GREENFIELD_KEYS,
    BROWNFIELD_KEYS,
    next_question,
    ready_for_tasks,
    question_text,
)


class GreenfieldFlowTest(unittest.TestCase):
    def test_first_question_is_purpose(self) -> None:
        d = Draft(mode="greenfield")
        q = next_question(d)
        self.assertEqual(q, "purpose")

    def test_advances_through_all_keys(self) -> None:
        d = Draft(mode="greenfield")
        seen = []
        for _ in range(len(GREENFIELD_KEYS)):
            q = next_question(d)
            seen.append(q)
            record_answer(d, key=q, text="x")
        self.assertEqual(seen, list(GREENFIELD_KEYS))

    def test_ready_for_tasks_after_all_answered(self) -> None:
        d = Draft(mode="greenfield")
        for k in GREENFIELD_KEYS:
            record_answer(d, key=k, text="x")
        self.assertTrue(ready_for_tasks(d))

    def test_not_ready_when_missing(self) -> None:
        d = Draft(mode="greenfield")
        record_answer(d, key="purpose", text="x")
        self.assertFalse(ready_for_tasks(d))


class BrownfieldFlowTest(unittest.TestCase):
    def test_brownfield_starts_with_analysis_confirm(self) -> None:
        d = Draft(mode="brownfield")
        q = next_question(d)
        self.assertEqual(q, "analysis_confirm")


class QuestionTextTest(unittest.TestCase):
    def test_question_text_is_korean_and_nonempty(self) -> None:
        for key in GREENFIELD_KEYS:
            text = question_text(key)
            self.assertTrue(text)
            self.assertGreater(len(text), 5)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_questions -v
```

Expected: `ModuleNotFoundError: No module named 'wily.questions'`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/questions.py`:

```python
"""Interview question registries.

Two flows:
  - greenfield: purpose → users → success → non_goals → actors_setup
  - brownfield: analysis_confirm → purpose_revise → success → non_goals → actors_setup

After all keys are answered, the CLI transitions to task candidate suggestion.
"""

from __future__ import annotations

from .interview import Draft

GREENFIELD_KEYS = (
    "purpose",
    "users",
    "success",
    "non_goals",
    "actors_setup",
)

BROWNFIELD_KEYS = (
    "analysis_confirm",
    "purpose_revise",
    "success",
    "non_goals",
    "actors_setup",
)


QUESTION_TEXT_KO = {
    "purpose": "이 프로젝트의 한 줄 목적은? (예: \"고객 지원 챗봇\")",
    "users": "누가 쓰나? 주요 사용자/이해관계자를 알려줘.",
    "success": "무엇이 되면 성공인가? 객관적 조건으로 1~3줄.",
    "non_goals": "절대 안 하는 것 / 제약은? (없으면 \"없음\")",
    "actors_setup": (
        "협업 인원의 actor 별칭과 git author 매핑을 알려줘. "
        "형식: \"<id> <display>, emails=a@b,c@d; <id2> ...\". 본인만이면 \"wily\""
    ),
    "analysis_confirm": (
        "자동 분석 결과(위 출력)가 이 프로젝트의 정체에 맞나? "
        "맞으면 \"ok\", 보강하려면 \"revise: <설명>\"."
    ),
    "purpose_revise": "큰 그림을 보강하고 싶은 부분이 있나? 없으면 \"없음\".",
}


def next_question(draft: Draft) -> str | None:
    keys = GREENFIELD_KEYS if draft.mode == "greenfield" else BROWNFIELD_KEYS
    for key in keys:
        if key not in draft.answers:
            return key
    return None


def ready_for_tasks(draft: Draft) -> bool:
    return next_question(draft) is None


def question_text(key: str) -> str:
    return QUESTION_TEXT_KO.get(key, f"answer for {key}?")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_questions -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/questions.py plugins/wily-roadmap/tests/v3/test_questions.py
git commit -m "feat(wily): v3 interview question registries"
```

---

### Task 9.3: `analysis.py` — brownfield repo analyzer

**Files:**
- Create: `plugins/wily-roadmap/scripts/wily/analysis.py`
- Test: `plugins/wily-roadmap/tests/v3/test_analysis.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_analysis.py`:

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, set(map(str, [ROOT / "scripts"])).pop())

from wily.analysis import (  # noqa: E402
    BrownfieldSnapshot,
    analyze_repo,
    extract_authors,
)


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "wily@x"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=path, check=True)


def _commit(path: Path, files: dict[str, str], message: str) -> None:
    for rel, content in files.items():
        full = path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=path, check=True)


class AnalyzeRepoTest(unittest.TestCase):
    def test_empty_repo_returns_minimal_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            snap = analyze_repo(repo)
            self.assertEqual(snap.authors, [])
            self.assertEqual(snap.commit_count, 0)

    def test_repo_with_history_extracts_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            _commit(repo, {"README.md": "# Hello\n\nA project that does X.\n"}, "init")
            _commit(repo, {"src/a.py": "x = 1"}, "feature a")
            snap = analyze_repo(repo)
            self.assertGreaterEqual(snap.commit_count, 2)
            self.assertIn("wily", snap.authors[0]["name"])
            self.assertIn("Hello", snap.readme_excerpt or "")


class ExtractAuthorsTest(unittest.TestCase):
    def test_extract_authors_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            _commit(repo, {"a": "1"}, "one")
            _commit(repo, {"b": "1"}, "two")
            authors = extract_authors(repo)
            self.assertEqual(len(authors), 1)
            self.assertEqual(authors[0]["email"], "wily@x")
            self.assertGreaterEqual(authors[0]["commits"], 2)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_analysis -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/analysis.py`:

```python
"""Brownfield repository analysis for `wily init --adopt`.

Best-effort: read git log, README, top-level file tree. Each piece is
optional — analyzer never raises on missing data. Returns a snapshot
the CLI presents as a first-pass description for the user to confirm.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BrownfieldSnapshot:
    commit_count: int = 0
    authors: list[dict] = field(default_factory=list)
    readme_excerpt: str | None = None
    top_level_files: list[str] = field(default_factory=list)
    legacy_wily_detected: bool = False


def analyze_repo(repo: Path) -> BrownfieldSnapshot:
    snap = BrownfieldSnapshot()
    snap.commit_count = _commit_count(repo)
    snap.authors = extract_authors(repo)
    snap.readme_excerpt = _read_readme(repo)
    snap.top_level_files = _list_top_level(repo)
    snap.legacy_wily_detected = (repo / ".wily" / "roadmap.yaml").exists()
    return snap


def _commit_count(repo: Path) -> int:
    try:
        out = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return int(out or "0")
    except (subprocess.CalledProcessError, ValueError):
        return 0


def extract_authors(repo: Path) -> list[dict]:
    try:
        out = subprocess.run(
            ["git", "log", "--pretty=format:%ae|%an", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return []
    counts: dict[tuple[str, str], int] = {}
    for line in out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        email, name = line.split("|", 1)
        key = (email, name)
        counts[key] = counts.get(key, 0) + 1
    return sorted(
        ({"email": e, "name": n, "commits": c} for (e, n), c in counts.items()),
        key=lambda d: -d["commits"],
    )


def _read_readme(repo: Path) -> str | None:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        candidate = repo / name
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8", errors="replace")
            return "\n".join(text.splitlines()[:30])
    return None


def _list_top_level(repo: Path) -> list[str]:
    try:
        return sorted(
            p.name for p in repo.iterdir()
            if not p.name.startswith(".") and p.name != "node_modules"
        )
    except OSError:
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Replace the awkward `sys.path.insert` line in the test (it was deliberately written badly to ensure it'd fail-first). Update test header:

```python
sys.path.insert(0, str(ROOT / "scripts"))
```

Then:

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_analysis -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/analysis.py plugins/wily-roadmap/tests/v3/test_analysis.py
git commit -m "feat(wily): v3 brownfield repo analysis"
```

---

### Task 9.4: `cli/init.py` — interview dispatch (entry + answer/back/revise/show)

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/init.py`
- Test: `plugins/wily-roadmap/tests/v3/test_cli_init.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_init.py`:

```python
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import init as init_cmd  # noqa: E402
from wily.config import load_actors, load_tasks  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def _bare_repo(tmp: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "wily@x"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=tmp, check=True)
    (tmp / "README.md").write_text("# demo\n")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp, check=True)


class InitFlowTest(unittest.TestCase):
    def test_first_call_prompts_purpose_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _bare_repo(Path(tmp))
            (Path(tmp) / ".wily").mkdir()
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                rc = init_cmd.main(["--new"])
            self.assertEqual(rc, 0)
            self.assertIn("목적", buf.getvalue())

    def test_answer_advances_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _bare_repo(Path(tmp))
            (Path(tmp) / ".wily").mkdir()
            with chdir(tmp):
                init_cmd.main(["--new"])
                rc = init_cmd.main(["answer", "rebuild wily"])
            self.assertEqual(rc, 0)
            buf = io.StringIO()
            with chdir(tmp), redirect_stdout(buf):
                init_cmd.main([])
            self.assertIn("사용자", buf.getvalue())

    def test_back_pops_last(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _bare_repo(Path(tmp))
            (Path(tmp) / ".wily").mkdir()
            with chdir(tmp):
                init_cmd.main(["--new"])
                init_cmd.main(["answer", "a"])
                init_cmd.main(["answer", "b"])
                rc = init_cmd.main(["back"])
            self.assertEqual(rc, 0)

    def test_show_displays_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _bare_repo(Path(tmp))
            (Path(tmp) / ".wily").mkdir()
            with chdir(tmp):
                init_cmd.main(["--new"])
                init_cmd.main(["answer", "rebuild wily"])
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = init_cmd.main(["show"])
            self.assertEqual(rc, 0)
            self.assertIn("rebuild wily", buf.getvalue())

    def test_full_greenfield_commits_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _bare_repo(Path(tmp))
            (Path(tmp) / ".wily").mkdir()
            with chdir(tmp):
                init_cmd.main(["--new"])
                init_cmd.main(["answer", "rebuild wily"])
                init_cmd.main(["answer", "Wily 박사"])
                init_cmd.main(["answer", "tasks.yaml runs"])
                init_cmd.main(["answer", "no LLM call"])
                init_cmd.main(["answer", "wily wily@x"])
                init_cmd.main(["add-task", "First task"])
                init_cmd.main(["revise-task", "T01", "intent", "do the thing"])
                rc = init_cmd.main(["commit"])
            self.assertEqual(rc, 0)
            paths = WilyPaths(Path(tmp))
            self.assertTrue(paths.project_md.exists())
            self.assertTrue(paths.tasks_yaml.exists())
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].id, "T01")
            self.assertEqual(tasks[0].intent, "do the thing")
            actors = load_actors(paths)
            self.assertEqual(actors[0].id, "wily")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_init -v
```

Expected: stub failures.

- [ ] **Step 3: Write minimal implementation**

`plugins/wily-roadmap/scripts/wily/cli/init.py`:

```python
"""`wily init` — interview-driven bootstrap (greenfield + brownfield).

Everything mutates via subcommands; never opens an editor or reads from
a file the user wrote. Draft state in `.wily/init/draft.yaml`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..analysis import analyze_repo
from ..config import save_actors, save_tasks
from ..models import Actor, Task
from ..paths import WilyPaths, find_wily_root, WilyRootNotFound
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
from ..questions import next_question, question_text, ready_for_tasks
from ..transitions import check_dependencies, DependencyError
from . import _common


def main(args: list[str]) -> int:
    explicit_mode = None
    if "--new" in args:
        explicit_mode = "greenfield"
    if "--adopt" in args:
        explicit_mode = "brownfield"
    args = [a for a in args if a not in {"--new", "--adopt"}]

    cwd = Path.cwd()
    try:
        root = find_wily_root(cwd)
    except WilyRootNotFound:
        # Allow init from a directory without .wily/ — we create it.
        root = cwd
        (root / ".wily").mkdir(parents=True, exist_ok=True)

    paths = WilyPaths(root)

    if not args:
        return _start_or_continue(paths, explicit_mode, root)

    sub, rest = args[0], args[1:]
    if sub == "show":
        return _show(paths)
    if sub == "answer":
        return _answer(paths, rest)
    if sub == "back":
        return _back(paths)
    if sub == "revise":
        return _revise(paths, rest)
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

    _common.emit_error(f"unknown init subcommand: {sub}")
    return _common.EXIT_USAGE


def _detect_mode(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    snap = analyze_repo(root)
    if snap.commit_count == 0 and not snap.readme_excerpt:
        return "greenfield"
    return "brownfield"


def _start_or_continue(paths: WilyPaths, explicit_mode: str | None, root: Path) -> int:
    if paths.init_draft.exists():
        draft = load_or_init_draft(paths, mode="greenfield")
    else:
        mode = _detect_mode(root, explicit_mode)
        draft = load_or_init_draft(paths, mode=mode)
        if draft.mode == "brownfield":
            snap = analyze_repo(root)
            draft.answers["_analysis"] = yaml.safe_dump(
                {
                    "commit_count": snap.commit_count,
                    "authors": snap.authors,
                    "top_level_files": snap.top_level_files,
                    "readme_excerpt": snap.readme_excerpt,
                    "legacy_wily_detected": snap.legacy_wily_detected,
                },
                allow_unicode=True,
            )
        save_draft(paths, draft)
        _common.emit_text(f"wily init started (mode: {draft.mode})")

    return _emit_next_question(paths, draft, root)


def _emit_next_question(paths: WilyPaths, draft: Draft, root: Path) -> int:
    if draft.mode == "brownfield" and "_analysis" in draft.answers and "analysis_confirm" not in draft.answers:
        _common.emit_text("=== 자동 분석 결과 ===")
        _common.emit_text(draft.answers["_analysis"])
        _common.emit_text("===")
    key = next_question(draft)
    if key is None:
        _common.emit_text("모든 질문이 끝났음. `wily init suggest`로 task 후보 보고, `wily init commit`로 확정.")
        return _common.EXIT_OK
    _common.emit_text(f"[{key}] {question_text(key)}")
    return _common.EXIT_OK


def _show(paths: WilyPaths) -> int:
    if not paths.init_draft.exists():
        _common.emit_text("(no draft in progress)")
        return _common.EXIT_OK
    draft = load_or_init_draft(paths, mode="greenfield")
    _common.emit_text(f"mode: {draft.mode}")
    for k in draft.history:
        if k.startswith("_"):
            continue
        _common.emit_text(f"  {k}: {draft.answers[k]}")
    if draft.task_candidates:
        _common.emit_text("task candidates:")
        for tc in draft.task_candidates:
            _common.emit_text(
                f"  {tc['id']}  {tc['title']!r}  assignee={tc.get('assignee') or '-'}"
            )
    return _common.EXIT_OK


def _answer(paths: WilyPaths, args: list[str]) -> int:
    if "--multi" in args:
        import sys as _sys
        text = _sys.stdin.read().rstrip("\n")
    else:
        text = " ".join(args).strip()
    if not text:
        _common.emit_error("usage: wily init answer <text> | --multi")
        return _common.EXIT_USAGE

    draft = load_or_init_draft(paths, mode="greenfield")
    key = next_question(draft)
    if key is None:
        _common.emit_error("no current question; use `wily init revise <key> <text>`")
        return _common.EXIT_USAGE
    record_answer(draft, key=key, text=text)
    save_draft(paths, draft)
    _common.emit_text(f"saved {key!r}.")
    return _emit_next_question(paths, draft, Path.cwd())


def _back(paths: WilyPaths) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    popped = pop_last_answer(draft)
    if popped is None:
        _common.emit_text("nothing to roll back")
        return _common.EXIT_OK
    save_draft(paths, draft)
    _common.emit_text(f"removed last answer: {popped}")
    return _emit_next_question(paths, draft, Path.cwd())


def _revise(paths: WilyPaths, args: list[str]) -> int:
    if len(args) < 2:
        _common.emit_error("usage: wily init revise <key> <text>")
        return _common.EXIT_USAGE
    key, text = args[0], " ".join(args[1:])
    draft = load_or_init_draft(paths, mode="greenfield")
    try:
        revise_answer(draft, key=key, text=text)
    except KeyError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"revised {key!r}.")
    return _common.EXIT_OK


def _suggest(paths: WilyPaths) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    if not ready_for_tasks(draft):
        missing = next_question(draft)
        _common.emit_text(f"답이 부족: {missing!r} 부터 채워줘 (`wily init answer ...`).")
        return _common.EXIT_FAILURE
    if not draft.task_candidates:
        _common.emit_text(
            "task 후보가 비었음. `wily init add-task \"<title>\"`로 추가 후 `revise-task`로 보강."
        )
    else:
        for tc in draft.task_candidates:
            _common.emit_text(
                f"{tc['id']}  {tc['title']!r}  assignee={tc.get('assignee') or '-'}"
            )
    return _common.EXIT_OK


def _add_task(paths: WilyPaths, args: list[str]) -> int:
    title = " ".join(args).strip()
    if not title:
        _common.emit_error("usage: wily init add-task \"<title>\"")
        return _common.EXIT_USAGE
    draft = load_or_init_draft(paths, mode="greenfield")
    tid = add_task_candidate(draft, title=title)
    save_draft(paths, draft)
    _common.emit_text(f"added {tid}: {title!r}")
    return _common.EXIT_OK


def _revise_task(paths: WilyPaths, args: list[str]) -> int:
    if len(args) < 3:
        _common.emit_error("usage: wily init revise-task <id> <field> <value>")
        return _common.EXIT_USAGE
    tid, field, value = args[0], args[1], " ".join(args[2:])
    draft = load_or_init_draft(paths, mode="greenfield")
    if field in {"scope", "depends_on"}:
        parsed = [s.strip() for s in value.split(",") if s.strip()]
    else:
        parsed = value
    try:
        revise_task_candidate(draft, tid, field, parsed)
    except KeyError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"{tid}.{field} updated")
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
    except KeyError as exc:
        _common.emit_error(str(exc))
        return _common.EXIT_FAILURE
    save_draft(paths, draft)
    _common.emit_text(f"{args[0]}.assignee = {args[1]}")
    return _common.EXIT_OK


def _commit(paths: WilyPaths, root: Path) -> int:
    draft = load_or_init_draft(paths, mode="greenfield")
    if not ready_for_tasks(draft):
        missing = next_question(draft)
        _common.emit_error(f"답이 부족함: {missing!r}")
        return _common.EXIT_FAILURE

    actors = _parse_actors_setup(draft.answers.get("actors_setup", ""))
    tasks = [Task.from_dict(tc) for tc in draft.task_candidates]
    try:
        check_dependencies(tasks)
    except DependencyError as exc:
        _common.emit_error(f"dependency check failed: {exc}")
        return _common.EXIT_FAILURE

    purpose = draft.answers.get("purpose") or draft.answers.get("purpose_revise") or ""
    project_title = purpose.splitlines()[0] if purpose else "(untitled)"
    save_tasks(paths, project_title, tasks)
    save_actors(paths, actors)
    _write_project_md(paths, draft)

    discard_draft(paths)
    _common.emit_text(f"init committed: {len(tasks)} task(s), {len(actors)} actor(s)")
    _common.emit_text(f"project.md / tasks.yaml / actors.yaml written under {paths.wily_dir.relative_to(root) if paths.wily_dir.is_relative_to(root) else paths.wily_dir}")
    return _common.EXIT_OK


def _cancel(paths: WilyPaths) -> int:
    discard_draft(paths)
    _common.emit_text("init draft discarded")
    return _common.EXIT_OK


def _parse_actors_setup(text: str) -> list[Actor]:
    """Parse '<id> <display>, emails=a@b,c@d; <id2> ...' into Actors."""
    if not text.strip():
        return [Actor(id="wily", display="Wily")]
    actors: list[Actor] = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        emails: list[str] = []
        if "emails=" in chunk:
            head, _, email_part = chunk.partition("emails=")
            emails = [e.strip() for e in email_part.split(",") if e.strip()]
            chunk = head.strip().rstrip(",")
        parts = chunk.split(None, 1)
        if not parts:
            continue
        aid = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else aid
        actors.append(Actor(id=aid, display=display, git_author_emails=emails))
    if not actors:
        actors = [Actor(id="wily", display="Wily")]
    return actors


def _write_project_md(paths: WilyPaths, draft: Draft) -> None:
    body: list[str] = []
    body.append(f"# {draft.answers.get('purpose', '(no purpose)')}")
    body.append("")
    for key in ("users", "success", "non_goals", "purpose_revise"):
        value = draft.answers.get(key)
        if value:
            body.append(f"## {key}")
            body.append(value)
            body.append("")
    paths.project_md.write_text("\n".join(body), encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_init -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/init.py plugins/wily-roadmap/tests/v3/test_cli_init.py
git commit -m "feat(wily): wily init interview flow (greenfield + brownfield)"
```

---

### Task 9.5: Brownfield adopt path — archive legacy `.wily/`

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/init.py` (extend `_start_or_continue` and add `adopt-legacy` subcommand)
- Test: `plugins/wily-roadmap/tests/v3/test_cli_init_adopt.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_cli_init_adopt.py`:

```python
import sys
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import init as init_cmd  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


class AdoptLegacyTest(unittest.TestCase):
    def test_adopt_archives_legacy_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".wily" / "stages").mkdir(parents=True)
            (root / ".wily" / "roadmap.yaml").write_text("roadmap_schema: wily-roadmap-v2\n")
            (root / ".wily" / "status.md").write_text("# old status\n")
            with chdir(root):
                rc = init_cmd.main(["adopt-legacy"])
            self.assertEqual(rc, 0)
            paths = WilyPaths(root)
            self.assertTrue(paths.archive_dir.exists())
            archived = list(paths.archive_dir.iterdir())
            self.assertEqual(len(archived), 1)
            self.assertTrue((archived[0] / "roadmap.yaml").exists())
            self.assertFalse((root / ".wily" / "roadmap.yaml").exists())

    def test_adopt_refuses_when_no_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".wily").mkdir()
            with chdir(root):
                rc = init_cmd.main(["adopt-legacy"])
            self.assertEqual(rc, 1)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_init_adopt -v
```

Expected: `adopt-legacy` unknown subcommand.

- [ ] **Step 3: Write minimal implementation**

Add to `cli/init.py`:

```python
# Add at top:
from datetime import date
import shutil

# Add to the dispatcher near the other subcommands:
    if sub == "adopt-legacy":
        return _adopt_legacy(paths)

# New function:
def _adopt_legacy(paths: WilyPaths) -> int:
    legacy_marker = paths.wily_dir / "roadmap.yaml"
    if not legacy_marker.exists():
        _common.emit_error("no legacy roadmap.yaml found in .wily/")
        return _common.EXIT_FAILURE
    paths.archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    dest = paths.archive_dir / f"legacy-{stamp}"
    if dest.exists():
        suffix = 2
        while (paths.archive_dir / f"legacy-{stamp}-{suffix}").exists():
            suffix += 1
        dest = paths.archive_dir / f"legacy-{stamp}-{suffix}"
    dest.mkdir(parents=True)

    # Move every child of .wily/ EXCEPT archive/ and init/ (draft state we are keeping)
    for child in list(paths.wily_dir.iterdir()):
        if child.name in {"archive", "init"}:
            continue
        shutil.move(str(child), str(dest / child.name))

    _common.emit_text(f"legacy .wily/ archived to {dest.relative_to(paths.root)}")
    _common.emit_text("Run `wily init --adopt` to begin brownfield interview from this snapshot.")
    return _common.EXIT_OK
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_cli_init_adopt -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily/cli/init.py plugins/wily-roadmap/tests/v3/test_cli_init_adopt.py
git commit -m "feat(wily): wily init adopt-legacy archives v2 .wily/"
```

---

## Phase 10 — Launcher shim, skills, marketplace

### Task 10.1: Rewrite `scripts/wily.py` as thin entry shim

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily.py`
- Test: `plugins/wily-roadmap/tests/v3/test_entry_shim.py`

After this task, the old 4244-line `wily.py` is replaced by a small shim that forwards to `wily.cli.__main__`. Old behavior (v2 commands) goes away in Phase 11.

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_entry_shim.py`:

```python
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wily.py"


class EntryShimTest(unittest.TestCase):
    def test_no_args_prints_help_and_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            combined = result.stdout + result.stderr
            self.assertIn("init", combined)
            self.assertIn("watch", combined)

    def test_unknown_command_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "nonsense"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)

    def test_init_new_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".wily").mkdir()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "init", "--new"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_entry_shim -v
```

Expected: passes only when shim is in place.

- [ ] **Step 3: Replace `scripts/wily.py` with shim**

Overwrite `plugins/wily-roadmap/scripts/wily.py`:

```python
#!/usr/bin/env python3
"""Entry shim for wily v3.

The implementation lives in the `wily/` package alongside this file.
This shim exists because `.codex-plugin/plugin.json` and the repo-root
`wily` launcher both invoke `scripts/wily.py` by path.

If you are looking for v2 code, see git history before commit
`feat(wily): replace v2 wily.py with v3 entry shim`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from wily.cli.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_entry_shim -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/tests/v3/test_entry_shim.py
git commit -m "feat(wily): replace v2 wily.py with v3 entry shim"
```

After this commit, v2-only tests in `plugins/wily-roadmap/tests/test_wily_cli.py` will fail — that's expected, cleanup happens in Phase 11.

---

### Task 10.2: New SKILL.md files (11 skills)

**Files:**
- Create 11 directories under `plugins/wily-roadmap/skills/`:
  `wily-init/`, `wily-next/`, `wily-claim/`, `wily-go/`, `wily-done/`, `wily-block/`, `wily-replan/`, `wily-land/`, `wily-watch/`, `wily-status/`, `wily-execute/`
- Test: `plugins/wily-roadmap/tests/v3/test_skills_v3.py`

Each SKILL.md follows the same template. To avoid repetition this task uses one canonical template and a list of (skill, summary, internal_command) tuples Codex fills in.

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_skills_v3.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

V3_SKILLS = (
    "wily-init", "wily-next", "wily-claim", "wily-go", "wily-done",
    "wily-block", "wily-replan", "wily-land", "wily-watch", "wily-status",
    "wily-execute",
)


class V3SkillsTest(unittest.TestCase):
    def test_each_skill_exists_with_metadata(self) -> None:
        for name in V3_SKILLS:
            with self.subTest(skill=name):
                path = SKILLS / name / "SKILL.md"
                self.assertTrue(path.exists(), f"missing: {path}")
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"name: {name}", text)
                self.assertIn("description:", text)

    def test_wily_execute_describes_orchestration(self) -> None:
        text = (SKILLS / "wily-execute" / "SKILL.md").read_text(encoding="utf-8")
        # Must guide agents through claim -> go -> cw -> done sequence
        for token in ("wily claim", "wily go", "custom-workflow-skillset:plan-goal-runner", "wily done"):
            self.assertIn(token, text)

    def test_no_v2_only_skill_dirs(self) -> None:
        v2_only = {"wily-complete", "wily-start", "wily-decompose-stage",
                   "wily-retry", "wily-run", "wily-update", "wily-clean",
                   "wily-issues", "wily-workflow"}
        for name in v2_only:
            with self.subTest(skill=name):
                self.assertFalse(
                    (SKILLS / name).exists(),
                    f"v2 skill {name} should be removed in Phase 11",
                )
```

Note: the last assertion (`test_no_v2_only_skill_dirs`) will fail until Phase 11. Mark it `@unittest.expectedFailure` temporarily, or skip in this task and unskip in Phase 11. Use `unittest.skip` with reason `"v2 cleanup in Phase 11"`.

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_skills_v3 -v
```

Expected: missing skill files raise AssertionError.

- [ ] **Step 3: Write skill files**

Template (`plugins/wily-roadmap/skills/<name>/SKILL.md`):

```markdown
---
name: <name>
description: <one-line description>
metadata:
  short-description: <very short>
---

# <Title>

<One paragraph: what this command does, when to use it, what it changes.>

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py <subcommand> [args]
```

## Arguments

- <enumerate args/options>

## Behavior

- <bullet list of side effects / state changes>

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Report the result, the relevant path/artifact, and the next action or blocker.
- Do not echo internal helper commands in normal user-facing responses.
```

Per-skill content (Codex fills in from spec §5):

| Skill | description | subcommand |
|-------|-------------|------------|
| `wily-init` | Use when the user types $wily-init or asks to start the wily v3 interview (greenfield or brownfield adopt). | `init [--new\|--adopt\|answer\|...]` |
| `wily-next` | Use when the user types $wily-next or asks which task to pick up. | `next [--mine\|--json]` |
| `wily-claim` | Use when the user types $wily-claim or says they are about to start a task. | `claim <id> [--force]` |
| `wily-go` | Use when the user types $wily-go to get the goal text to hand to custom-workflow. | `go <id> [--json]` |
| `wily-done` | Use when the user types $wily-done after verifying a task. | `done <id> [--note\|--observed\|--force]` |
| `wily-block` | Use when the user types $wily-block and a task cannot continue. | `block <id> <reason>` |
| `wily-replan` | Use when the user types $wily-replan to revise task list (add/revise/drop/assign). | `replan [add\|revise-task\|drop\|assign\|commit\|cancel]` |
| `wily-land` | Use when the user types $wily-land after a task is done and wants commit/push. | `land <id> [--no-push\|--force]` |
| `wily-watch` | Use when the user types $wily-watch for a continuously refreshing roadmap pane. | `watch [--once\|--interval N]` |
| `wily-status` | Use when the user types $wily-status for a one-shot project snapshot. | `status [--json]` |

`wily-execute` is the meta-guide. Its body:

```markdown
---
name: wily-execute
description: Use when the user asks an agent to execute a Wily task end-to-end via custom-workflow. Routes claim -> go -> cw invocation -> done in order.
metadata:
  short-description: Drive a Wily task through custom-workflow
---

# Wily Execute

When the user asks "T03 cw로 진행해줘" or "wily 다음 task 처리해줘", run this orchestration:

1. `wily status` (or `wily next`) — confirm the task is ready and assigned correctly.
2. `wily claim <id>` — flip status to in_progress; record actor + claim SHA.
3. `wily go <id>` — capture the goal text. Hand the entire block (between the `====` markers) to `custom-workflow-skillset:plan-goal-runner`.
4. Run custom-workflow. cw will append cp events to `.wily/tasks/<id>/progress.jsonl` and put `Wily-Task: <id>` / `Wily-CP: <name>` trailers on its commits.
5. When cw finishes, compare its result to each `acceptance` item in the task. If scope drift (files modified outside `scope`), report it before proceeding.
6. `wily done <id>` — flip to done and write `result.md`.
7. Only after the user explicitly approves: `wily land <id>` — commit and push.

Guardrails:
- Never call `wily done` if cw failed or the user did not approve.
- Never call `wily land` without explicit user approval.
- For another actor's observed work, use `wily done <id> --observed` only when the user asks you to close it on their behalf.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Report the task id, current step, and next required action or blocker.
- Do not echo internal helper commands in normal user-facing responses.
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_skills_v3 -v
```

Expected: 2 tests pass; 1 skipped.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/skills/wily-init plugins/wily-roadmap/skills/wily-next \
        plugins/wily-roadmap/skills/wily-claim plugins/wily-roadmap/skills/wily-go \
        plugins/wily-roadmap/skills/wily-done plugins/wily-roadmap/skills/wily-block \
        plugins/wily-roadmap/skills/wily-replan plugins/wily-roadmap/skills/wily-land \
        plugins/wily-roadmap/skills/wily-watch plugins/wily-roadmap/skills/wily-status \
        plugins/wily-roadmap/skills/wily-execute \
        plugins/wily-roadmap/tests/v3/test_skills_v3.py
git commit -m "feat(wily): v3 skills (10 commands + wily-execute meta-guide)"
```

---

### Task 10.3: Update plugin manifests

**Files:**
- Modify: `plugins/wily-roadmap/.codex-plugin/plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Test: `plugins/wily-roadmap/tests/v3/test_manifests.py`

- [ ] **Step 1: Write the failing test**

`plugins/wily-roadmap/tests/v3/test_manifests.py`:

```python
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT.parents[1] / ".agents" / "plugins" / "marketplace.json"

V3_COMMANDS = {
    "init", "next", "claim", "go", "done", "block",
    "replan", "land", "watch", "status",
}
V3_SKILLS = V3_COMMANDS | {"execute"}


class ManifestsTest(unittest.TestCase):
    def test_plugin_json_lists_v3_commands(self) -> None:
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        cmd_names = {c["name"] for c in data.get("commands", [])}
        self.assertEqual(cmd_names, V3_COMMANDS,
                         f"plugin.json commands mismatch: {cmd_names ^ V3_COMMANDS}")

    def test_plugin_json_lists_v3_skills(self) -> None:
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        skill_names = {s["name"] for s in data.get("skills", [])}
        expected = {f"wily-{x}" for x in V3_SKILLS}
        self.assertEqual(skill_names, expected)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_manifests -v
```

Expected: v2 command/skill set differs.

- [ ] **Step 3: Rewrite manifests**

`plugins/wily-roadmap/.codex-plugin/plugin.json` (preserve existing top-level metadata; replace `commands` and `skills` arrays). Each command points at `commands/<cmd>.md` (Codex creates trivial command markdown if missing — body is one paragraph + `$ARGUMENTS`), each skill at `skills/wily-<name>/SKILL.md`.

`.agents/plugins/marketplace.json`: bump the version (e.g., `3.0.0`) and keep the entry pointing at `plugins/wily-roadmap`.

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_manifests -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/.codex-plugin/plugin.json \
        plugins/wily-roadmap/commands \
        .agents/plugins/marketplace.json \
        plugins/wily-roadmap/tests/v3/test_manifests.py
git commit -m "feat(wily): v3 plugin manifests and command stubs"
```

---

## Phase 11 — v2 cleanup + adopt this repo

### Task 11.1: Remove v2 skill directories

**Files:**
- Delete: 16 v2 skill dirs (all except those reused in v3)
- Modify: `plugins/wily-roadmap/tests/v3/test_skills_v3.py` (unskip the v2-removal assertion)

- [ ] **Step 1: List v2 skill directories**

```bash
ls plugins/wily-roadmap/skills/
```

v2 skills not in v3 set: `wily-complete`, `wily-start`, `wily-decompose-stage`, `wily-retry`, `wily-run`, `wily-update`, `wily-clean`, `wily-issues`, `wily-workflow`.

v3 skills exist with same name as some v2 skills (`wily-init`, `wily-next`, `wily-block`, `wily-replan`, `wily-land`, `wily-watch`, `wily-status`) — those were already rewritten in Task 10.2.

- [ ] **Step 2: Remove the v2-only directories**

```bash
for name in wily-complete wily-start wily-decompose-stage wily-retry \
            wily-run wily-update wily-clean wily-issues wily-workflow; do
  rm -rf "plugins/wily-roadmap/skills/${name}"
done
```

- [ ] **Step 3: Re-enable the v2-removal test assertion**

In `plugins/wily-roadmap/tests/v3/test_skills_v3.py`, remove the `@unittest.skip` decorator on `test_no_v2_only_skill_dirs` if one was added in Task 10.2.

- [ ] **Step 4: Run the test to verify**

```bash
python3 -m unittest plugins.wily-roadmap.tests.v3.test_skills_v3 -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/wily-roadmap/skills plugins/wily-roadmap/tests/v3/test_skills_v3.py
git commit -m "chore(wily): remove v2-only skill directories"
```

---

### Task 11.2: Remove v2 tests

**Files:**
- Delete: `plugins/wily-roadmap/tests/test_wily_cli.py` (v2 monolith test, 1900+ lines)
- Delete: `plugins/wily-roadmap/tests/test_wily_command_skills.py`
- Delete: `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- Delete: any other `tests/test_*.py` whose body imports the v2 monolithic `wily.py` API (e.g. `command_complete`, `emit_board_live_event`).

- [ ] **Step 1: Identify v2 tests**

```bash
grep -lE "command_complete|emit_board_live_event|wily-roadmap-v2|find_stage_phase" plugins/wily-roadmap/tests/*.py
```

- [ ] **Step 2: Delete listed files**

```bash
git rm plugins/wily-roadmap/tests/test_wily_cli.py
git rm plugins/wily-roadmap/tests/test_wily_command_skills.py
git rm plugins/wily-roadmap/tests/test_wily_state_summary.py
# add any others from step 1
```

- [ ] **Step 3: Run full test suite**

```bash
python3 -m unittest discover -s plugins/wily-roadmap/tests -v
```

Expected: only v3 tests run; all pass.

- [ ] **Step 4: Verify no leftover imports**

```bash
grep -rE "command_complete|emit_board_live_event" plugins/wily-roadmap/
```

Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(wily): remove v2 test files tied to deleted code"
```

---

### Task 11.3: Adopt this repo's `.wily/` to v3 (live migration)

**Files:**
- `.wily/` (this repository's own state)

This is the e2e proof. Performed against the real repository.

- [ ] **Step 1: Archive existing v2 state**

```bash
python3 plugins/wily-roadmap/scripts/wily.py init adopt-legacy
```

Expected: `legacy .wily/ archived to .wily/archive/legacy-2026-05-18`.

- [ ] **Step 2: Start the brownfield interview**

```bash
python3 plugins/wily-roadmap/scripts/wily.py init --adopt
```

Expected: first prompt is `analysis_confirm` with auto-analysis (commit count, authors, top-level files, legacy_wily_detected=True).

- [ ] **Step 3: Answer interview questions**

Sample answers (Codex fills in real values from the spec):

```bash
python3 plugins/wily-roadmap/scripts/wily.py init answer "ok"
python3 plugins/wily-roadmap/scripts/wily.py init answer "wily-roadmap v3: 박사 개인 추적기 + 라이트 협업 가시화"
python3 plugins/wily-roadmap/scripts/wily.py init answer "Wily 박사 + Right 박사"
python3 plugins/wily-roadmap/scripts/wily.py init answer "tasks.yaml + watch가 일관되게 동작; 별도 분해 단계 없음"
python3 plugins/wily-roadmap/scripts/wily.py init answer "외부 LLM 호출 안 함; wily-board 통합 안 함"
python3 plugins/wily-roadmap/scripts/wily.py init answer "wily Wily 박사, emails=kokyuhyun@goedu.kr"
```

- [ ] **Step 4: Build the task list manually**

```bash
python3 plugins/wily-roadmap/scripts/wily.py init add-task "Stabilize v3 in this repo"
python3 plugins/wily-roadmap/scripts/wily.py init revise-task T01 intent "v3 redesign now applied to this repo; future work uses v3 commands only"
python3 plugins/wily-roadmap/scripts/wily.py init revise-task T01 acceptance "wily watch shows the project; tasks.yaml/actors.yaml present; v2 archive preserved"
python3 plugins/wily-roadmap/scripts/wily.py init revise-task T01 scope "plugins/wily-roadmap/scripts/wily/*,plugins/wily-roadmap/skills/*"
python3 plugins/wily-roadmap/scripts/wily.py init assign T01 wily
python3 plugins/wily-roadmap/scripts/wily.py init commit
```

Expected: `init committed: 1 task(s), 1 actor(s)`.

- [ ] **Step 5: Verify + commit**

```bash
python3 plugins/wily-roadmap/scripts/wily.py status
```

Expected: project title shown, `T01 ready wily`, mode `solo`.

```bash
git status --short
git add .wily/
git commit -m "chore(wily): adopt v3 schema, archive v2 state under .wily/archive/"
```

---

### Task 11.4: External cleanup guidance

**Files:**
- Modify: `README.md` (mention v3, point to spec/plan)
- Output: human-readable cleanup notes

Old GitHub Actions workflow (`Notify Wily Board`), Codex `~/.codex/hooks.json` PostToolUse entry, and `~/.wily/board.json` are owned by other repos / user environment. wily must not silently mutate them.

- [ ] **Step 1: Update README**

In `README.md`, replace any v2-specific instructions with a short pointer:

```markdown
## wily-roadmap v3

Project + flat goal-sized Task manager. See:

- Spec: `docs/superpowers/specs/2026-05-18-wily-redesign-design.md`
- Plan: `docs/superpowers/plans/2026-05-18-wily-roadmap-v3.md`

Run from this repo:

```bash
./wily watch
./wily next
```
```

- [ ] **Step 2: Emit cleanup checklist to the user (do not auto-execute)**

Print this list to stdout from Codex once Task 11.3 succeeds:

```
v3 adoption complete. Manual cleanup actions (do these only with user approval):

1. Codex hooks: edit ~/.codex/hooks.json and remove any PostToolUse entry that runs
   `plugins/wily-roadmap/scripts/wily.py live-worked` (or similar). v3 has no
   live-* commands.

2. GitHub Actions: delete `.github/workflows/wily-board-sync.yml` (or equivalent)
   in a follow-up PR. The wily-board service is being retired in a separate spec.

3. Stale config: `~/.wily/board.json` can be deleted; v3 ignores it.

4. Branch: when v3 lands, archive the legacy `wily-roadmap-v2` branch reference
   if you keep one; otherwise main now carries the v3 surface.
```

- [ ] **Step 3: Run the full test suite one final time**

```bash
python3 -m unittest discover -s plugins/wily-roadmap/tests -v
```

Expected: all v3 tests pass; no v2 tests remain.

- [ ] **Step 4: Verify external surface is clean**

```bash
grep -rE "wily-board|emit_board_live_event|wily-roadmap-v2" plugins/wily-roadmap/
```

Expected: zero matches in code; matches only inside `docs/superpowers/` (historical references).

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs(wily): point README at v3 spec and plan"
```

---

## Done definition

When all phases complete, this branch (`feat/wily-v3-redesign`) satisfies:

1. `plugins/wily-roadmap/scripts/wily/` package implements all 10 commands.
2. `plugins/wily-roadmap/skills/` contains exactly 11 skill directories (10 commands + `wily-execute`).
3. v2 board code, v2 commands, v2 tests, and v2 skill directories are removed.
4. This repo's `.wily/` was migrated via `wily init --adopt`; v2 state is preserved under `.wily/archive/legacy-2026-05-18/`.
5. `python3 -m unittest discover -s plugins/wily-roadmap/tests` passes.
6. Plugin manifests (`plugin.json`, `marketplace.json`) list the v3 surface only.
7. `~/.codex/hooks.json` and `.github/workflows/*.yml` cleanup is documented for the user to perform; wily does not mutate them.

Push (`git push -u origin feat/wily-v3-redesign`) and PR creation are deferred to the user — not part of this plan.


