from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wily.py"
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import block as block_cmd, next as next_cmd, replan as replan_cmd  # noqa: E402
from wily.cli import init as init_cmd  # noqa: E402
from wily.config import load_actors, load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.observation import observation_base  # noqa: E402
from wily.paths import WilyPaths, WilyRootNotFound, find_wily_root  # noqa: E402
from wily.progress import CpEvent, append_event, cp_summary, init_progress  # noqa: E402
from wily.transitions import DependencyError, TransitionError, apply_claim, apply_done, check_dependencies  # noqa: E402
from wily.ui.watch_render import render_watch  # noqa: E402


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "wily@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=path, check=True)
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


class CoreModelTest(unittest.TestCase):
    def test_paths_config_and_progress_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".wily").mkdir()
            paths = WilyPaths(root)
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First")])
            title, tasks = load_tasks(paths)
            self.assertEqual(title, "demo")
            self.assertEqual(tasks[0].status, TaskStatus.READY)
            self.assertEqual(load_actors(paths)[0].id, "wily")
            init_progress(paths, "T01")
            append_event(paths, "T01", CpEvent(ts="2026-05-18T00:00:00Z", actor="wily", cp="plan", event="start"))
            append_event(paths, "T01", CpEvent(ts="2026-05-18T00:01:00Z", actor="wily", cp="plan", event="done"))
            summary = cp_summary(paths, "T01")
            self.assertEqual((summary.total, summary.done), (1, 1))

    def test_transitions_and_dependency_errors(self) -> None:
        task = Task(id="T01", title="x")
        claimed = apply_claim(task, actor="wily", sha="abc", at="now")
        self.assertEqual(claimed.status, TaskStatus.IN_PROGRESS)
        done = apply_done(claimed, at="later")
        self.assertEqual(done.status, TaskStatus.DONE)
        with self.assertRaises(TransitionError):
            apply_claim(done, actor="wily", sha="abc", at="now")
        with self.assertRaises(DependencyError):
            check_dependencies([Task(id="T01", title="a", depends_on=["T02"]), Task(id="T02", title="b", depends_on=["T01"])])

    def test_find_wily_root_walks_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".wily").mkdir()
            child = root / "a" / "b"
            child.mkdir(parents=True)
            self.assertEqual(find_wily_root(child), root.resolve())
            with self.assertRaises(WilyRootNotFound):
                find_wily_root(root.parent)

    def test_watch_renderer_keeps_rich_pipeline_shape(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(id="T01", title="First", status=TaskStatus.DONE, assignee="wily"),
                Task(id="T02", title="Second", status=TaskStatus.IN_PROGRESS, assignee="right"),
                Task(id="T03", title="Third", status=TaskStatus.READY, assignee="wily"),
            ],
            actors=[Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])],
            observed_commits=[],
            cp_summaries={},
            mode="shared",
        )
        self.assertIn("Wily Roadmap v3", output)
        self.assertIn("▕", output)
        self.assertIn("▏", output)
        self.assertIn("├─", output)
        self.assertIn("└─", output)
        self.assertIn("▶", output)


class CliLifecycleTest(unittest.TestCase):
    def test_init_claim_go_done_status_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            env = os.environ.copy()
            commands = [
                ["init", "--new"],
                ["init", "answer", "Demo Project"],
                ["init", "answer", "Wily"],
                ["init", "answer", "tasks done"],
                ["init", "answer", "no board"],
                ["init", "answer", "wily Wily, emails=wily@example.com"],
                ["init", "add-task", "First task"],
                ["init", "revise-task", "T01", "intent", "do it"],
                ["init", "revise-task", "T01", "acceptance", "done output exists"],
                ["init", "revise-task", "T01", "scope", "work.txt"],
                ["init", "assign", "T01", "wily"],
                ["init", "commit"],
            ]
            for args in commands:
                result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "claim", "T01"], cwd=root, capture_output=True, text=True).returncode, 0)
            go = subprocess.run([sys.executable, str(SCRIPT), "go", "T01"], cwd=root, capture_output=True, text=True)
            self.assertEqual(go.returncode, 0)
            self.assertIn("Wily Task T01", go.stdout)
            (root / "work.txt").write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "add", "work.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "work"], cwd=root, check=True)
            self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "done", "T01"], cwd=root, capture_output=True, text=True).returncode, 0)
            status = subprocess.run([sys.executable, str(SCRIPT), "status", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(status.returncode, 0)
            payload = json.loads(status.stdout)
            self.assertEqual(payload["tasks"][0]["status"], "done")
            self.assertTrue((root / ".wily" / "tasks" / "T01" / "result.md").exists())

    def test_removed_v2_command_exits_usage(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "run", "T01"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("removed in wily v3", result.stderr)

    def test_legacy_hook_commands_are_removed(self) -> None:
        legacy_hook_command = "live" + "-worked"
        result = subprocess.run([sys.executable, str(SCRIPT), legacy_hook_command], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        hook_result = subprocess.run(
            [sys.executable, str(SCRIPT), legacy_hook_command, "--from-hook", "--agent", "codex"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(hook_result.returncode, 0)

    def test_block_replan_adopt_and_next_mine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", assignee="right")])
            with chdir_compat(root):
                self.assertEqual(block_cmd.main(["T01", "waiting"]), 0)
                _, tasks = load_tasks(paths)
                self.assertEqual(tasks[0].status, TaskStatus.BLOCKED)
                self.assertEqual(replan_cmd.main(["add", "Second"]), 0)
                self.assertEqual(replan_cmd.main(["revise-task", "T02", "depends_on", "T01"]), 0)
                self.assertEqual(replan_cmd.main(["assign", "T02", "wily"]), 0)
                self.assertEqual(replan_cmd.main(["commit"]), 0)
                self.assertEqual(next_cmd.main(["--mine"]), 1)
            (paths.wily_dir / "roadmap.yaml").write_text("roadmap_schema: old\n", encoding="utf-8")
            with chdir_compat(root):
                self.assertEqual(init_cmd.main(["adopt-legacy"]), 0)
            self.assertTrue(any(paths.archive_dir.glob("legacy-*/roadmap.yaml")))

    def test_status_observation_does_not_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            remote = root / "remote.git"
            subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=root, check=True)
            base = observation_base(root)
            self.assertEqual(base, subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip())
            remote_refs = subprocess.run(["git", "show-ref", "--verify", "refs/remotes/origin/main"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(remote_refs.returncode, 0)


if __name__ == "__main__":
    unittest.main()


class chdir_compat:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.old: str | None = None

    def __enter__(self) -> None:
        self.old = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, *_exc) -> None:
        if self.old is not None:
            os.chdir(self.old)
