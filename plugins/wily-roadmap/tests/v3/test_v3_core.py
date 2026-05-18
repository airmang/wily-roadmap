from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wily.py"
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import block as block_cmd, next as next_cmd, replan as replan_cmd, watch as watch_cmd  # noqa: E402
from wily.cli import init as init_cmd  # noqa: E402
from wily.config import load_actors, load_tasks, save_actors, save_tasks  # noqa: E402
from wily.models import Actor, Task, TaskStatus  # noqa: E402
from wily.observation import observation_base  # noqa: E402
from wily.paths import WilyPaths, WilyRootNotFound, find_wily_root  # noqa: E402
from wily.progress import CpEvent, CpSummary, append_event, cp_summary, init_progress  # noqa: E402
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

    def test_watch_renderer_shows_task_detail_rows_in_ascii(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(
                    id="T01",
                    title="First",
                    status=TaskStatus.IN_PROGRESS,
                    assignee="wily",
                    blocker="waiting for review",
                ),
            ],
            actors=[],
            observed_commits=[],
            cp_summaries={"T01": CpSummary(total=3, done=1, in_progress=1, current_cp="verify")},
            mode="solo",
            ui="ascii",
        )
        self.assertIn("Wily Roadmap v3", output)
        self.assertIn("\\- ~ T01", output)
        self.assertIn("cp [#--] 1/3 cp current:verify", output)
        self.assertIn("blocker: waiting for review", output)

    def test_watch_launch_mode_selects_tmux_pane_by_default(self) -> None:
        self.assertEqual(
            watch_cmd.watch_launch_mode(
                ["--interval", "1"],
                in_tmux=True,
                stdin_tty=True,
                stdout_tty=True,
            ),
            "pane",
        )
        self.assertEqual(
            watch_cmd.watch_launch_mode(["--here"], in_tmux=True, stdin_tty=True, stdout_tty=True),
            "here",
        )
        self.assertEqual(
            watch_cmd.watch_launch_mode([], in_tmux=False, stdin_tty=True, stdout_tty=True),
            "here",
        )
        self.assertEqual(
            watch_cmd.watch_launch_mode([], in_tmux=False, stdin_tty=False, stdout_tty=False),
            "needs_interactive_terminal",
        )

    def test_tmux_watch_command_opens_horizontal_split_on_current_pane(self) -> None:
        root = Path("/tmp/demo repo")
        command = watch_cmd.tmux_watch_command(
            root,
            ["--interval", "1.5", "--ui", "ascii"],
            script=Path("/tmp/wily.py"),
            python="python3",
            current_pane="%7",
        )
        self.assertEqual(command[:4], ["tmux", "split-window", "-t", "%7"])
        self.assertEqual(command[4], "-h")
        inner = command[5]
        self.assertIn("cd '/tmp/demo repo'", inner)
        self.assertIn("python3 /tmp/wily.py watch --here --ui ascii --interval 1.5", inner)

    def test_watch_status_args_strip_watch_only_flags(self) -> None:
        self.assertEqual(
            watch_cmd.status_args_from_watch_args(
                ["--here", "--interval", "1", "--ui", "ascii", "--dry-run-pane", "--no-interactive"]
            ),
            ["--ui", "ascii"],
        )

    def test_watch_rejects_invalid_ui_before_launching_pane(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertIsNone(watch_cmd.watch_ui(["--ui", "wide"]))
            self.assertIsNone(watch_cmd.watch_ui(["--ui"]))
        self.assertEqual(stderr.getvalue().count("--ui requires"), 2)


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
            watch = subprocess.run(
                [sys.executable, str(SCRIPT), "watch", "--once", "--ui", "ascii"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(watch.returncode, 0)
            self.assertIn("Wily Roadmap v3", watch.stdout)
            self.assertIn("\\- * T01", watch.stdout)

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
