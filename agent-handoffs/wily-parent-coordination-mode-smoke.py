from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "wily-roadmap" / "scripts" / "wily.py"
sys.path.insert(0, str(ROOT / "plugins" / "wily-roadmap" / "scripts"))

from wily.config import save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.observation import claim_snapshot_for_repos  # noqa: E402
from wily.paths import WilyPaths  # noqa: E402


def run(args: list[str], cwd: Path, ok: set[int]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode not in ok:
        raise AssertionError(f"{args} cwd={cwd} rc={result.returncode}\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    return result


def git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "wily@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=path, check=True)
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


def write_coordination(parent: Path, repos: tuple[tuple[str, str], ...]) -> None:
    wily = parent / ".wily"
    wily.mkdir(exist_ok=True)
    lines = ["schema: wily-coordination-v1", "title: Parent Project", "parent:", "  id: parent", "  path: .", "repos:"]
    for repo_id, rel_path in repos:
        lines.extend([f"  - id: {repo_id}", f"    path: {rel_path}"])
    (wily / "coordination.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def setup_parent(base: Path, repos: tuple[tuple[str, str], ...] = (("roadmap", "./wily-roadmap"),)) -> tuple[Path, dict[str, Path], WilyPaths]:
    base.mkdir(parents=True, exist_ok=True)
    parent = base / "workspace"
    parent.mkdir()
    children = {}
    for repo_id, rel_path in repos:
        child = parent / rel_path.removeprefix("./")
        child.mkdir(parents=True)
        git_repo(child)
        children[repo_id] = child
    write_coordination(parent, repos)
    paths = WilyPaths(parent)
    save_actors(paths, [Actor(id="wily", display="Wily")])
    return parent, children, paths


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wily-coordination-smoke-") as tmp:
        base = Path(tmp)

        parent, children, paths = setup_parent(base / "lifecycle")
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Lifecycle", intent="do it", acceptance="done", scope=["roadmap:src/**"]), Task(id="T02", title="Next ready", intent="do it", acceptance="done")])
        run(["claim", "T01", "--as", "wily", "--json"], parent, {0})
        (parent / "agent-handoffs").mkdir()
        (parent / "agent-handoffs" / "status.md").write_text("| Checkpoint | Status | Evidence |\n| --- | --- | --- |\n| Plan | DONE | ok |\n", encoding="utf-8")
        run(["cp", "T01", "import-status", "agent-handoffs/status.md", "--actor", "wily"], parent, {0})
        child = children["roadmap"]
        (child / "src").mkdir()
        (child / "src" / "app.py").write_text("app\n", encoding="utf-8")
        done = run(["done", "T01", "--json"], parent, {0})
        status = run(["status", "--json"], parent, {0, 1, 2})
        next_result = run(["next", "--json"], parent, {0})
        watch = run(["watch", "--json"], parent, {0, 1, 2})
        assert json.loads(status.stdout)["active_mode"] == "coordination"
        assert json.loads(watch.stdout)["tasks"][0]["id"] == "T01"
        assert json.loads(next_result.stdout)["task"]["id"] == "T02"
        assert json.loads(done.stdout)["changed_files"] == ["roadmap:src/app.py"]
        print("PASS lifecycle claim/cp/done/status/next/watch")

        parent, _children, paths = setup_parent(base / "parent-block")
        (parent / "docs").mkdir()
        (parent / "docs" / "spec.md").write_text("parent\n", encoding="utf-8")
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Parent block", status=TaskStatus.DONE, scope=["parent:docs/**"])])
        parent_block = run(["land", "T01", "--dry-run", "--json"], parent, {3})
        assert json.loads(parent_block.stdout)["errors"][0]["code"] == "parent_not_git"
        real_parent_block = run(["land", "T01", "--json"], parent, {3})
        assert json.loads(real_parent_block.stdout)["errors"][0]["code"] == "parent_not_git"
        print("PASS parent-scoped dry-run and land block without parent git")

        parent, children, paths = setup_parent(base / "out-of-scope")
        snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", children["roadmap"])])
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Out scope", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)])
        child = children["roadmap"]
        (child / "src").mkdir()
        (child / "src" / "app.py").write_text("app\n", encoding="utf-8")
        (child / "docs").mkdir()
        (child / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")
        out_scope = run(["land", "T01", "--dry-run", "--json"], parent, {3})
        real_out_scope = run(["land", "T01", "--json"], parent, {3})
        assert json.loads(out_scope.stdout)["repos"]["roadmap"]["out_of_scope_changes"] == ["docs/outside.md"]
        assert json.loads(real_out_scope.stdout)["errors"][0]["code"] == "out_of_scope_changes"
        assert subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=child, capture_output=True, text=True, check=True).stdout.strip() == ""
        print("PASS out-of-scope dry-run and land block before staging")

        parent, children, paths = setup_parent(base / "child-land")
        child = children["roadmap"]
        snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Child land", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)])
        paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
        paths.result_md("T01").write_text("# result\n", encoding="utf-8")
        (child / "src").mkdir()
        (child / "src" / "app.py").write_text("app\n", encoding="utf-8")
        child_dry = run(["land", "T01", "--dry-run", "--json"], parent, {0})
        assert ".wily/tasks.yaml" in json.loads(child_dry.stdout)["parent_ledger_changes"]
        run(["land", "T01", "--no-push"], parent, {0})
        assert "Wily-Task: T01" in subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=child, capture_output=True, text=True, check=True).stdout
        print("PASS child-only dry-run and land commit")

        parent, children, paths = setup_parent(base / "multi", repos=(("roadmap", "./wily-roadmap"), ("board", "./wily-board")))
        roadmap, board = children["roadmap"], children["board"]
        snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", roadmap), ("board", board)])
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Multi", status=TaskStatus.DONE, scope=["roadmap:src/**", "board:app/**"], claim_snapshot=snapshot)])
        (roadmap / "src").mkdir()
        (roadmap / "src" / "app.py").write_text("app\n", encoding="utf-8")
        (board / "app").mkdir()
        (board / "app" / "ui.py").write_text("ui\n", encoding="utf-8")
        run(["land", "T01", "--dry-run", "--json"], parent, {0})
        run(["land", "T01", "--no-push"], parent, {0})
        for repo in (roadmap, board):
            assert "Wily-Task: T01" in subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout
        print("PASS multi-repo dry-run and per-repo commits")

        parent, children, paths = setup_parent(base / "dirty")
        child = children["roadmap"]
        (child / "src").mkdir()
        (child / "src" / "pre.py").write_text("pre\n", encoding="utf-8")
        (child / "src" / "mixed.py").write_text("before\n", encoding="utf-8")
        snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Dirty", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)])
        (child / "src" / "mixed.py").write_text("after\n", encoding="utf-8")
        (child / "src" / "new.py").write_text("new\n", encoding="utf-8")
        dirty = run(["land", "T01", "--dry-run", "--json"], parent, {3})
        dirty_payload = json.loads(dirty.stdout)["repos"]["roadmap"]
        assert dirty_payload["pre_existing_dirty"] == ["src/pre.py"]
        assert dirty_payload["mixed_files"] == ["src/mixed.py"]
        assert dirty_payload["task_candidate_changes"] == ["src/new.py"]
        print("PASS dirty baseline and mixed-file blocking")

        parent, children, paths = setup_parent(base / "child-local")
        child = children["roadmap"]
        save_tasks(paths, "Parent Project", [Task(id="T01", title="Parent ready")])
        save_tasks(WilyPaths(child), "Child Project", [Task(id="C01", title="Child ready")])
        child_next = run(["next", "--json"], child, {0})
        assert json.loads(child_next.stdout)["id"] == "C01"
        print("PASS child-local invocation precedence")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
