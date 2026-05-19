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

from wily.cli import agent as agent_cmd  # noqa: E402
from wily.cli import block as block_cmd, cp as cp_cmd, doctor as doctor_cmd, done as done_cmd, go as go_cmd, land as land_cmd, next as next_cmd, replan as replan_cmd, watch as watch_cmd  # noqa: E402
from wily.agent.config import AgentConfig  # noqa: E402
from wily.agent.daemon import run_once as agent_run_once  # noqa: E402
from wily.agent.registry import RegisteredRepo, load_registry, save_registry  # noqa: E402
from wily.cli import init as init_cmd  # noqa: E402
from wily.config import load_actors, load_tasks, save_actors, save_tasks  # noqa: E402
from wily.hooks.drift_guard import ensure_drift_stub  # noqa: E402
from wily.models import AcceptanceItem, Actor, Task, TaskStatus  # noqa: E402
from wily.observation import observation_base  # noqa: E402
from wily.paths import WilyPaths, WilyRootNotFound, find_wily_root, migrate_legacy_handoffs, touch_wily  # noqa: E402
from wily.progress import CpEvent, CpSummary, append_event, cp_summary, init_progress, read_ac_checks, read_events  # noqa: E402
from wily.scheduling import parallel_candidates, waiting_candidates  # noqa: E402
from wily.transitions import DependencyError, TransitionError, apply_block, apply_claim, apply_done, check_dependencies  # noqa: E402
from wily.ui.watch_layout import WatchLayoutConfig  # noqa: E402
from wily.ui.watch_activity import build_activity_lines  # noqa: E402
from wily.ui.watch_render import render_watch  # noqa: E402


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "wily@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=path, check=True)
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


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


class CoreModelTest(unittest.TestCase):
    def test_agent_launchd_plist_uses_plugin_launcher_and_repo_registry(self) -> None:
        plist = agent_cmd.launchd_plist(
            label="com.wily.roadmap.agent",
            python_executable="/usr/bin/python3",
            plugin_root=Path("/opt/wily-roadmap"),
            registry_path=Path("/Users/wily/.config/wily/agent/registry.json"),
            config_path=Path("/Users/wily/.config/wily/agent/config.json"),
            log_dir=Path("/Users/wily/Library/Logs/wily-agent"),
        )

        self.assertIn("/opt/wily-roadmap/scripts/wily.py", plist)
        self.assertIn("agent", plist)
        self.assertIn("dev", plist)
        self.assertIn("/Users/wily/.config/wily/agent/registry.json", plist)
        self.assertIn("/Users/wily/.config/wily/agent/config.json", plist)
        self.assertNotIn("/tmp/wily-agent", plist)

    def test_agent_foreground_command_uses_plugin_daemon_module(self) -> None:
        command = agent_cmd.foreground_command(
            python_executable="/usr/bin/python3",
            plugin_root=Path("/opt/wily-roadmap"),
            registry_path=Path("/Users/wily/.config/wily/agent/registry.json"),
            config_path=Path("/Users/wily/.config/wily/agent/config.json"),
            once=True,
        )

        self.assertEqual(command[:3], ["/usr/bin/python3", "/opt/wily-roadmap/scripts/wily.py", "agent"])
        self.assertIn("dev", command)
        self.assertIn("--once", command)
        self.assertIn("--offline-ok", command)

    def test_agent_daemon_reloads_registry_each_tick(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / ".wily").mkdir()
            paths = WilyPaths(repo)
            save_tasks(paths, "demo", [Task(id="T01", title="First")])
            registry_path = root / "registry.json"
            config = AgentConfig()

            self.assertEqual(agent_run_once(config, registry_path, offline_ok=True), [])
            save_registry(registry_path, [RegisteredRepo(path=repo, repo="R-W-LAB/demo")])
            result = agent_run_once(config, registry_path, offline_ok=True)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["reason"], "not configured")

    def test_agent_builds_board_v3_snapshot_payload_from_local_wily_state(self) -> None:
        from wily.agent.snapshot import build_snapshot_payload, snapshot_sha

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run(["git", "remote", "add", "origin", "git@github.com:R-W-LAB/demo.git"], cwd=root, check=True)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            paths.project_md.write_text("# Demo Project\n\nLocal project notes.\n", encoding="utf-8")
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"], capacity=2)])
            save_tasks(
                paths,
                "Demo Project",
                [
                    Task(
                        id="T01",
                        title="First task",
                        intent="Ship the first thing",
                        acceptance="It works",
                        scope=["plugins/**"],
                        status=TaskStatus.IN_PROGRESS,
                        actor="wily",
                        parallel_lane="agent",
                        priority=1,
                        capacity_hint=2,
                    )
                ],
            )
            init_progress(paths, "T01")
            append_event(paths, "T01", CpEvent(ts="2026-05-19T00:00:00Z", actor="wily", cp="plan", event="start"))
            append_event(paths, "T01", CpEvent(ts="2026-05-19T00:01:00Z", actor="wily", cp="plan", event="done"))
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# Result\n\nDone locally.\n", encoding="utf-8")

            payload = build_snapshot_payload(root, repo="R-W-LAB/demo", actor="wily")

            self.assertEqual(payload["repo"], "R-W-LAB/demo")
            self.assertTrue(payload["remote_url"].endswith("R-W-LAB/demo.git"))
            self.assertEqual(payload["title"], "Demo Project")
            self.assertEqual(payload["mode_hint"], "solo")
            self.assertEqual(payload["local_path"], str(root.resolve()))
            self.assertEqual(payload["tasks"][0]["id"], "T01")
            self.assertEqual(payload["actors"]["wily"]["display"], "Wily")
            self.assertEqual(payload["actors"]["wily"]["capacity"], 2)
            self.assertEqual(payload["task_progress"]["T01"]["done"], 1)
            self.assertEqual(payload["task_progress"]["T01"]["total"], 1)
            self.assertEqual(payload["cp_events"]["T01"][0]["cp"], "plan")
            self.assertIn("Done locally.", payload["task_results"]["T01"])
            self.assertIn("Local project notes.", payload["project_md"])
            self.assertEqual(payload["snapshot_sha"], snapshot_sha(payload))
            self.assertTrue(payload["observed_commits"])

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
            self.assertEqual(summary.cp_names, ["plan"])
            self.assertEqual(paths.handoff_dir("T01"), root / ".wily" / "handoffs" / "T01")
            self.assertEqual(paths.handoff_status_md("T01"), root / ".wily" / "handoffs" / "T01" / "status.md")
            touch_wily(paths)
            self.assertTrue((root / ".wily" / ".touch").exists())

    def test_state_loaders_accept_plain_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            paths.tasks_yaml.write_text(
                "\n".join(
                    [
                        "schema: wily-v3",
                        "project_title: Demo",
                        "tasks:",
                        "  - id: T01",
                        "    title: First",
                        "    status: ready",
                        "    depends_on: []",
                    ]
                ),
                encoding="utf-8",
            )
            paths.actors_yaml.write_text(
                "\n".join(
                    [
                        "schema: wily-v3",
                        "actors:",
                        "  wily:",
                        "    display: Wily",
                        "    git_author_emails:",
                        "      - wily@example.com",
                    ]
                ),
                encoding="utf-8",
            )

            title, tasks = load_tasks(paths)
            actors = load_actors(paths)

            self.assertEqual(title, "Demo")
            self.assertEqual(tasks[0].id, "T01")
            self.assertEqual(tasks[0].status, TaskStatus.READY)
            self.assertEqual(actors[0].git_author_emails, ["wily@example.com"])

    def test_cp_command_records_progress_for_watch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "demo",
                [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")],
            )

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "start", "plan", "--actor", "wily", "--ts", "2026-05-18T00:00:00Z"]), 0)
                self.assertEqual(cp_cmd.main(["T01", "done", "plan", "--actor", "wily", "--ts", "2026-05-18T00:01:00Z"]), 0)

            summary = cp_summary(paths, "T01")
            self.assertEqual((summary.total, summary.done, summary.current_cp), (1, 1, None))
            output = render_watch(
                project_title="Demo",
                tasks=[Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")],
                actors=[Actor(id="wily", display="Wily")],
                observed_commits=[],
                cp_summaries={"T01": summary},
                mode="solo",
                ui="ascii",
            )
            self.assertIn("체크포인트 [#] 1/1", output)

    def test_cp_command_appends_distinct_notes_for_same_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "note", "plan", "--note", "first", "--actor", "wily", "--ts", "2026-05-18T00:00:00Z"]), 0)
                self.assertEqual(cp_cmd.main(["T01", "note", "plan", "--note", "second", "--actor", "wily", "--ts", "2026-05-18T00:01:00Z"]), 0)

            events = read_events(paths, "T01")
            self.assertEqual([(event.event, event.note) for event in events], [("note", "first"), ("note", "second")])

    def test_cp_cli_dispatch_records_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "cp",
                    "T01",
                    "start",
                    "plan",
                    "--actor",
                    "wily",
                    "--ts",
                    "2026-05-18T00:00:00Z",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("T01 cp start: plan", result.stdout)
            self.assertEqual(cp_summary(paths, "T01").current_cp, "plan")
            self.assertTrue(paths.touch_file.exists())

    def test_claim_and_block_update_wily_touch_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", intent="do", acceptance="done")])

            with chdir_compat(root):
                self.assertEqual(
                    subprocess.run([sys.executable, str(SCRIPT), "claim", "T01"], cwd=root, capture_output=True, text=True).returncode,
                    0,
                )
                first_touch = paths.touch_file.stat().st_mtime_ns
                self.assertEqual(block_cmd.main(["T01", "waiting"]), 0)

            self.assertGreaterEqual(paths.touch_file.stat().st_mtime_ns, first_touch)

    def test_watch_redraws_only_when_touch_mtime_changes(self) -> None:
        self.assertTrue(watch_cmd.should_redraw(None, 1))
        self.assertFalse(watch_cmd.should_redraw(1, 1))
        self.assertTrue(watch_cmd.should_redraw(1, 2))

    def test_doctor_reports_failures_warnings_and_fixable_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="Active", status=TaskStatus.IN_PROGRESS, actor="ghost", claim_sha="abc"),
                    Task(id="T02", title="Waiting", depends_on=["T99"]),
                ],
            )
            paths.task_dir("T77").mkdir(parents=True)

            with chdir_compat(root):
                stderr = StringIO()
                with redirect_stderr(stderr):
                    self.assertEqual(doctor_cmd.main([]), 2)
                output = stderr.getvalue()
                self.assertIn("broken depends_on", output)
                self.assertIn("missing actor", output)
                self.assertIn("missing progress.jsonl", output)
                self.assertIn("orphan task dir", output)

                with redirect_stderr(StringIO()):
                    self.assertEqual(doctor_cmd.main(["--fix"]), 2)

            self.assertTrue(paths.progress_jsonl("T01").exists())

    def test_doctor_ok_when_required_state_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            (root / ".venv").mkdir()
            hook = root / ".git" / "hooks" / "pre-commit"
            hook.write_text("python wily.py replan drift-guard --from-hook\n", encoding="utf-8")
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="Active", status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha="abc")])
            paths.progress_jsonl("T01").parent.mkdir(parents=True)
            paths.progress_jsonl("T01").write_text("", encoding="utf-8")

            with chdir_compat(root):
                self.assertEqual(doctor_cmd.main([]), 0)

    def test_cp_import_status_converts_custom_workflow_board_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "demo",
                [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")],
            )
            status = root / "agent-handoffs" / "demo-status.md"
            status.parent.mkdir()
            status.write_text(
                "\n".join(
                    [
                        "| Checkpoint | Status | Evidence |",
                        "| --- | --- | --- |",
                        "| Execution package | DONE | created |",
                        "| RED tests | DONE | failed then passed |",
                        "| Implementation | RUNNING | current |",
                        "| Future | PENDING | waiting |",
                    ]
                ),
                encoding="utf-8",
            )

            with chdir_compat(root):
                args = ["T01", "import-status", str(status.relative_to(root)), "--actor", "wily", "--ts", "2026-05-18T00:00:00Z"]
                self.assertEqual(cp_cmd.main(args), 0)
                self.assertEqual(cp_cmd.main(args), 0)

            events = read_events(paths, "T01")
            self.assertEqual([(event.cp, event.event) for event in events], [
                ("Execution package", "start"),
                ("Execution package", "done"),
                ("RED tests", "start"),
                ("RED tests", "done"),
                ("Implementation", "start"),
            ])
            summary = cp_summary(paths, "T01")
            self.assertEqual((summary.total, summary.done, summary.current_cp), (3, 2, "Implementation"))

    def test_cp_import_status_uses_task_handoff_default_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            paths.handoff_dir("T01").mkdir(parents=True)
            paths.handoff_status_md("T01").write_text(
                "\n".join(
                    [
                        "| Checkpoint | Status | Evidence |",
                        "| --- | --- | --- |",
                        "| Plan | DONE | ok |",
                    ]
                ),
                encoding="utf-8",
            )

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "import-status", "--actor", "wily"]), 0)

            self.assertEqual([(event.cp, event.event) for event in read_events(paths, "T01")], [("Plan", "start"), ("Plan", "done")])

    def test_migrate_legacy_handoffs_moves_files_under_wily_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            legacy = root / "agent-handoffs"
            legacy.mkdir()
            (legacy / "t09-demo-status.md").write_text("status\n", encoding="utf-8")
            (legacy / "notes.md").write_text("notes\n", encoding="utf-8")

            moved = migrate_legacy_handoffs(paths)

            self.assertEqual(moved, 2)
            self.assertFalse((legacy / "t09-demo-status.md").exists())
            self.assertEqual((paths.handoff_dir("T09") / "t09-demo-status.md").read_text(encoding="utf-8"), "status\n")
            self.assertEqual((paths.handoff_dir("legacy") / "notes.md").read_text(encoding="utf-8"), "notes\n")
            self.assertEqual(migrate_legacy_handoffs(paths), 0)

    def test_cp_import_status_imports_acceptance_check_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "demo-status.md"
            status.parent.mkdir()
            status.write_text(
                "\n".join(
                    [
                        "| AC | Status | Evidence |",
                        "| --- | --- | --- |",
                        "| 1 | pass | unit tests |",
                        "| 2 | fail | missing docs |",
                    ]
                ),
                encoding="utf-8",
            )

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "import-status", str(status.relative_to(root)), "--actor", "wily"]), 0)

            checks = read_ac_checks(paths, "T01")
            self.assertEqual(
                [(check.index, check.status, check.evidence) for check in checks],
                [(1, "pass", "unit tests"), (2, "fail", "missing docs")],
            )

    def test_cp_import_status_blocked_checkpoint_does_not_remain_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "blocked-status.md"
            status.parent.mkdir()
            status.write_text(
                "\n".join(
                    [
                        "| Checkpoint | Status | Evidence |",
                        "| --- | --- | --- |",
                        "| Implementation | BLOCKED | waiting on API |",
                    ]
                ),
                encoding="utf-8",
            )

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "import-status", str(status.relative_to(root)), "--actor", "wily"]), 0)

            self.assertEqual(cp_summary(paths, "T01").in_progress, 0)

    def test_cp_import_status_dry_run_reports_unrecognized_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "odd-status.md"
            status.parent.mkdir()
            status.write_text("plain text status\n| Checkpoint | State | Evidence |\n| --- | --- | --- |\n| Plan | DONE | ok |\n", encoding="utf-8")

            with chdir_compat(root):
                stderr = StringIO()
                with redirect_stderr(stderr):
                    code = cp_cmd.main(["T01", "import-status", str(status.relative_to(root)), "--dry-run"])

            self.assertEqual(code, 0)
            self.assertIn("unrecognized status line", stderr.getvalue())
            self.assertEqual(read_events(paths, "T01"), [])

    def test_parallel_metadata_round_trips_without_breaking_legacy_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".wily").mkdir()
            paths = WilyPaths(root)
            save_actors(paths, [Actor(id="wily", display="Wily", capacity=2)])
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="Legacy"),
                    Task(
                        id="T02",
                        title="Parallel",
                        parallel_lane="frontend",
                        priority=1,
                        capacity_hint=2,
                    ),
                ],
            )

            _, tasks = load_tasks(paths)
            actors = load_actors(paths)

            self.assertIsNone(tasks[0].parallel_lane)
            self.assertIsNone(tasks[0].priority)
            self.assertIsNone(tasks[0].capacity_hint)
            self.assertEqual(tasks[1].parallel_lane, "frontend")
            self.assertEqual(tasks[1].priority, 1)
            self.assertEqual(tasks[1].capacity_hint, 2)
            self.assertEqual(actors[0].capacity, 2)
            self.assertNotIn("parallel_lane", tasks[0].to_dict())
            self.assertNotIn("capacity", Actor(id="solo", display="Solo").to_dict())

    def test_acceptance_items_round_trip_with_legacy_string_compatibility(self) -> None:
        legacy = Task.from_dict({"id": "T01", "title": "Legacy", "acceptance": "single"})
        structured = Task.from_dict(
            {
                "id": "T02",
                "title": "Structured",
                "acceptance": [
                    "first",
                    {"text": "second", "status": "pass", "evidence": "unit test"},
                ],
            }
        )

        self.assertEqual(legacy.acceptance_items, [AcceptanceItem(text="single")])
        self.assertEqual([item.text for item in structured.acceptance_items], ["first", "second"])
        self.assertEqual(structured.acceptance_items[1].status, "pass")
        self.assertEqual(legacy.to_dict()["acceptance"], "single")
        self.assertIsInstance(structured.to_dict()["acceptance"], list)

    def test_scheduling_orders_parallel_candidates_and_separates_waiting(self) -> None:
        tasks = [
            Task(id="T01", title="Done", status=TaskStatus.DONE),
            Task(id="T02", title="Waiting", status=TaskStatus.READY, depends_on=["T99"], priority=1),
            Task(id="T03", title="Backend high", status=TaskStatus.READY, parallel_lane="backend", priority=1, capacity_hint=2),
            Task(id="T04", title="Frontend", status=TaskStatus.READY, parallel_lane="frontend", priority=2, capacity_hint=1),
            Task(id="T05", title="Backend low capacity", status=TaskStatus.READY, parallel_lane="backend", priority=1, capacity_hint=1),
        ]

        self.assertEqual([task.id for task in parallel_candidates(tasks)], ["T05", "T03", "T04"])
        self.assertEqual([task.id for task in waiting_candidates(tasks)], ["T02"])

    def test_transitions_and_dependency_errors(self) -> None:
        task = Task(id="T01", title="x")
        claimed = apply_claim(task, actor="wily", sha="abc", at="now")
        self.assertEqual(claimed.status, TaskStatus.IN_PROGRESS)
        done = apply_done(claimed, at="later")
        self.assertEqual(done.status, TaskStatus.DONE)
        with self.assertRaises(TransitionError):
            apply_claim(done, actor="wily", sha="abc", at="now")
        with self.assertRaises(TransitionError):
            apply_block(Task(id="T02", title="blocked", status=TaskStatus.BLOCKED), reason="still blocked")
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
        self.assertIn("── 진행 중 ──", output)
        self.assertIn("── 병렬 가능 ──", output)
        self.assertIn("── 완료 ──", output)
        self.assertIn("◐", output)
        self.assertIn("▶", output)
        self.assertIn("●", output)

    def test_remote_observation_fetches_and_renders_right_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "local"
            remote = Path(tmp) / "remote.git"
            other = Path(tmp) / "right"
            root.mkdir()
            _git_repo(root)
            branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=root, check=True)
            subprocess.run(["git", "push", "-q", "-u", "origin", branch], cwd=root, check=True)
            subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
            subprocess.run(["git", "config", "user.email", "right@example.com"], cwd=other, check=True)
            subprocess.run(["git", "config", "user.name", "right"], cwd=other, check=True)
            (other / "src").mkdir()
            (other / "src" / "right.py").write_text("print('right')\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/right.py"], cwd=other, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "right work"], cwd=other, check=True)
            subprocess.run(["git", "push", "-q"], cwd=other, check=True)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(
                paths,
                [
                    Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"]),
                    Actor(id="right", display="Right", git_author_emails=["right@example.com"]),
                ],
            )
            save_tasks(paths, "demo", [Task(id="T01", title="Right task", scope=["src/*"], assignee="right")])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "status", "--ui", "ascii"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("right work", result.stdout)
            self.assertIn("추정 태스크: T01", result.stdout)

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
            cp_summaries={"T01": CpSummary(total=3, done=1, in_progress=1, current_cp="verify", cp_names=["plan", "design", "verify"])},
            mode="solo",
            ui="ascii",
        )
        self.assertIn("Wily Roadmap v3", output)
        self.assertIn("모드 단독", output)
        self.assertIn("\\- ~ T01", output)
        self.assertIn("체크포인트 [#--] 1/3 현재:verify", output)
        self.assertIn("차단 사유: waiting for review", output)

    def test_watch_renderer_groups_tasks_by_status(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(id="T01", title="Done Task", status=TaskStatus.DONE, assignee="wily"),
                Task(id="T02", title="Ready Task", status=TaskStatus.READY, assignee="right"),
                Task(id="T03", title="Blocked Task", status=TaskStatus.BLOCKED, assignee="wily", blocker="api down"),
            ],
            actors=[],
            observed_commits=[],
            cp_summaries={},
            mode="solo",
            ui="ascii",
        )
        self.assertIn("-- 차단 --", output)
        self.assertIn("-- 병렬 가능 --", output)
        self.assertIn("-- 완료 --", output)
        blocked_pos = output.index("-- 차단 --")
        ready_pos = output.index("-- 병렬 가능 --")
        done_pos = output.index("-- 완료 --")
        self.assertLess(blocked_pos, ready_pos)
        self.assertLess(ready_pos, done_pos)

    def test_watch_renderer_shows_dependency_text(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, assignee="wily"),
                Task(id="T02", title="Second", status=TaskStatus.READY, assignee="wily", depends_on=["T01"]),
            ],
            actors=[],
            observed_commits=[],
            cp_summaries={},
            mode="solo",
            ui="ascii",
        )
        self.assertIn("대기 중: T01 (진행 중)", output)

    def test_watch_renderer_shows_parallel_lanes_capacity_and_scope_conflicts(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(id="T01", title="Active", status=TaskStatus.IN_PROGRESS, actor="wily", scope=["src/ui.py"]),
                Task(
                    id="T02",
                    title="Ready lane",
                    status=TaskStatus.READY,
                    assignee="wily",
                    scope=["src/api.py"],
                    parallel_lane="backend",
                    priority=1,
                ),
                Task(
                    id="T03",
                    title="Conflicting lane",
                    status=TaskStatus.READY,
                    assignee="wily",
                    scope=["src/ui.py"],
                    parallel_lane="frontend",
                    priority=2,
                    capacity_hint=2,
                ),
                Task(
                    id="T04",
                    title="Waiting lane",
                    status=TaskStatus.READY,
                    assignee="right",
                    depends_on=["T01"],
                    parallel_lane="docs",
                ),
            ],
            actors=[Actor(id="wily", display="Wily", capacity=2), Actor(id="right", display="Right")],
            observed_commits=[],
            cp_summaries={},
            mode="collab",
            ui="ascii",
        )

        self.assertIn("-- 병렬 가능 --", output)
        self.assertIn("-- 의존 대기 --", output)
        self.assertIn("병렬: 레인 backend · 우선순위 1", output)
        self.assertIn("작업자 여력: wily 1/2", output)
        self.assertIn("충돌 가능: T01 (scope 겹침)", output)
        self.assertIn("대기 중: T01 (진행 중)", output)

    def test_watch_renderer_treats_missing_dependencies_as_waiting(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(
                    id="T01",
                    title="Missing dependency",
                    status=TaskStatus.READY,
                    assignee="wily",
                    depends_on=["T99"],
                    parallel_lane="backend",
                ),
            ],
            actors=[Actor(id="wily", display="Wily")],
            observed_commits=[],
            cp_summaries={},
            mode="solo",
            ui="ascii",
        )

        self.assertIn("-- 의존 대기 --", output)
        self.assertNotIn("-- 병렬 가능 --", output)
        self.assertIn("대기 중: T99 (누락)", output)

    def test_watch_renderer_does_not_treat_capacity_hint_as_actor_capacity(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(id="T01", title="Active", status=TaskStatus.IN_PROGRESS, actor="wily"),
                Task(
                    id="T02",
                    title="High hint",
                    status=TaskStatus.READY,
                    assignee="wily",
                    parallel_lane="backend",
                    capacity_hint=3,
                ),
            ],
            actors=[Actor(id="wily", display="Wily", capacity=1)],
            observed_commits=[],
            cp_summaries={},
            mode="solo",
            ui="ascii",
        )

        self.assertIn("병렬: 레인 backend · 필요 여력 3", output)
        self.assertIn("작업자 여력: wily 1/1 (여력 없음)", output)
        self.assertNotIn("작업자 여력: wily 1/3", output)

    def test_watch_activity_panel_shows_actor_capacity(self) -> None:
        lines = build_activity_lines(
            actors=[Actor(id="wily", display="Wily", capacity=2)],
            tasks=[
                Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily"),
                Task(id="T02", title="Second", status=TaskStatus.READY, assignee="wily", capacity_hint=3),
            ],
            cp_summaries={},
            ascii_mode=True,
            width=30,
        )
        text = "\n".join(t for t, _s in lines)
        self.assertIn("여력: 1/2", text)
        self.assertIn("추천 여력: 3", text)

    def test_watch_layout_config_responsive_breakpoints(self) -> None:
        compact = WatchLayoutConfig(width=72, ascii_mode=True, compact=True)
        self.assertEqual(compact.layout_mode, "compact")
        self.assertEqual(compact.task_pane_width, 70)
        self.assertFalse(compact.show_activity_panel)

        standard = WatchLayoutConfig(width=100)
        self.assertEqual(standard.layout_mode, "standard")
        self.assertFalse(standard.show_activity_panel)

        wide = WatchLayoutConfig(width=130)
        self.assertEqual(wide.layout_mode, "wide")
        self.assertTrue(wide.show_activity_panel)
        self.assertEqual(wide.task_pane_width, 65)

    def test_watch_activity_panel_renders_actor_state(self) -> None:
        lines = build_activity_lines(
            actors=[Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])],
            tasks=[
                Task(id="T01", title="First", status=TaskStatus.DONE, actor="wily", done_at="2026-05-18T10:00:00Z"),
                Task(id="T02", title="Second", status=TaskStatus.IN_PROGRESS, actor="wily", assignee="wily"),
            ],
            cp_summaries={"T02": CpSummary(total=1, done=0, in_progress=1, current_cp="verify", cp_names=["verify"])},
            ascii_mode=True,
            width=30,
        )
        text = "\n".join(t for t, _s in lines)
        self.assertIn("활동", text)
        self.assertIn("wily", text)
        self.assertIn("현재: T02 verify", text)
        self.assertIn("최근 완료: T01", text)

    def test_watch_status_args_strip_new_flags(self) -> None:
        stripped = watch_cmd.status_args_from_watch_args(
            ["--here", "--interval", "1", "--ui", "ascii", "--dry-run-pane", "--no-interactive", "--compact", "--show-timeline", "--hide-log"]
        )
        self.assertEqual(stripped, ["--ui", "ascii"])

    def test_tmux_watch_command_passes_new_flags(self) -> None:
        root = Path("/tmp/demo repo")
        command = watch_cmd.tmux_watch_command(
            root,
            ["--interval", "1.5", "--ui", "ascii", "--compact", "--show-timeline", "--hide-log"],
            script=Path("/tmp/wily.py"),
            python="python3",
            current_pane="%7",
        )
        self.assertEqual(command[:4], ["tmux", "split-window", "-t", "%7"])
        self.assertEqual(command[4], "-h")
        inner = command[5]
        self.assertIn("--compact", inner)
        self.assertIn("--show-timeline", inner)
        self.assertIn("--hide-log", inner)

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

    def test_watch_rejects_invalid_ui_before_launching_pane(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertIsNone(watch_cmd.watch_ui(["--ui", "wide"]))
            self.assertIsNone(watch_cmd.watch_ui(["--ui"]))
        self.assertEqual(stderr.getvalue().count("--ui requires"), 2)


class CliLifecycleTest(unittest.TestCase):
    def test_agent_cli_dispatch_lists_lifecycle_subcommands(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "agent", "--help"], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        for token in ("login", "install", "configure", "register", "unregister", "start", "stop", "status", "check", "run"):
            self.assertIn(token, result.stdout)

    def test_agent_check_is_best_effort_without_configured_daemon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First")])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "agent", "check", "--json"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["installed"], True)
            self.assertEqual(payload["configured"], False)
            self.assertIn("daemon", payload)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.READY)

    def test_init_commit_upserts_concise_agent_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                "\n".join(
                    [
                        "# Project Agent Guide",
                        "",
                        "Keep this project-specific rule.",
                        "",
                        "## Wily Roadmap",
                        "",
                        "old Wily text",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            commands = [
                ["init", "--new"],
                ["init", "answer", "Demo Project"],
                ["init", "answer", "Wily"],
                ["init", "answer", "tasks done"],
                ["init", "answer", "no board"],
                ["init", "answer", "wily Wily, emails=wily@example.com"],
                ["init", "add-task", "First task"],
                ["init", "commit"],
            ]
            for args in commands:
                result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

            agents_text = agents.read_text(encoding="utf-8")
            claude_text = (root / "CLAUDE.md").read_text(encoding="utf-8")
            for text in (agents_text, claude_text):
                self.assertIn("## Wily Roadmap", text)
                self.assertIn("Treat `.wily/` as the local project/task ledger.", text)
                self.assertIn("wily cp <id> import-status agent-handoffs/<slug>-status.md", text)
                self.assertIn("## Agent Behavior", text)
                self.assertIn("Keep edits surgical; do not refactor unrelated code.", text)
            self.assertIn("Keep this project-specific rule.", agents_text)
            self.assertIn("old Wily text", agents_text)

    def test_init_instruction_upsert_preserves_user_sections_and_uses_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text(
                "\n".join(
                    [
                        "# Guide",
                        "",
                        "## Wily Roadmap",
                        "",
                        "User-owned section must remain.",
                        "",
                        "<!-- wily-roadmap:start -->",
                        "old managed text",
                        "<!-- wily-roadmap:end -->",
                    ]
                ),
                encoding="utf-8",
            )

            init_cmd._upsert_agent_instruction_sections(path)

            text = path.read_text(encoding="utf-8")
            self.assertIn("User-owned section must remain.", text)
            self.assertIn("<!-- wily-roadmap:start -->", text)
            self.assertIn("<!-- wily-roadmap:end -->", text)
            self.assertNotIn("old managed text", text)

    def test_init_instruction_upsert_migrates_legacy_wily_sections_to_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text(
                "\n".join(
                    [
                        "# Guide",
                        "",
                        "Intro.",
                        "",
                        "## Wily Roadmap",
                        "",
                        "- Treat `.wily/` as the local project/task ledger.",
                        "",
                        "## Agent Behavior",
                        "",
                        "- Keep edits surgical; do not refactor unrelated code.",
                    ]
                ),
                encoding="utf-8",
            )

            init_cmd._upsert_agent_instruction_sections(path)

            text = path.read_text(encoding="utf-8")
            self.assertIn("Intro.", text)
            self.assertIn("<!-- wily-roadmap:start -->", text)
            self.assertIn("<!-- wily-roadmap:end -->", text)
            self.assertEqual(text.count("## Wily Roadmap"), 1)

    def test_init_commit_best_effort_registers_repo_when_agent_config_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            registry = root / "agent-registry.json"
            env = os.environ.copy()
            env["WILY_AGENT_REGISTRY"] = str(registry)
            env["WILY_BOARD_REPO"] = "R-W-LAB/demo"
            commands = [
                ["init", "--new"],
                ["init", "answer", "Demo Project"],
                ["init", "answer", "Wily"],
                ["init", "answer", "tasks done"],
                ["init", "answer", "no board"],
                ["init", "answer", "wily Wily, emails=wily@example.com"],
                ["init", "add-task", "First task"],
                ["init", "commit"],
            ]

            for args in commands:
                result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

            repos = load_registry(registry)
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0].path, root.resolve())
            self.assertEqual(repos[0].repo, "R-W-LAB/demo")

    def test_init_commit_warns_but_succeeds_when_agent_register_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            bad_parent = root / "not-a-dir"
            bad_parent.write_text("file\n", encoding="utf-8")
            env = os.environ.copy()
            env["WILY_AGENT_REGISTRY"] = str(bad_parent / "registry.json")
            env["WILY_BOARD_REPO"] = "R-W-LAB/demo"
            commands = [
                ["init", "--new"],
                ["init", "answer", "Demo Project"],
                ["init", "answer", "Wily"],
                ["init", "answer", "tasks done"],
                ["init", "answer", "no board"],
                ["init", "answer", "wily Wily, emails=wily@example.com"],
                ["init", "add-task", "First task"],
            ]
            for args in commands:
                result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

            result = subprocess.run([sys.executable, str(SCRIPT), "init", "commit"], cwd=root, env=env, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wily-agent register skipped", result.stderr)
            self.assertTrue((root / ".wily" / "tasks.yaml").exists())

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

    def test_init_new_from_git_subdirectory_uses_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subdir = root / "src" / "pkg"
            subdir.mkdir(parents=True)

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "init", "--new"],
                cwd=subdir,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / ".wily").is_dir())
            self.assertFalse((subdir / ".wily").exists())

    def test_init_quick_commits_minimal_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "init",
                    "--quick",
                    "--purpose",
                    "Quick Demo",
                    "--users",
                    "Wily",
                    "--success",
                    "tasks done",
                    "--actor",
                    "wily:wily@example.com",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            title, tasks = load_tasks(WilyPaths(root))
            self.assertEqual(title, "Quick Demo")
            self.assertEqual(tasks, [])
            self.assertEqual(load_actors(WilyPaths(root))[0].git_author_emails, ["wily@example.com"])
            self.assertFalse((root / ".wily" / "init" / "draft.yaml").exists())

    def test_init_resume_prints_progress_and_cancel_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run([sys.executable, str(SCRIPT), "init", "--new"], cwd=root, capture_output=True, text=True, check=True)
            subprocess.run([sys.executable, str(SCRIPT), "init", "answer", "Demo"], cwd=root, capture_output=True, text=True, check=True)

            result = subprocess.run([sys.executable, str(SCRIPT), "init"], cwd=root, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("진행률 1/5", result.stdout)
            self.assertIn("wily init cancel", result.stdout)

    def test_init_help_mentions_cancel(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "init", "--help"], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        self.assertIn("cancel", result.stdout)

    def test_init_adopt_migrates_legacy_roadmap_into_v3_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            wily_dir = root / ".wily"
            wily_dir.mkdir()
            (wily_dir / "status.md").write_text("# Legacy Project\n\nExisting notes.\n", encoding="utf-8")
            (wily_dir / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "goal: Legacy goal",
                        "roadmap_schema: wily-roadmap-v2",
                        "stages:",
                        "  - id: s01",
                        "    title: Finished stage",
                        "    status: done",
                        "    depends_on: []",
                        "    path: stages/s01-finished",
                        "  - id: s02",
                        "    title: Ready stage",
                        "    status: ready",
                        "    depends_on: [s01]",
                        "    path: stages/s02-ready",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "init", "--adopt"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(any((wily_dir / "archive").glob("legacy-*/roadmap.yaml")))
            title, tasks = load_tasks(WilyPaths(root))
            self.assertEqual(title, "Legacy goal")
            self.assertEqual([(task.id, task.title, task.status) for task in tasks], [
                ("T01", "Finished stage", TaskStatus.DONE),
                ("T02", "Ready stage", TaskStatus.READY),
            ])
            self.assertEqual(tasks[1].depends_on, ["T01"])
            self.assertTrue((wily_dir / "actors.yaml").exists())
            self.assertIn("Legacy Project", (wily_dir / "project.md").read_text(encoding="utf-8"))

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

    def test_next_mine_fails_when_git_author_matches_no_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run(["git", "config", "user.email", "unknown@example.com"], cwd=root, check=True)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", assignee="wily")])

            with chdir_compat(root):
                stderr = StringIO()
                with redirect_stderr(stderr):
                    code = next_cmd.main(["--mine"])

            self.assertEqual(code, 1)
            self.assertIn("no actor matches current git author", stderr.getvalue())

    def test_claim_as_overrides_git_author_actor_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run(["git", "config", "user.email", "unknown@example.com"], cwd=root, check=True)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(paths, "demo", [Task(id="T01", title="First", intent="do it", acceptance="done")])

            result = subprocess.run([sys.executable, str(SCRIPT), "claim", "T01", "--as", "wily"], cwd=root, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].actor, "wily")

    def test_claim_actor_mismatch_message_includes_yaml_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run(["git", "config", "user.email", "unknown@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Unknown Dev"], cwd=root, check=True)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", intent="do it", acceptance="done")])

            result = subprocess.run([sys.executable, str(SCRIPT), "claim", "T01"], cwd=root, capture_output=True, text=True)

            self.assertEqual(result.returncode, 1)
            self.assertIn("actors.yaml", result.stderr)
            self.assertIn("git_author_emails:", result.stderr)
            self.assertIn("unknown@example.com", result.stderr)
            self.assertIn("wily replan actor add", result.stderr)

    def test_replan_actor_add_updates_actors_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(paths, "demo", [])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "replan", "actor", "add", "right", "--email=right@example.com", "--name=Right Dev"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            actors = {actor.id: actor for actor in load_actors(paths)}
            self.assertEqual(actors["right"].git_author_emails, ["right@example.com"])
            self.assertEqual(actors["right"].git_author_names, ["Right Dev"])

    def test_next_all_json_exposes_parallel_candidates_and_waiting_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="Blocked dep", status=TaskStatus.IN_PROGRESS),
                    Task(id="T02", title="Waiting", status=TaskStatus.READY, depends_on=["T01"], priority=1),
                    Task(id="T03", title="Backend", status=TaskStatus.READY, parallel_lane="backend", priority=1, capacity_hint=2),
                    Task(id="T04", title="Frontend", status=TaskStatus.READY, parallel_lane="frontend", priority=2, capacity_hint=1),
                    Task(id="T05", title="Backend small", status=TaskStatus.READY, parallel_lane="backend", priority=1, capacity_hint=1),
                ],
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "next", "--all", "--json"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual([task["id"] for task in payload["parallel"]], ["T05", "T03", "T04"])
            self.assertEqual([task["id"] for task in payload["waiting"]], ["T02"])

    def test_claim_rejects_empty_intent_or_acceptance_unless_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="Stub", intent="", acceptance="")])

            blocked = subprocess.run([sys.executable, str(SCRIPT), "claim", "T01"], cwd=root, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 3)
            self.assertIn("intent", blocked.stderr)
            self.assertIn("acceptance", blocked.stderr)

            allowed = subprocess.run([sys.executable, str(SCRIPT), "claim", "T01", "--allow-empty"], cwd=root, capture_output=True, text=True)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_go_warns_when_acceptance_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Stub", intent="do it", acceptance="", status=TaskStatus.IN_PROGRESS)])

            result = subprocess.run([sys.executable, str(SCRIPT), "go", "T01"], cwd=root, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("warning: T01 has empty acceptance", result.stderr)
            self.assertIn("(no acceptance)", result.stdout)

    def test_replan_draft_does_not_overwrite_init_interview_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            with chdir_compat(root):
                self.assertEqual(init_cmd.main(["--new"]), 0)
                self.assertEqual(init_cmd.main(["answer", "Demo Project"]), 0)
                self.assertEqual(replan_cmd.main(["add", "Later task"]), 0)
                self.assertEqual(replan_cmd.main(["commit"]), 0)
            draft_text = paths.init_draft.read_text(encoding="utf-8")
            self.assertIn("Demo Project", draft_text)

    def test_replan_refuses_all_done_task_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Done", status=TaskStatus.DONE)])

            with chdir_compat(root):
                self.assertEqual(replan_cmd.main(["revise-task", "T01", "title", "Changed"]), 3)

    def test_replan_drift_guard_creates_in_progress_stub_for_unclaimed_staged_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="Planned")])
            (root / "unplanned.py").write_text("print('drift')\n", encoding="utf-8")
            subprocess.run(["git", "add", "unplanned.py"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(replan_cmd.main(["drift-guard", "--from-hook"]), 0)
                self.assertEqual(replan_cmd.main(["drift-guard", "--from-hook"]), 0)

            _, tasks = load_tasks(paths)
            stubs = [task for task in tasks if task.title.startswith("drift:")]
            self.assertEqual(len(stubs), 1)
            self.assertEqual(stubs[0].status, TaskStatus.IN_PROGRESS)
            self.assertEqual(stubs[0].scope, ["unplanned.py"])
            self.assertEqual(stubs[0].intent, "")
            self.assertEqual(stubs[0].acceptance, "")

    def test_replan_drift_guard_stubs_only_files_outside_active_claim_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "demo",
                [Task(id="T01", title="Planned", scope=["src/*"], status=TaskStatus.IN_PROGRESS, actor="wily")],
            )
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "src" / "planned.py").write_text("print('planned')\n", encoding="utf-8")
            (root / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/planned.py", "docs/outside.md"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(replan_cmd.main(["drift-guard", "--from-hook"]), 0)

            _, tasks = load_tasks(paths)
            stubs = [task for task in tasks if task.title.startswith("drift:")]
            self.assertEqual(len(stubs), 1)
            self.assertEqual(stubs[0].scope, ["docs/outside.md"])

    def test_replan_installs_opt_in_pre_commit_drift_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [])

            with chdir_compat(root):
                self.assertEqual(replan_cmd.main(["install-pre-commit-hook"]), 0)

            hook = root / ".git" / "hooks" / "pre-commit"
            self.assertTrue(hook.exists())
            self.assertTrue(hook.stat().st_mode & 0o111)
            text = hook.read_text(encoding="utf-8")
            self.assertIn("drift-guard --from-hook", text)
            self.assertIn(str(SCRIPT), text)

    def test_value_flags_require_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "start", "plan", "--actor"]), 2)
                self.assertEqual(done_cmd.main(["T01", "--note"]), 2)

    def test_done_observed_records_actor_from_observed_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(
                paths,
                [
                    Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"]),
                    Actor(id="right", display="Right", git_author_emails=["right@example.com"]),
                ],
            )
            save_tasks(
                paths,
                "demo",
                [Task(id="T01", title="Observed", scope=["right.txt"], status=TaskStatus.IN_PROGRESS, assignee="right", claim_sha=base, claim_at="2026-05-18T00:00:00Z")],
            )
            subprocess.run(["git", "config", "user.email", "right@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "right"], cwd=root, check=True)
            (root / "right.txt").write_text("right\n", encoding="utf-8")
            subprocess.run(["git", "add", "right.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "right observed"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(done_cmd.main(["T01", "--observed"]), 0)

            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].actor, "right")
            self.assertIn("actor: right (observed)", paths.result_md("T01").read_text(encoding="utf-8"))

    def test_done_blocks_scope_drift_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Scoped", scope=["src/*"], status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha=base)])
            (root / "docs").mkdir()
            (root / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/outside.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "outside"], cwd=root, check=True)

            with chdir_compat(root):
                stderr = StringIO()
                with redirect_stderr(stderr):
                    code = done_cmd.main(["T01"])

            self.assertEqual(code, 3)
            self.assertIn("scope drift detected", stderr.getvalue())
            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.IN_PROGRESS)
            self.assertFalse(paths.result_md("T01").exists())

    def test_done_can_adopt_scope_drift_into_current_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Scoped", scope=["src/*"], status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha=base)])
            (root / "docs").mkdir()
            (root / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/outside.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "outside"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(done_cmd.main(["T01", "--add-scope"]), 0)

            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.DONE)
            self.assertIn("docs/outside.md", tasks[0].scope)

    def test_done_can_create_or_reuse_drift_stub_for_scope_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(
                paths,
                "demo",
                [Task(id="T01", title="Scoped", scope=["src/*"], status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha=base)],
            )
            (root / "docs").mkdir()
            (root / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/outside.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "outside"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(done_cmd.main(["T01", "--stub-drift"]), 0)

            _, tasks = load_tasks(paths)
            stubs = [task for task in tasks if task.title.startswith("drift:")]
            self.assertEqual(len(stubs), 1)
            self.assertEqual(stubs[0].scope, ["docs/outside.md"])
            self.assertEqual(tasks[0].status, TaskStatus.DONE)

    def test_done_drift_only_considers_current_actor_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(
                paths,
                [
                    Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"]),
                    Actor(id="right", display="Right", git_author_emails=["right@example.com"]),
                ],
            )
            save_tasks(paths, "demo", [Task(id="T01", title="Scoped", scope=["src/*"], status=TaskStatus.IN_PROGRESS, actor="wily", claim_sha=base)])
            (root / "docs").mkdir()
            (root / "docs" / "right.md").write_text("right\n", encoding="utf-8")
            subprocess.run(["git", "config", "user.email", "right@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "right"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/right.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "right change"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(done_cmd.main(["T01"]), 0)

            _, tasks = load_tasks(paths)
            self.assertEqual(tasks[0].status, TaskStatus.DONE)

    def test_drift_stub_reuses_subset_scope_for_same_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            existing = Task(
                id="T02",
                title="drift: docs/a.md (+1 files)",
                scope=["docs/a.md", "docs/b.md"],
                status=TaskStatus.IN_PROGRESS,
                actor="wily",
            )
            save_tasks(paths, "demo", [existing])

            reused = ensure_drift_stub(root, paths, "demo", [existing], ["docs/a.md"])

            self.assertEqual(reused.id, "T02")
            _, tasks = load_tasks(paths)
            self.assertEqual(len([task for task in tasks if task.title.startswith("drift:")]), 1)

    def test_done_records_acceptance_checks_in_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(
                paths,
                "demo",
                [
                    Task(
                        id="T01",
                        title="Structured",
                        intent="do it",
                        acceptance=[AcceptanceItem(text="tests pass"), AcceptanceItem(text="docs updated")],
                        status=TaskStatus.IN_PROGRESS,
                        actor="wily",
                        claim_sha=base,
                    )
                ],
            )

            with chdir_compat(root):
                self.assertEqual(done_cmd.main(["T01", "--ac-check", "1=pass", "--ac-check", "2=fail:missing docs"]), 0)

            result = paths.result_md("T01").read_text(encoding="utf-8")
            self.assertIn("| 1 | pass | tests pass |", result)
            self.assertIn("| 2 | fail | docs updated | missing docs |", result)
            self.assertEqual(read_ac_checks(paths, "T01")[1].status, "fail")

    def test_land_changed_uses_porcelain_v2_paths_for_rename_and_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            old = root / "old.txt"
            old.write_text("old\n", encoding="utf-8")
            subprocess.run(["git", "add", "old.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "old"], cwd=root, check=True)
            subprocess.run(["git", "mv", "old.txt", "new.txt"], cwd=root, check=True)
            (root / "copy.txt").write_text((root / "new.txt").read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run(["git", "add", "copy.txt"], cwd=root, check=True)

            changed = land_cmd._changed(root)

            self.assertIn("new.txt", changed)
            self.assertIn("copy.txt", changed)
            self.assertNotIn("old.txt -> new.txt", changed)

    def test_land_message_marks_force_commit_before_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            message = land_cmd._message(paths, "T01", "Pre done", pre_done=True)

            self.assertIn("Wily-Task: T01", message)
            self.assertIn("Wily-Pre-Done: true", message)

    def test_go_checkpoint_commands_are_portable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = WilyPaths(root)
            (root / ".wily").mkdir()
            text = go_cmd.goal_text(root, paths, Task(id="T01", title="Portable", status=TaskStatus.IN_PROGRESS))

            self.assertIn("wily cp T01 start <cp-name>", text)
            self.assertNotIn("plugins/wily-roadmap/scripts/wily.py", text)

    def test_json_contract_for_agent_facing_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="First", intent="do it", acceptance="done"),
                    Task(id="T02", title="Second", intent="block it", acceptance="blocked"),
                ],
            )

            claim = subprocess.run([sys.executable, str(SCRIPT), "claim", "T01", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(claim.returncode, 0, claim.stderr)
            self.assertEqual(json.loads(claim.stdout)["task"]["status"], "in_progress")

            cp = subprocess.run(
                [sys.executable, str(SCRIPT), "cp", "T01", "start", "plan", "--actor", "wily", "--json"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual(json.loads(cp.stdout)["event"]["cp"], "plan")

            done = subprocess.run([sys.executable, str(SCRIPT), "done", "T01", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)["task"]["status"], "done")

            block = subprocess.run([sys.executable, str(SCRIPT), "block", "T02", "waiting", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(block.returncode, 0, block.stderr)
            self.assertEqual(json.loads(block.stdout)["task"]["blocker"], "waiting")

            watch = subprocess.run([sys.executable, str(SCRIPT), "watch", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(watch.returncode, 2)
            self.assertEqual(json.loads(watch.stdout)["tasks"][1]["status"], "blocked")

    def test_init_and_replan_json_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)

            init_result = subprocess.run([sys.executable, str(SCRIPT), "init", "--new", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            self.assertEqual(json.loads(init_result.stdout)["current_question"], "purpose")

            paths = WilyPaths(root)
            save_tasks(paths, "demo", [Task(id="T01", title="First")])
            replan_result = subprocess.run([sys.executable, str(SCRIPT), "replan", "--json"], cwd=root, capture_output=True, text=True)
            self.assertEqual(replan_result.returncode, 0, replan_result.stderr)
            self.assertEqual(json.loads(replan_result.stdout)["tasks"][0]["id"], "T01")

    def test_observation_base_without_remote_ref_falls_back_to_head(self) -> None:
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
