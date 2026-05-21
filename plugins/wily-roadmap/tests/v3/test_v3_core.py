from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wily.py"
sys.path.insert(0, str(ROOT / "scripts"))

from wily.cli import agent as agent_cmd  # noqa: E402
from wily.agent import client as agent_client  # noqa: E402
from wily.cli import _common  # noqa: E402
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
from wily.ui.watch_render import _display_width, render_watch  # noqa: E402


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "wily@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "wily"], cwd=path, check=True)
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


def _write_coordination(parent: Path, *, child_id: str = "roadmap", child_path: str = "./wily-roadmap") -> None:
    wily_dir = parent / ".wily"
    wily_dir.mkdir(exist_ok=True)
    (wily_dir / "coordination.yaml").write_text(
        "\n".join(
            [
                "schema: wily-coordination-v1",
                "title: Parent Project",
                "parent:",
                "  id: parent",
                "  path: .",
                "repos:",
                f"  - id: {child_id}",
                f"    path: {child_path}",
                "",
            ]
        ),
        encoding="utf-8",
    )


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

    def test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def fake_post_json(url: str, payload: dict[str, object], **_kwargs: object) -> dict[str, object]:
            calls.append((url, payload))
            return {"sent": False, "reason": "boom"}

        original = agent_client.post_json
        agent_client.post_json = fake_post_json
        try:
            config = AgentConfig(board_url="https://board.example", token="token", actor="wily")

            snapshot = agent_client.publish_snapshot(config, {"repo": "R-W-LAB/demo"})
            heartbeat = agent_client.publish_heartbeat(
                config,
                project_id="project-1",
                current_task_id="T01",
            )
        finally:
            agent_client.post_json = original

        self.assertEqual(snapshot, {"sent": False, "reason": "boom"})
        self.assertEqual(heartbeat, {"sent": False, "reason": "boom"})
        self.assertEqual(calls[0][0], "https://board.example/agent/snapshot")
        self.assertEqual(calls[1][0], "https://board.example/agent/heartbeat")

    def test_agent_client_posts_t26_heartbeat_payload_in_token_mode(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def fake_post_json(url: str, payload: dict[str, object], **_kwargs: object) -> dict[str, object]:
            calls.append((url, payload))
            return {"status": 202}

        original = agent_client.post_json
        agent_client.post_json = fake_post_json
        try:
            config = AgentConfig(board_url="https://board.example", token="token", actor="wily", machine_id="machine-1")
            heartbeat = {
                "project_id": "R-W-LAB/demo",
                "repo_slug": "R-W-LAB/demo",
                "actor": {"id": "wily", "display": "Wily"},
                "machine": {"hostname": "demo-host", "machine_id": "machine-1"},
                "current_task_id": "T01",
                "current_cp": "Implementation",
                "status": "active",
                "captured_at": "2026-05-20T00:00:00Z",
            }

            result = agent_client.publish_heartbeat(config, payload=heartbeat)
        finally:
            agent_client.post_json = original

        self.assertEqual(result["sent"], True)
        self.assertEqual(calls, [("https://board.example/agent/heartbeat", heartbeat)])

    def test_agent_builds_board_v3_snapshot_payload_from_local_wily_state(self) -> None:
        from wily.agent.snapshot import build_snapshot_payload, snapshot_sha

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            subprocess.run(["git", "branch", "-M", "main"], cwd=root, check=True)
            subprocess.run(["git", "remote", "add", "origin", "git@github.com:R-W-LAB/demo.git"], cwd=root, check=True)
            (root / "wily-workspace.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Demo Workspace",
                        "repos:",
                        "  - id: demo",
                        "    path: .",
                        "    title: Demo Repo",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
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
            append_event(paths, "T01", CpEvent(ts="2026-05-19T00:02:00Z", actor="wily", cp="Implementation", event="start", note="coding"))
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# Result\n\nDone locally.\n", encoding="utf-8")

            payload = build_snapshot_payload(root, repo="R-W-LAB/demo", actor="wily")

            self.assertEqual(payload["payload_version"], "board_v3_snapshot_v1")
            self.assertEqual(payload["active_mode"], "single_repo")
            self.assertNotIn("coordination", payload)
            self.assertEqual(payload["repo"], "R-W-LAB/demo")
            self.assertTrue(payload["remote_url"].endswith("R-W-LAB/demo.git"))
            self.assertEqual(payload["remote"]["raw_url"], "git@github.com:R-W-LAB/demo.git")
            self.assertEqual(payload["remote"]["normalized_url"], "https://github.com/R-W-LAB/demo")
            self.assertEqual(payload["remote"]["owner"], "R-W-LAB")
            self.assertEqual(payload["remote"]["name"], "demo")
            self.assertEqual(payload["remote"]["slug"], "R-W-LAB/demo")
            self.assertEqual(payload["repo_slug"], "R-W-LAB/demo")
            self.assertEqual(payload["branch"], "main")
            self.assertRegex(payload["checkout_id"], r"^checkout_[0-9a-f]{16}$")
            self.assertEqual(payload["worktree_id"], payload["checkout_id"])
            self.assertEqual(payload["checkout"]["checkout_id"], payload["checkout_id"])
            self.assertEqual(payload["checkout"]["worktree_id"], payload["worktree_id"])
            self.assertEqual(payload["checkout"]["branch"], "main")
            self.assertEqual(payload["checkout"]["local_path"], str(root.resolve()))
            self.assertEqual(payload["workspace"]["title"], "Demo Workspace")
            self.assertEqual(payload["workspace"]["repo"]["id"], "demo")
            self.assertEqual(payload["title"], "Demo Project")
            self.assertEqual(payload["mode_hint"], "solo")
            self.assertEqual(payload["local_path"], str(root.resolve()))
            self.assertTrue(payload["machine"]["hostname"])
            self.assertEqual(payload["machine"]["machine_id"], "")
            self.assertEqual(payload["actor"]["id"], "wily")
            self.assertEqual(payload["actor"]["display"], "Wily")
            self.assertEqual(payload["tasks"][0]["id"], "T01")
            self.assertEqual(payload["tasks"][0]["actor"], "wily")
            self.assertEqual(payload["tasks"][0]["claim_sha"], None)
            self.assertEqual(payload["tasks"][0]["parallel_lane"], "agent")
            self.assertEqual(payload["actors"]["wily"]["display"], "Wily")
            self.assertEqual(payload["actors"]["wily"]["capacity"], 2)
            self.assertEqual(payload["task_progress"]["T01"]["done"], 1)
            self.assertEqual(payload["task_progress"]["T01"]["total"], 2)
            self.assertEqual(payload["task_progress"]["T01"]["current_cp"], "Implementation")
            self.assertEqual(payload["cp_events"]["T01"][0]["cp"], "plan")
            self.assertEqual(payload["presence"]["project_id"], payload["project_id"])
            self.assertEqual(payload["presence"]["repo_slug"], "R-W-LAB/demo")
            self.assertEqual(payload["presence"]["checkout_id"], payload["checkout_id"])
            self.assertEqual(payload["presence"]["worktree_id"], payload["worktree_id"])
            self.assertEqual(payload["presence"]["branch"], "main")
            self.assertEqual(payload["presence"]["local_path"], str(root.resolve()))
            self.assertEqual(payload["presence"]["current_task_id"], "T01")
            self.assertEqual(payload["presence"]["current_cp"], "Implementation")
            self.assertEqual(payload["presence"]["status"], "active")
            timeline = payload["checkpoint_timeline"]["T01"]
            self.assertEqual([row["id"] for row in timeline], ["plan", "Implementation"])
            self.assertEqual(timeline[0]["status"], "done")
            self.assertEqual(timeline[0]["last_update"], "2026-05-19T00:01:00Z")
            self.assertEqual(timeline[1]["status"], "running")
            self.assertEqual(timeline[1]["current_action"], "coding")
            self.assertEqual(timeline[1]["verification"], "")
            self.assertEqual(timeline[1]["status_board"], {})
            self.assertEqual(timeline[1]["result_summary"], "Done locally.")
            self.assertEqual(payload["recovery"]["imported_count"], 0)
            self.assertEqual(payload["recovery"]["skipped_duplicate_count"], 0)
            self.assertEqual(payload["recovery"]["warnings"], [])
            self.assertIn("last_successful_push", payload["sync_health"])
            self.assertIn("pending_snapshot_sha", payload["sync_health"])
            self.assertIn("Done locally.", payload["task_results"]["T01"])
            self.assertIn("Local project notes.", payload["project_md"])
            self.assertEqual(payload["snapshot_sha"], snapshot_sha(payload))
            self.assertTrue(payload["observed_commits"])

    def test_agent_snapshot_includes_parent_coordination_contract_for_board(self) -> None:
        from wily.agent.snapshot import build_snapshot_payload, snapshot_sha
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            scratch = parent / "scratch"
            for repo_root, remote in (
                (roadmap, "git@github.com:R-W-LAB/wily-roadmap.git"),
                (board, "git@github.com:R-W-LAB/wily-board.git"),
                (scratch, "git@github.com:R-W-LAB/scratch.git"),
            ):
                repo_root.mkdir()
                _git_repo(repo_root)
                subprocess.run(["git", "branch", "-M", "main"], cwd=repo_root, check=True)
                subprocess.run(["git", "remote", "add", "origin", remote], cwd=repo_root, check=True)
            (parent / ".wily").mkdir()
            (parent / ".wily" / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Wily Plugin Parent",
                        "parent:",
                        "  id: parent",
                        "  title: Coordination Parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    title: Wily Roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: board",
                        "    title: Wily Board",
                        "    path: ./wily-board",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            src = roadmap / "src"
            src.mkdir()
            for index in range(6):
                (src / f"{index:02d}.py").write_text(f"print({index})\n", encoding="utf-8")
            (board / "server.py").write_text("print('board')\n", encoding="utf-8")
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", roadmap), ("board", board)])
            paths = WilyPaths(parent)
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(
                paths,
                "Parent Roadmap",
                [
                    Task(
                        id="T01",
                        title="Ship parent coordination",
                        status=TaskStatus.IN_PROGRESS,
                        actor="wily",
                        depends_on=["T00"],
                        scope=["roadmap:src/**", {"repo": "parent", "path": "agent-handoffs/**"}],
                        claim_snapshot=snapshot,
                    )
                ],
            )

            payload = build_snapshot_payload(parent, repo="R-W-LAB/wily-plugin", actor="wily")

            self.assertEqual(payload["payload_version"], "board_v3_snapshot_v1")
            self.assertEqual(payload["active_mode"], "coordination")
            coordination = payload["coordination"]
            self.assertEqual(coordination["schema"], "wily-coordination-snapshot-v1")
            self.assertEqual(coordination["title"], "Wily Plugin Parent")
            self.assertEqual(coordination["manifest_path"], str((parent / ".wily" / "coordination.yaml").resolve()))
            self.assertEqual(coordination["display"], {"default_owner": "parent", "child_default_visibility": "nested"})
            self.assertEqual(
                coordination["parent"],
                {
                    "id": "parent",
                    "title": "Coordination Parent",
                    "path": str(parent.resolve()),
                    "project_id": payload["project_id"],
                    "repo_slug": "R-W-LAB/wily-plugin",
                    "display_role": "owner",
                },
            )
            children = {child["id"]: child for child in coordination["children"]}
            self.assertEqual(set(children), {"roadmap", "board"})
            self.assertNotIn("scratch", children)
            self.assertEqual(children["roadmap"]["title"], "Wily Roadmap")
            self.assertEqual(children["roadmap"]["path"], str(roadmap.resolve()))
            self.assertEqual(children["roadmap"]["repo_slug"], "R-W-LAB/wily-roadmap")
            self.assertEqual(children["roadmap"]["remote"]["slug"], "R-W-LAB/wily-roadmap")
            self.assertEqual(children["roadmap"]["branch"], "main")
            self.assertEqual(
                children["roadmap"]["display"],
                {"default_visibility": "nested", "owned_by_parent": True, "direct_route": "scoped_parent_view"},
            )
            roadmap_entries = {entry["id"]: entry for entry in coordination["task_roadmap"]}
            task = roadmap_entries["T01"]
            self.assertEqual(task["title"], "Ship parent coordination")
            self.assertEqual(task["status"], "in_progress")
            self.assertEqual(task["depends_on"], ["T00"])
            self.assertEqual(task["actor"], "wily")
            self.assertEqual(
                task["scope"],
                [
                    {"repo": "roadmap", "path": "src/**", "source": "roadmap:src/**"},
                    {"repo": "parent", "path": "agent-handoffs/**", "source": {"repo": "parent", "path": "agent-handoffs/**"}},
                ],
            )
            self.assertEqual([repo["id"] for repo in task["target_repos"]], ["roadmap", "parent"])
            self.assertEqual(task["target_repos"][0]["repo_slug"], "R-W-LAB/wily-roadmap")
            self.assertEqual(task["claim_snapshot_summary"]["parent"]["git_available"], False)
            roadmap_summary = task["claim_snapshot_summary"]["roadmap"]
            self.assertEqual(roadmap_summary["git_available"], True)
            self.assertEqual(roadmap_summary["branch"], "main")
            self.assertTrue(roadmap_summary["sha"])
            self.assertEqual(roadmap_summary["dirty"], True)
            self.assertEqual(roadmap_summary["changed_file_count"], 6)
            self.assertEqual(roadmap_summary["changed_files_sample"], [f"src/{index:02d}.py" for index in range(5)])
            self.assertNotIn("fingerprints", roadmap_summary)
            self.assertEqual(payload["snapshot_sha"], snapshot_sha(payload))

    def test_agent_snapshot_keeps_manifest_workspace_compatible_without_coordination_display_hints(self) -> None:
        from wily.agent.snapshot import build_snapshot_payload

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "child"
            child.mkdir()
            _git_repo(root)
            subprocess.run(["git", "branch", "-M", "main"], cwd=root, check=True)
            (root / "wily-workspace.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Manifest Only",
                        "repos:",
                        "  - id: root",
                        "    path: .",
                        "    title: Root Repo",
                        "  - id: child",
                        "    path: ./child",
                        "    title: Child Repo",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "Manifest Root", [Task(id="T01", title="Workspace task")])

            payload = build_snapshot_payload(root, repo="R-W-LAB/root", actor="wily")

            self.assertEqual(payload["active_mode"], "single_repo")
            self.assertEqual(payload["workspace"]["title"], "Manifest Only")
            self.assertEqual(payload["workspace"]["repo"]["id"], "root")
            self.assertNotIn("coordination", payload)
            self.assertNotIn("display", payload["workspace"])

    def test_agent_recovery_imports_missing_status_events_without_downgrading_ledger(self) -> None:
        from wily.agent.recovery import recover_status_boards

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            init_progress(paths, "T01")
            append_event(paths, "T01", CpEvent(ts="2026-05-18T00:00:00Z", actor="wily", cp="Plan", event="start"))
            append_event(paths, "T01", CpEvent(ts="2026-05-18T00:01:00Z", actor="wily", cp="Plan", event="done"))
            status = root / "agent-handoffs" / "t01-demo-status.md"
            status.parent.mkdir()
            status.write_text(
                "\n".join(
                    [
                        "| Checkpoint | Status | Evidence |",
                        "| --- | --- | --- |",
                        "| Plan | BLOCKED | stale board state must not cancel done ledger cp |",
                        "| Implementation | DONE | recovered from status board |",
                    ]
                ),
                encoding="utf-8",
            )

            report = recover_status_boards(root, actor="wily", ts="2026-05-20T00:00:00Z")

            events = [(event.cp, event.event, event.note) for event in read_events(paths, "T01")]
            self.assertEqual(events[:2], [("Plan", "start", None), ("Plan", "done", None)])
            self.assertNotIn(("Plan", "cancel", "stale board state must not cancel done ledger cp"), events)
            self.assertIn(("Implementation", "start", None), events)
            self.assertIn(("Implementation", "done", "recovered from status board"), events)
            self.assertEqual(report["imported_count"], 2)
            self.assertGreaterEqual(report["skipped_duplicate_count"], 1)
            self.assertEqual(report["warnings"], [])
            self.assertEqual(report["tasks"]["T01"]["status_boards"][0]["source_path"], str(status.resolve()))

    def test_agent_recovery_warns_and_imports_nothing_for_ambiguous_status_boards(self) -> None:
        from wily.agent.recovery import recover_status_boards

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            first = root / "agent-handoffs" / "t01-alpha-status.md"
            second = root / "agent-handoffs" / "t01-beta-status.md"
            first.parent.mkdir()
            for status in (first, second):
                status.write_text("| Checkpoint | Status | Evidence |\n| --- | --- | --- |\n| Plan | DONE | ok |\n", encoding="utf-8")

            report = recover_status_boards(root, actor="wily", ts="2026-05-20T00:00:00Z")

            self.assertEqual(read_events(paths, "T01"), [])
            self.assertEqual(report["imported_count"], 0)
            self.assertTrue(any("ambiguous" in warning.lower() for warning in report["warnings"]))

    def test_agent_sync_health_records_failure_success_and_pending_snapshot(self) -> None:
        from wily.agent.sync_health import load_sync_health, record_publish_result

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sync-health.json"

            failed = record_publish_result(
                target,
                kind="snapshot",
                snapshot_sha="sha-old",
                result={"sent": False, "reason": "board down"},
                client_version="wily-agent/0.1.0",
                captured_at="2026-05-20T00:00:00Z",
            )

            self.assertEqual(failed["last_failed_push"], "2026-05-20T00:00:00Z")
            self.assertEqual(failed["last_failure_reason"], "snapshot: board down")
            self.assertEqual(failed["pending_snapshot_sha"], "sha-old")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), failed)

            recovered = record_publish_result(
                target,
                kind="snapshot",
                snapshot_sha="sha-new",
                result={"sent": True, "status": 202},
                client_version="wily-agent/0.1.0",
                captured_at="2026-05-20T00:01:00Z",
            )

            self.assertEqual(recovered["last_successful_push"], "2026-05-20T00:01:00Z")
            self.assertEqual(recovered["last_failure_reason"], "")
            self.assertEqual(recovered["pending_snapshot_sha"], "")
            self.assertEqual(load_sync_health(target), recovered)

    def test_agent_daemon_records_failure_then_reconnect_sends_latest_snapshot(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo
        from wily.agent.sync_health import load_sync_health

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Old title", status=TaskStatus.IN_PROGRESS, actor="wily")])
            repo = RegisteredRepo(path=root, repo="R-W-LAB/demo")
            config = AgentConfig(board_url="https://board.example", token="token", actor="wily", machine_id="machine-1")
            sync_health_path = root / "sync-health.json"
            snapshots: list[dict[str, object]] = []
            results = iter([{"sent": False, "reason": "board down"}, {"sent": True, "status": 202}])

            def fake_publish_snapshot(_config: AgentConfig, payload: dict[str, object]) -> dict[str, object]:
                snapshots.append(payload)
                return next(results)

            with patch.object(daemon, "publish_snapshot", side_effect=fake_publish_snapshot), patch.object(
                daemon,
                "publish_heartbeat",
                return_value={"sent": True, "status": 202},
            ):
                first = daemon.publish_repo_heartbeat(config, repo, include_snapshot=True, sync_health_path=sync_health_path)
                save_tasks(paths, "demo", [Task(id="T01", title="New title", status=TaskStatus.IN_PROGRESS, actor="wily")])
                second = daemon.publish_repo_heartbeat(config, repo, include_snapshot=True, sync_health_path=sync_health_path)

            self.assertEqual(first["snapshot"]["sent"], False)
            self.assertEqual(second["snapshot"]["sent"], True)
            self.assertEqual(snapshots[-1]["tasks"][0]["title"], "New title")
            health = load_sync_health(sync_health_path)
            self.assertEqual(health["last_failure_reason"], "")
            self.assertEqual(health["pending_snapshot_sha"], "")
            self.assertEqual(second["sync_health"]["last_successful_push"], health["last_successful_push"])

    def test_agent_recovery_imported_by_daemon_uses_non_empty_timestamp(self) -> None:
        from wily.agent.recovery import recover_status_boards

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "t01-demo-status.md"
            status.parent.mkdir()
            status.write_text("| Checkpoint | Status | Evidence |\n| --- | --- | --- |\n| Plan | DONE | recovered |\n", encoding="utf-8")

            report = recover_status_boards(root, actor="wily")

            events = read_events(paths, "T01")
            self.assertTrue(events)
            self.assertTrue(all(event.ts for event in events))
            self.assertEqual(report["imported_count"], 2)
            self.assertEqual(report["would_import_count"], 0)

    def test_agent_daemon_status_recovery_does_not_dirty_progress_ledger(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "t01-demo-status.md"
            status.parent.mkdir()
            status.write_text("| Checkpoint | Status | Evidence |\n| --- | --- | --- |\n| Plan | DONE | recovered |\n", encoding="utf-8")

            with patch.object(daemon, "publish_snapshot", return_value={"sent": True, "status": 202}), patch.object(
                daemon,
                "publish_heartbeat",
                return_value={"sent": True, "status": 202},
            ):
                result = daemon.publish_repo_heartbeat(
                    AgentConfig(board_url="https://board.example", token="token", actor="wily"),
                    RegisteredRepo(path=root, repo="R-W-LAB/demo"),
                    sync_health_path=root / "sync-health.json",
                )

            self.assertEqual(result["snapshot"]["sent"], True)
            self.assertEqual(read_events(paths, "T01"), [])
            self.assertEqual(result["sync_health"]["last_failure_reason"], "")
            self.assertEqual(result["recovery"]["imported_count"], 0)
            self.assertEqual(result["recovery"]["would_import_count"], 2)

    def test_agent_recovery_ignores_non_checkpoint_status_tables(self) -> None:
        from wily.agent.recovery import recover_status_boards

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            status = root / "agent-handoffs" / "t01-demo-status.md"
            status.parent.mkdir()
            status.write_text(
                "\n".join(
                    [
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP01 | DONE | Real checkpoint | root | ok |",
                        "",
                        "| Item | Status | Notes |",
                        "| --- | --- | --- |",
                        "| Superpowers routing | DONE | not a checkpoint |",
                    ]
                ),
                encoding="utf-8",
            )

            recover_status_boards(root, actor="wily", ts="2026-05-20T00:00:00Z")

            self.assertEqual(
                [(event.cp, event.event) for event in read_events(paths, "T01")],
                [("Real checkpoint", "start"), ("Real checkpoint", "done")],
            )

    def test_agent_run_once_keeps_sync_health_isolated_per_registered_repo(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo, save_registry

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a = base / "repo-a"
            repo_b = base / "repo-b"
            for repo_root, title in ((repo_a, "Repo A"), (repo_b, "Repo B")):
                repo_root.mkdir()
                _git_repo(repo_root)
                paths = WilyPaths(repo_root)
                paths.wily_dir.mkdir()
                save_tasks(paths, title, [Task(id="T01", title=title, status=TaskStatus.IN_PROGRESS, actor="wily")])
            registry = base / "registry.json"
            save_registry(registry, [RegisteredRepo(path=repo_a, repo="R-W-LAB/a"), RegisteredRepo(path=repo_b, repo="R-W-LAB/b")])
            snapshots: list[dict[str, object]] = []

            def fake_publish_snapshot(_config: AgentConfig, payload: dict[str, object]) -> dict[str, object]:
                snapshots.append(payload)
                return {"sent": False, "reason": "repo a down"} if payload["repo_slug"] == "R-W-LAB/a" else {"sent": True, "status": 202}

            with patch.object(daemon, "publish_snapshot", side_effect=fake_publish_snapshot), patch.object(
                daemon,
                "publish_heartbeat",
                return_value={"sent": True, "status": 202},
            ):
                daemon.run_once(
                    AgentConfig(board_url="https://board.example", token="token", actor="wily"),
                    registry,
                    sync_health_path=base / "sync-health.json",
                )

            self.assertEqual(snapshots[0]["repo_slug"], "R-W-LAB/a")
            self.assertEqual(snapshots[1]["repo_slug"], "R-W-LAB/b")
            self.assertEqual(snapshots[1]["sync_health"]["pending_snapshot_sha"], "")

    def test_agent_legacy_live_config_does_not_record_token_snapshot_failure(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo
        from wily.agent.sync_health import load_sync_health

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            health_path = root / "sync-health.json"

            with patch.object(daemon, "publish_snapshot", side_effect=AssertionError("token snapshot should not run")), patch.object(
                daemon,
                "publish_event",
                return_value={"sent": True, "status": 202},
            ):
                result = daemon.publish_repo_heartbeat(
                    AgentConfig(board_url="https://board.example", repo="R-W-LAB/demo", actor="wily", secret="secret"),
                    RegisteredRepo(path=root, repo="R-W-LAB/demo"),
                    include_snapshot=True,
                    sync_health_path=health_path,
                )

            self.assertEqual(result["snapshot"], {"sent": False, "reason": "not configured"})
            self.assertEqual(result["heartbeat"]["sent"], True)
            self.assertEqual(load_sync_health(health_path)["last_failure_reason"], "")

    def test_agent_failed_debounced_snapshot_retries_before_fallback_window(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo

        class StopLoop(Exception):
            pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            repo = RegisteredRepo(path=root, repo="R-W-LAB/demo")
            config = AgentConfig(board_url="https://board.example", token="token", actor="wily", heartbeat_interval=999)
            times = iter([0.0, 1.0, 4.5, 5.0])
            mtimes = iter([2.0, 2.0, 2.0])
            sleep_calls = 0
            current_time: float | str = "initial"
            snapshot_publish_times: list[float | str] = []

            def fake_sleep(_seconds: float) -> None:
                nonlocal sleep_calls
                if sleep_calls >= 3:
                    raise StopLoop()
                sleep_calls += 1

            def fake_monotonic() -> float:
                nonlocal current_time
                current_time = next(times)
                return float(current_time)

            def fake_publish(_config: AgentConfig, _repo: RegisteredRepo, *, include_snapshot: bool = True, **_kwargs: object) -> dict[str, object]:
                if include_snapshot:
                    snapshot_publish_times.append(current_time)
                sent = current_time != 4.5
                return {"repo": str(root), "snapshot": {"sent": sent}, "heartbeat": {"sent": True}}

            with patch.object(daemon, "load_registry", return_value=[repo]), patch.object(
                daemon,
                "publish_repo_heartbeat",
                side_effect=fake_publish,
            ), patch.object(daemon, "wily_tree_mtime", side_effect=lambda _path: next(mtimes)), patch.object(
                daemon.time,
                "sleep",
                side_effect=fake_sleep,
            ), patch.object(daemon.time, "monotonic", side_effect=fake_monotonic), patch.object(
                daemon,
                "SNAPSHOT_DEBOUNCE_SECONDS",
                2.0,
            ), patch.object(
                daemon,
                "SNAPSHOT_FALLBACK_SECONDS",
                60.0,
            ):
                with self.assertRaises(StopLoop):
                    daemon.run_loop(config, root / "registry.json", once=False, offline_ok=False)

            self.assertEqual(snapshot_publish_times, ["initial", 4.5, 5.0])

    def test_agent_snapshot_presence_is_idle_without_active_task(self) -> None:
        from wily.agent.snapshot import build_snapshot_payload

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="Ready task", status=TaskStatus.READY)])

            payload = build_snapshot_payload(root, repo="R-W-LAB/demo", actor="wily")

            self.assertEqual(payload["presence"]["status"], "idle")
            self.assertIsNone(payload["presence"]["current_task_id"])
            self.assertIsNone(payload["presence"]["current_cp"])

    def test_agent_daemon_debounces_wily_changes_and_sends_fallback_snapshots(self) -> None:
        from wily.agent import daemon
        from wily.agent.registry import RegisteredRepo

        class StopLoop(Exception):
            pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            save_tasks(paths, "demo", [Task(id="T01", title="First", status=TaskStatus.IN_PROGRESS, actor="wily")])
            repo = RegisteredRepo(path=root, repo="R-W-LAB/demo")
            config = AgentConfig(board_url="https://board.example", token="token", actor="wily", heartbeat_interval=999)
            times = iter([0.0, 1.0, 2.0, 4.5, 16.0])
            mtimes = iter([1.0, 2.0, 2.0, 2.0])
            sleep_calls = 0
            current_time: float | str = "initial"
            snapshot_publish_times: list[float | str] = []

            def fake_sleep(_seconds: float) -> None:
                nonlocal sleep_calls
                if sleep_calls >= 4:
                    raise StopLoop()
                sleep_calls += 1

            def fake_monotonic() -> float:
                nonlocal current_time
                current_time = next(times)
                return float(current_time)

            def fake_publish(_config: AgentConfig, _repo: RegisteredRepo, *, include_snapshot: bool = True, **_kwargs: object) -> dict[str, object]:
                if include_snapshot:
                    snapshot_publish_times.append(current_time)
                return {"repo": str(root), "snapshot": {"sent": include_snapshot}, "heartbeat": {"sent": True}}

            with patch.object(daemon, "load_registry", return_value=[repo]), patch.object(
                daemon,
                "publish_repo_heartbeat",
                side_effect=fake_publish,
            ), patch.object(daemon, "wily_tree_mtime", side_effect=lambda _path: next(mtimes)), patch.object(
                daemon.time,
                "sleep",
                side_effect=fake_sleep,
            ), patch.object(daemon.time, "monotonic", side_effect=fake_monotonic), patch.object(
                daemon,
                "SNAPSHOT_DEBOUNCE_SECONDS",
                2.0,
            ), patch.object(
                daemon,
                "SNAPSHOT_FALLBACK_SECONDS",
                10.0,
            ):
                with self.assertRaises(StopLoop):
                    daemon.run_loop(config, root / "registry.json", once=False, offline_ok=False)

            self.assertEqual(snapshot_publish_times, ["initial", 4.5, 16.0])

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
            self.assertEqual(summary.done_cp_names, ["plan"])
            self.assertEqual(summary.last_event_at, "2026-05-18T00:01:00Z")
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

    def test_doctor_reports_invalid_coordination_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_tasks(paths, "Parent Project", [])
            (paths.wily_dir / "coordination.yaml").write_text("schema: wrong\nrepos: []\n", encoding="utf-8")

            with chdir_compat(parent):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(doctor_cmd.main(["--json"]), 2)

            payload = json.loads(stdout.getvalue())
            diagnostics = payload["diagnostics"]
            self.assertTrue(any(item["code"] == "coordination-config" and item["level"] == "fail" for item in diagnostics))

    def test_doctor_reports_malformed_coordination_config_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_tasks(paths, "Parent Project", [])
            (paths.wily_dir / "coordination.yaml").write_text("schema: [\n", encoding="utf-8")

            with chdir_compat(parent):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(doctor_cmd.main(["--json"]), 2)

            diagnostics = json.loads(stdout.getvalue())["diagnostics"]
            self.assertTrue(any(item["code"] == "coordination-config" and item["level"] == "fail" for item in diagnostics))

    def test_doctor_aggregates_coordination_parent_and_child_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            _git_repo(parent)
            _write_coordination(parent)
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            for repo in (parent, child):
                (repo / ".venv").mkdir()
                hook = repo / ".git" / "hooks" / "pre-commit"
                hook.write_text("python wily.py replan drift-guard --from-hook\n", encoding="utf-8")

            parent_paths = WilyPaths(parent)
            child_paths = WilyPaths(child)
            save_tasks(parent_paths, "Parent Project", [Task(id="T01", title="Parent task", depends_on=["T99"])])
            save_tasks(child_paths, "Child Project", [Task(id="C01", title="Child task", depends_on=["C99"])])
            child_paths.task_dir("C77").mkdir(parents=True)

            with chdir_compat(parent):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(doctor_cmd.main(["--json"]), 2)

            diagnostics = json.loads(stdout.getvalue())["diagnostics"]
            broken = [item for item in diagnostics if item["code"] == "broken-depends-on"]
            self.assertEqual({item["repo"] for item in broken}, {"parent", "roadmap"})
            self.assertTrue(any(item["repo"] == "parent" and "T01" in item["message"] for item in broken))
            self.assertTrue(any(item["repo"] == "roadmap" and "C01" in item["message"] for item in broken))
            self.assertTrue(any(item["code"] == "orphan-task-dir" and item["repo"] == "roadmap" for item in diagnostics))

    def test_doctor_reports_missing_coordination_repo_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            _git_repo(parent)
            _write_coordination(parent, child_path="./missing-child")
            paths = WilyPaths(parent)
            (parent / ".venv").mkdir()
            (parent / ".git" / "hooks" / "pre-commit").write_text("python wily.py replan drift-guard --from-hook\n", encoding="utf-8")
            save_tasks(paths, "Parent Project", [])

            with chdir_compat(parent):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(doctor_cmd.main(["--json"]), 2)

            diagnostics = json.loads(stdout.getvalue())["diagnostics"]
            self.assertTrue(
                any(item["code"] == "coordination-repo-path" and item["repo"] == "roadmap" and item["level"] == "fail" for item in diagnostics)
            )

    def test_doctor_warns_for_coordination_legacy_handoffs_and_missing_child_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            _git_repo(parent)
            _write_coordination(parent)
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            for repo in (parent, child):
                (repo / ".venv").mkdir()
                save_tasks(WilyPaths(repo), f"{repo.name} Project", [])
            parent_hook = parent / ".git" / "hooks" / "pre-commit"
            parent_hook.write_text("python wily.py replan drift-guard --from-hook\n", encoding="utf-8")
            (parent / "agent-handoffs").mkdir()
            (parent / "agent-handoffs" / "t01-status.md").write_text("# status\n", encoding="utf-8")

            with chdir_compat(parent):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(doctor_cmd.main(["--json"]), 1)

            diagnostics = json.loads(stdout.getvalue())["diagnostics"]
            self.assertTrue(
                any(item["code"] == "legacy-handoff-location" and item["repo"] == "parent" for item in diagnostics)
            )
            self.assertTrue(
                any(item["code"] == "pre-commit-hook" and item["repo"] == "roadmap" for item in diagnostics)
            )
            self.assertFalse(any(item["code"] == "pre-commit-hook" and item["repo"] == "parent" and item["level"] == "warn" for item in diagnostics))

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

    def test_cp_import_status_uses_custom_workflow_checkpoint_column_when_present(self) -> None:
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
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP01 | DONE | Baseline and contract tests | root | ok |",
                        "| CP02 | RUNNING | Snapshot identity and timeline | root | current |",
                    ]
                ),
                encoding="utf-8",
            )

            with chdir_compat(root):
                self.assertEqual(cp_cmd.main(["T01", "import-status", str(status.relative_to(root)), "--actor", "wily"]), 0)

            self.assertEqual(
                [(event.cp, event.event, event.note) for event in read_events(paths, "T01")],
                [
                    ("Baseline and contract tests", "start", None),
                    ("Baseline and contract tests", "done", "ok"),
                    ("Snapshot identity and timeline", "start", None),
                ],
            )

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

    def test_coordination_config_loads_parent_owned_repo_registry(self) -> None:
        from wily.coordination import load_coordination_config

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            wily_dir = parent / ".wily"
            wily_dir.mkdir()
            (wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "    title: Wily Roadmap",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_coordination_config(wily_dir / "coordination.yaml")

            self.assertEqual(config.title, "Parent Project")
            self.assertEqual(config.parent.id, "parent")
            self.assertEqual(config.parent.path, parent.resolve())
            self.assertEqual([repo.id for repo in config.repos], ["roadmap"])
            self.assertEqual(config.repos[0].path, child.resolve())

    def test_coordination_context_prefers_parent_mode_but_child_wily_wins_inside_child_repo(self) -> None:
        from wily.coordination import resolve_project_context

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_tasks(paths, "Parent Project", [Task(id="T01", title="Parent ready")])
            child = parent / "wily-roadmap"
            child.mkdir()
            save_tasks(WilyPaths(child), "Child Project", [Task(id="C01", title="Child ready")])
            (paths.wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (parent / "wily-workspace.yaml").write_text(
                "schema: wily-workspace-v1\ntitle: Manifest Only\nrepos: []\n",
                encoding="utf-8",
            )

            parent_context = resolve_project_context(parent / "nested")
            child_context = resolve_project_context(child)

            self.assertEqual(parent_context.active_mode, "coordination")
            self.assertEqual(parent_context.paths.root, parent.resolve())
            self.assertEqual(parent_context.repo_id_for_path(parent / "README.md"), "parent")
            self.assertEqual(parent_context.repo_id_for_path(child / "src" / "app.py"), "roadmap")
            self.assertEqual(child_context.active_mode, "single_repo")
            self.assertEqual(child_context.paths.root, child.resolve())
            self.assertIsNone(child_context.coordination)

    def test_scope_normalization_accepts_repo_qualified_and_structured_entries(self) -> None:
        from wily.scope import ScopeEntry, normalize_scope_entries, scope_to_yaml

        entries = normalize_scope_entries(
            [
                "parent:README.md",
                "roadmap:src/**",
                {"repo": "board", "path": "app/**"},
                "legacy/**",
            ],
            default_repo="parent",
            coordination=True,
        )

        self.assertEqual(
            entries,
            [
                ScopeEntry(repo="parent", path="README.md", source="parent:README.md"),
                ScopeEntry(repo="roadmap", path="src/**", source="roadmap:src/**"),
                ScopeEntry(repo="board", path="app/**", source={"repo": "board", "path": "app/**"}),
                ScopeEntry(repo="parent", path="legacy/**", source="legacy/**"),
            ],
        )
        self.assertEqual(
            scope_to_yaml(entries),
            [
                "parent:README.md",
                "roadmap:src/**",
                {"repo": "board", "path": "app/**"},
                "legacy/**",
            ],
        )

    def test_scope_matching_is_repo_aware_in_coordination_mode(self) -> None:
        from wily.scope import file_matches_scope, normalize_scope_entries

        scope = normalize_scope_entries(["parent:README.md", "roadmap:src/**"], default_repo="parent", coordination=True)

        self.assertTrue(file_matches_scope(scope, repo_id="parent", path="README.md"))
        self.assertTrue(file_matches_scope(scope, repo_id="roadmap", path="src/app.py"))
        self.assertFalse(file_matches_scope(scope, repo_id="board", path="src/app.py"))
        self.assertFalse(file_matches_scope(scope, repo_id="roadmap", path="README.md"))

    def test_task_serializes_claim_snapshot_and_structured_scope(self) -> None:
        snapshot = {
            "schema": "wily-claim-snapshot-v1",
            "repos": {
                "parent": {"git_available": False, "branch": None, "sha": None, "dirty": False, "changed_files": [], "fingerprints": {}},
                "roadmap": {"git_available": True, "branch": "main", "sha": "abc", "dirty": True, "changed_files": ["src/app.py"], "fingerprints": {}},
            },
        }

        task = Task(
            id="T01",
            title="Coordination",
            scope=[{"repo": "roadmap", "path": "src/**"}],
            claim_snapshot=snapshot,
        )
        data = task.to_dict()
        loaded = Task.from_dict(data)
        claimed = apply_claim(loaded, actor="wily", sha=None, at="now", claim_snapshot=snapshot)

        self.assertEqual(data["claim_snapshot"], snapshot)
        self.assertEqual(loaded.claim_snapshot, snapshot)
        self.assertEqual(loaded.scope, [{"repo": "roadmap", "path": "src/**"}])
        self.assertIsNone(claimed.claim_sha)
        self.assertEqual(claimed.claim_snapshot, snapshot)

    def test_coordination_claim_from_non_git_parent_records_claim_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            save_tasks(WilyPaths(child), "Child Project", [])
            subprocess.run(["git", "add", ".wily"], cwd=child, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "child wily"], cwd=child, check=True)
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent task", intent="do it", acceptance="done", scope=["roadmap:src/**"])],
            )
            (paths.wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "claim", "T01", "--as", "wily", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            task_payload = payload["task"]
            self.assertEqual(task_payload["status"], "in_progress")
            self.assertIsNone(task_payload["claim_sha"])
            self.assertEqual(task_payload["claim_snapshot"]["schema"], "wily-claim-snapshot-v1")
            repos = task_payload["claim_snapshot"]["repos"]
            self.assertFalse(repos["parent"]["git_available"])
            self.assertIsNone(repos["parent"]["sha"])
            self.assertTrue(repos["roadmap"]["git_available"])
            self.assertTrue(repos["roadmap"]["branch"])
            self.assertEqual(
                repos["roadmap"]["sha"],
                subprocess.run(["git", "rev-parse", "HEAD"], cwd=child, capture_output=True, text=True, check=True).stdout.strip(),
            )
            self.assertTrue(repos["roadmap"]["dirty"])
            self.assertIn("src/app.py", repos["roadmap"]["changed_files"])
            fingerprint = repos["roadmap"]["fingerprints"]["src/app.py"]
            self.assertEqual(fingerprint["kind"], "file")
            self.assertEqual(len(fingerprint["sha256"]), 64)
            _, tasks = load_tasks(paths)
            self.assertIsNone(tasks[0].claim_sha)
            self.assertIn("roadmap", tasks[0].claim_snapshot["repos"])

    def test_coordination_done_from_non_git_parent_reports_child_changes_from_claim_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent task", intent="do it", acceptance="done", scope=["roadmap:src/**"])],
            )
            (paths.wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            claim = subprocess.run(
                [sys.executable, str(SCRIPT), "claim", "T01", "--as", "wily", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

            done = subprocess.run(
                [sys.executable, str(SCRIPT), "done", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(done.returncode, 0, done.stderr)
            payload = json.loads(done.stdout)
            self.assertEqual(payload["changed_files"], ["roadmap:src/app.py"])
            self.assertEqual(payload["task"]["status"], "done")
            self.assertIn("roadmap:src/app.py", paths.result_md("T01").read_text(encoding="utf-8"))

    def test_coordination_done_rejects_drift_stub_in_parent_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent task", intent="do it", acceptance="done", scope=["roadmap:src/**"])],
            )
            claim = subprocess.run(
                [sys.executable, str(SCRIPT), "claim", "T01", "--as", "wily", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            (child / "docs").mkdir()
            (child / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")

            done = subprocess.run(
                [sys.executable, str(SCRIPT), "done", "T01", "--stub-drift"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(done.returncode, 3)
            self.assertIn("--stub-drift is not supported in coordination mode", done.stderr)
            _, tasks = load_tasks(paths)
            self.assertEqual([task.id for task in tasks], ["T01"])
            self.assertEqual(tasks[0].status, TaskStatus.IN_PROGRESS)
            self.assertFalse(paths.result_md("T01").exists())
            self.assertFalse(paths.task_dir("T02").exists())

    def test_coordination_cp_status_next_and_watch_use_parent_tasks_and_expose_active_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent ready", intent="do it", acceptance="done", scope=["roadmap:src/**"])],
            )
            (paths.wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            cp = subprocess.run(
                [sys.executable, str(SCRIPT), "cp", "T01", "start", "plan", "--actor", "wily"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            status = subprocess.run(
                [sys.executable, str(SCRIPT), "status", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            next_result = subprocess.run(
                [sys.executable, str(SCRIPT), "next", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            watch = subprocess.run(
                [sys.executable, str(SCRIPT), "watch", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            status_text = subprocess.run(
                [sys.executable, str(SCRIPT), "status", "--ui", "ascii"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("T01 cp start: plan", cp.stdout)
            self.assertEqual(status.returncode, 1, status.stderr)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["active_mode"], "coordination")
            self.assertEqual(status_payload["tasks"][0]["id"], "T01")
            self.assertEqual(status_payload["cp"]["T01"]["current_cp"], "plan")
            self.assertEqual(next_result.returncode, 0, next_result.stderr)
            next_payload = json.loads(next_result.stdout)
            self.assertEqual(next_payload["active_mode"], "coordination")
            self.assertEqual(next_payload["task"]["id"], "T01")
            self.assertEqual(watch.returncode, 1, watch.stderr)
            watch_payload = json.loads(watch.stdout)
            self.assertEqual(watch_payload["active_mode"], "coordination")
            self.assertEqual(watch_payload["tasks"][0]["id"], "T01")
            self.assertEqual(status_text.returncode, 1, status_text.stderr)
            self.assertIn("coordination", status_text.stdout)

    def test_coordination_cp_import_status_uses_parent_task_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            save_actors(paths, [Actor(id="wily", display="Wily")])
            save_tasks(paths, "Parent Project", [Task(id="T01", title="Parent ready", intent="do it", acceptance="done")])
            status_board = parent / "agent-handoffs" / "demo-status.md"
            status_board.parent.mkdir()
            status_board.write_text(
                "| Checkpoint | Status | Evidence |\n| --- | --- | --- |\n| Plan | DONE | imported |\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "cp", "T01", "import-status", str(status_board.relative_to(parent)), "--actor", "wily"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([(event.cp, event.event) for event in read_events(paths, "T01")], [("Plan", "start"), ("Plan", "done")])

    def test_coordination_cli_inside_registered_child_uses_child_local_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            save_tasks(WilyPaths(parent), "Parent Project", [Task(id="T01", title="Parent ready", intent="do it", acceptance="done")])
            save_tasks(WilyPaths(child), "Child Project", [Task(id="C01", title="Child ready", intent="do it", acceptance="done")])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "next", "--json"],
                cwd=child,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["id"], "C01")
            self.assertNotIn("active_mode", payload)

    def test_coordination_done_filters_unchanged_claim_dirty_files_and_reports_mixed_files(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            (child / "src").mkdir()
            (child / "src" / "pre.py").write_text("pre\n", encoding="utf-8")
            (child / "src" / "mixed.py").write_text("before\n", encoding="utf-8")
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            paths = WilyPaths(parent)
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Dirty done", status=TaskStatus.IN_PROGRESS, actor="wily", scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            (child / "src" / "mixed.py").write_text("after\n", encoding="utf-8")
            (child / "src" / "new.py").write_text("new\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "done", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["changed_files"], ["roadmap:src/mixed.py", "roadmap:src/new.py"])

    def test_coordination_done_accepts_structured_repo_scope(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            paths = WilyPaths(parent)
            save_tasks(
                paths,
                "Parent Project",
                [
                    Task(
                        id="T01",
                        title="Structured scope",
                        status=TaskStatus.IN_PROGRESS,
                        actor="wily",
                        scope=[{"repo": "roadmap", "path": "src/**"}],
                        claim_snapshot=snapshot,
                    )
                ],
            )
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("app\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "done", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["changed_files"], ["roadmap:src/app.py"])

    def test_coordination_land_dry_run_blocks_parent_artifact_when_parent_is_not_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            (parent / "docs").mkdir()
            (parent / "docs" / "spec.md").write_text("parent work\n", encoding="utf-8")
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent artifact", status=TaskStatus.DONE, scope=["parent:docs/**"])],
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("parent:docs/spec.md", payload["parent_task_artifact_changes"])
            self.assertEqual(payload["errors"][0]["code"], "parent_not_git")

    def test_coordination_land_blocks_parent_artifact_before_commit_when_parent_is_not_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            (parent / "docs").mkdir()
            (parent / "docs" / "spec.md").write_text("parent work\n", encoding="utf-8")
            save_tasks(paths, "Parent Project", [Task(id="T01", title="Parent artifact", status=TaskStatus.DONE, scope=["parent:docs/**"])])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "parent_not_git")

    def test_coordination_land_dry_run_blocks_out_of_scope_child_changes_before_staging(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Child work", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("app\n", encoding="utf-8")
            (child / "docs").mkdir()
            (child / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=child, capture_output=True, text=True, check=True)

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            self.assertEqual(staged.stdout.strip(), "")
            payload = json.loads(result.stdout)
            repo = payload["repos"]["roadmap"]
            self.assertEqual(repo["task_candidate_changes"], ["src/app.py"])
            self.assertEqual(repo["out_of_scope_changes"], ["docs/outside.md"])
            self.assertEqual(payload["errors"][0]["code"], "out_of_scope_changes")

    def test_coordination_land_blocks_out_of_scope_child_changes_before_staging(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(paths, "Parent Project", [Task(id="T01", title="Child work", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)])
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("app\n", encoding="utf-8")
            (child / "docs").mkdir()
            (child / "docs" / "outside.md").write_text("outside\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=child, capture_output=True, text=True, check=True)

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "out_of_scope_changes")
            self.assertEqual(staged.stdout.strip(), "")

    def test_coordination_land_dry_run_allows_child_only_changes_with_parent_ledger_reported(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Child work", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# result\n", encoding="utf-8")
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("app\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertFalse(payload["parent_git_required"])
            self.assertIn(".wily/tasks.yaml", payload["parent_ledger_changes"])
            self.assertIn(".wily/tasks/T01/result.md", payload["parent_ledger_changes"])
            self.assertEqual(payload["repos"]["roadmap"]["task_candidate_changes"], ["src/app.py"])

    def test_coordination_land_commits_parent_git_artifacts(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            _git_repo(parent)
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent commit", status=TaskStatus.DONE, scope=["parent:docs/**"], claim_snapshot=snapshot)],
            )
            (parent / "docs").mkdir()
            (parent / "docs" / "spec.md").write_text("parent\n", encoding="utf-8")

            dry_run = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--no-push"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            payload = json.loads(dry_run.stdout)
            self.assertEqual(payload["repos"]["parent"]["task_candidate_changes"], ["docs/spec.md"])
            self.assertEqual(result.returncode, 0, result.stderr)
            message = subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=parent, capture_output=True, text=True, check=True).stdout
            committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=parent, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertIn("Wily-Task: T01", message)
            self.assertEqual(committed, ["docs/spec.md"])

    def test_coordination_land_blocks_out_of_scope_parent_git_changes(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            _git_repo(parent)
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Parent guarded", status=TaskStatus.DONE, scope=["parent:docs/**"], claim_snapshot=snapshot)],
            )
            (parent / "docs").mkdir()
            (parent / "docs" / "spec.md").write_text("parent\n", encoding="utf-8")
            (parent / "notes.txt").write_text("outside\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=parent, capture_output=True, text=True, check=True)

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            self.assertEqual(staged.stdout.strip(), "")
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["repos"]["parent"]["task_candidate_changes"], ["docs/spec.md"])
            self.assertEqual(payload["repos"]["parent"]["out_of_scope_changes"], ["notes.txt"])
            self.assertIn({"code": "out_of_scope_changes", "repo": "parent", "files": ["notes.txt"]}, payload["errors"])

    def test_coordination_claim_snapshot_excludes_registered_child_repos_from_parent_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            _git_repo(parent)
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            save_actors(paths, [Actor(id="wily", display="Wily", git_author_emails=["wily@example.com"])])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Claim snapshot", intent="do it", acceptance="done", scope=["roadmap:src/**"])],
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "claim", "T01", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            task = json.loads(result.stdout)["task"]
            parent_changed = task["claim_snapshot"]["repos"]["parent"]["changed_files"]
            self.assertNotIn("wily-roadmap/README.md", parent_changed)
            self.assertFalse(any(path.startswith("wily-roadmap/.git/") for path in parent_changed))

    def test_coordination_land_dry_run_classifies_pre_existing_task_candidate_and_mixed_files(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            (child / "src").mkdir()
            (child / "src" / "pre.py").write_text("pre\n", encoding="utf-8")
            (child / "src" / "mixed.py").write_text("before\n", encoding="utf-8")
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            paths = WilyPaths(parent)
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Dirty baseline", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            (child / "src" / "mixed.py").write_text("after\n", encoding="utf-8")
            (child / "src" / "new.py").write_text("new\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            payload = json.loads(result.stdout)
            repo = payload["repos"]["roadmap"]
            self.assertEqual(repo["pre_existing_dirty"], ["src/pre.py"])
            self.assertEqual(repo["mixed_files"], ["src/mixed.py"])
            self.assertEqual(repo["task_candidate_changes"], ["src/new.py"])
            self.assertEqual(payload["errors"][0]["code"], "mixed_files")

    def test_coordination_land_dry_run_allows_mixed_files_only_with_explicit_include(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            (child / "src").mkdir()
            (child / "src" / "mixed.py").write_text("before\n", encoding="utf-8")
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            paths = WilyPaths(parent)
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Mixed", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            (child / "src" / "mixed.py").write_text("after\n", encoding="utf-8")

            by_file = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json", "--include", "roadmap:src/mixed.py"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            by_flag = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json", "--include-mixed"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(by_file.returncode, 0, by_file.stderr)
            self.assertEqual(by_flag.returncode, 0, by_flag.stderr)
            self.assertTrue(json.loads(by_file.stdout)["ok"])
            self.assertEqual(json.loads(by_flag.stdout)["repos"]["roadmap"]["included_mixed_files"], ["src/mixed.py"])

    def test_coordination_land_dry_run_rejects_invalid_explicit_include(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            (child / "src").mkdir()
            (child / "src" / "mixed.py").write_text("before\n", encoding="utf-8")
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            paths = WilyPaths(parent)
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Mixed", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            (child / "src" / "mixed.py").write_text("after\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--dry-run", "--json", "--include", "wrong:src/mixed.py"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_TRANSITION)
            payload = json.loads(result.stdout)
            self.assertIn({"code": "invalid_include", "message": "--include must name an existing mixed file as <repo:path>", "files": ["wrong:src/mixed.py"]}, payload["errors"])

    def test_coordination_land_commits_child_only_repo_changes_without_parent_git(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", child)])
            save_tasks(
                paths,
                "Parent Project",
                [Task(id="T01", title="Child commit", status=TaskStatus.DONE, scope=["roadmap:src/**"], claim_snapshot=snapshot)],
            )
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# result\n\n- changed files: 1\n", encoding="utf-8")
            (child / "src").mkdir()
            (child / "src" / "app.py").write_text("app\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--no-push"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            message = subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=child, capture_output=True, text=True, check=True).stdout
            committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=child, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertIn("Wily-Task: T01", message)
            self.assertEqual(committed, ["src/app.py"])
            self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=child, capture_output=True, text=True, check=True).stdout.strip(), "")

    def test_coordination_land_commits_one_local_commit_per_touched_child_repo(self) -> None:
        from wily.observation import claim_snapshot_for_repos

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            _git_repo(roadmap)
            _git_repo(board)
            paths = WilyPaths(parent)
            paths.wily_dir.mkdir()
            (paths.wily_dir / "coordination.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-coordination-v1",
                        "title: Parent Project",
                        "parent:",
                        "  id: parent",
                        "  path: .",
                        "repos:",
                        "  - id: roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: board",
                        "    path: ./wily-board",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            snapshot = claim_snapshot_for_repos([("parent", parent), ("roadmap", roadmap), ("board", board)])
            save_tasks(
                paths,
                "Parent Project",
                [
                    Task(
                        id="T01",
                        title="Multi repo",
                        status=TaskStatus.DONE,
                        scope=["roadmap:src/**", "board:app/**"],
                        claim_snapshot=snapshot,
                    )
                ],
            )
            (roadmap / "src").mkdir()
            (roadmap / "src" / "app.py").write_text("app\n", encoding="utf-8")
            (board / "app").mkdir()
            (board / "app" / "ui.py").write_text("ui\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--no-push"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for repo, expected in ((roadmap, "src/app.py"), (board, "app/ui.py")):
                message = subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout
                committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.splitlines()
                self.assertIn("Wily-Task: T01", message)
                self.assertEqual(committed, [expected])

    def test_coordination_land_rejects_push_before_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "wily-roadmap"
            child.mkdir()
            _git_repo(child)
            _write_coordination(parent)
            paths = WilyPaths(parent)
            save_tasks(paths, "Parent Project", [Task(id="T01", title="No push", status=TaskStatus.DONE)])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "land", "T01", "--push", "--dry-run"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_USAGE)
            self.assertIn("--push is not supported in coordination mode", result.stderr)

    def test_workspace_manifest_discovery_prefers_visible_manifest(self) -> None:
        from wily.workspace import discover_workspace_manifest, load_workspace

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            (parent / ".wily-workspace.yaml").write_text(
                "schema: wily-workspace-v1\ntitle: Hidden\nrepos: []\n",
                encoding="utf-8",
            )
            (parent / "wily-workspace.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Wily Plugin Workspace",
                        "repos:",
                        "  - id: wily-roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: wily-board",
                        "    path: ./wily-board",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            nested = parent / "nested" / "deep"
            nested.mkdir(parents=True)

            manifest = discover_workspace_manifest(nested)
            workspace = load_workspace(manifest)

            self.assertEqual(manifest, (parent / "wily-workspace.yaml").resolve())
            self.assertEqual(workspace.title, "Wily Plugin Workspace")
            self.assertEqual([repo.id for repo in workspace.repos], ["wily-roadmap", "wily-board"])
            self.assertEqual(workspace.repos[0].path, roadmap.resolve())
            self.assertEqual(workspace.repos[1].path, board.resolve())

    def test_workspace_manifest_discovery_accepts_dotfile_fallback(self) -> None:
        from wily.workspace import discover_workspace_manifest, load_workspace

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            (parent / "repo").mkdir()
            (parent / ".wily-workspace.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Dotfile Workspace",
                        "repos:",
                        "  - id: repo",
                        "    path: ./repo",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            manifest = discover_workspace_manifest(parent / "child")
            workspace = load_workspace(manifest)

            self.assertEqual(manifest, (parent / ".wily-workspace.yaml").resolve())
            self.assertEqual(workspace.title, "Dotfile Workspace")
            self.assertEqual(workspace.repos[0].path, (parent / "repo").resolve())

    def test_workspace_snapshot_summarizes_child_repos_and_invalid_repos(self) -> None:
        from wily.workspace import load_workspace, workspace_snapshot

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            save_tasks(
                WilyPaths(roadmap),
                "Roadmap",
                [
                    Task(id="R01", title="Done", status=TaskStatus.DONE),
                    Task(id="R02", title="Active", status=TaskStatus.IN_PROGRESS, actor="wily"),
                    Task(id="R03", title="Ready", status=TaskStatus.READY, priority=1),
                    Task(id="R04", title="Waiting", status=TaskStatus.READY, depends_on=["R02"], priority=2),
                    Task(id="R05", title="Blocked", status=TaskStatus.BLOCKED, blocker="needs API"),
                ],
            )
            save_actors(WilyPaths(roadmap), [Actor(id="wily", display="Wily")])
            save_tasks(
                WilyPaths(board),
                "Board",
                [
                    Task(id="B01", title="Board ready", status=TaskStatus.READY),
                    Task(id="B02", title="Board blocked", status=TaskStatus.BLOCKED, blocker="needs design"),
                ],
            )
            manifest = parent / "wily-workspace.yaml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Wily Plugin Workspace",
                        "repos:",
                        "  - id: wily-roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: wily-board",
                        "    path: ./wily-board",
                        "  - id: missing",
                        "    path: ./missing",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            snapshot = workspace_snapshot(load_workspace(manifest))
            repos = {repo["id"]: repo for repo in snapshot["repos"]}

            self.assertEqual(snapshot["title"], "Wily Plugin Workspace")
            self.assertEqual(repos["wily-roadmap"]["project_title"], "Roadmap")
            self.assertEqual(repos["wily-roadmap"]["mode"], "solo")
            self.assertEqual(
                repos["wily-roadmap"]["progress"],
                {"total": 5, "done": 1, "in_progress": 1, "ready": 2, "blocked": 1, "waiting": 1, "percent_done": 20},
            )
            self.assertEqual([task["id"] for task in repos["wily-roadmap"]["in_progress_tasks"]], ["R02"])
            self.assertEqual([task["id"] for task in repos["wily-roadmap"]["next_tasks"]], ["R03"])
            self.assertEqual([task["id"] for task in repos["wily-roadmap"]["waiting_tasks"]], ["R04"])
            self.assertEqual(repos["wily-roadmap"]["blocked_tasks"][0]["blocker"], "needs API")
            self.assertEqual([task["id"] for task in repos["wily-board"]["next_tasks"]], ["B01"])
            self.assertIn("error", repos["missing"])

    def test_workspace_next_aggregates_ready_tasks_without_claiming(self) -> None:
        from wily.workspace import load_workspace, workspace_next_tasks

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            save_tasks(WilyPaths(roadmap), "Roadmap", [Task(id="R01", title="Roadmap ready", status=TaskStatus.READY)])
            save_tasks(WilyPaths(board), "Board", [Task(id="B01", title="Board ready", status=TaskStatus.READY)])
            manifest = parent / "wily-workspace.yaml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Wily Plugin Workspace",
                        "repos:",
                        "  - id: wily-roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: wily-board",
                        "    path: ./wily-board",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            tasks = workspace_next_tasks(load_workspace(manifest))

            self.assertEqual([(task["repo_id"], task["id"]) for task in tasks], [("wily-roadmap", "R01"), ("wily-board", "B01")])
            self.assertEqual(load_tasks(WilyPaths(roadmap))[1][0].status, TaskStatus.READY)
            self.assertEqual(load_tasks(WilyPaths(board))[1][0].status, TaskStatus.READY)

    def test_workspace_cli_init_status_next_show_config_and_watch_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            save_tasks(WilyPaths(roadmap), "Roadmap", [Task(id="R01", title="Roadmap ready", status=TaskStatus.READY)])
            save_tasks(WilyPaths(board), "Board", [Task(id="B01", title="Board ready", status=TaskStatus.READY)])

            init = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "workspace",
                    "init",
                    "--repo",
                    "wily-roadmap=./wily-roadmap",
                    "--repo",
                    "wily-board=./wily-board",
                    "--title",
                    "Wily Plugin Workspace",
                ],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            self.assertTrue((parent / "wily-workspace.yaml").exists())
            self.assertFalse((parent / ".wily").exists())

            show_config = subprocess.run(
                [sys.executable, str(SCRIPT), "workspace", "show-config", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(show_config.returncode, 0, show_config.stderr)
            config_payload = json.loads(show_config.stdout)
            self.assertEqual(config_payload["schema"], "wily-workspace-v1")
            self.assertEqual([repo["id"] for repo in config_payload["repos"]], ["wily-roadmap", "wily-board"])

            status = subprocess.run(
                [sys.executable, str(SCRIPT), "workspace", "status", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["title"], "Wily Plugin Workspace")
            self.assertEqual([repo["id"] for repo in status_payload["repos"]], ["wily-roadmap", "wily-board"])

            next_result = subprocess.run(
                [sys.executable, str(SCRIPT), "workspace", "next"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(next_result.returncode, 0, next_result.stderr)
            self.assertIn("wily-roadmap R01", next_result.stdout)
            self.assertIn("wily-board B01", next_result.stdout)

            watch = subprocess.run(
                [sys.executable, str(SCRIPT), "workspace", "watch", "--once"],
                cwd=parent,
                capture_output=True,
                text=True,
            )
            self.assertEqual(watch.returncode, 0, watch.stderr)
            self.assertIn("Wily Plugin Workspace", watch.stdout)
            self.assertIn("Roadmap", watch.stdout)
            self.assertFalse((parent / ".wily").exists())

    def test_workspace_watch_tracks_child_touch_mtimes_and_rejects_zero_interval(self) -> None:
        from wily.cli import workspace as workspace_cmd
        from wily.workspace import load_workspace

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            board = parent / "wily-board"
            roadmap.mkdir()
            board.mkdir()
            save_tasks(WilyPaths(roadmap), "Roadmap", [Task(id="R01", title="Ready", status=TaskStatus.READY)])
            save_tasks(WilyPaths(board), "Board", [Task(id="B01", title="Ready", status=TaskStatus.READY)])
            WilyPaths(roadmap).touch_file.touch()
            WilyPaths(board).touch_file.touch()
            manifest = parent / "wily-workspace.yaml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Wily Plugin Workspace",
                        "repos:",
                        "  - id: wily-roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: wily-board",
                        "    path: ./wily-board",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_workspace(manifest)

            first = workspace_cmd.workspace_touch_mtimes(config)
            WilyPaths(board).touch_file.write_text("changed", encoding="utf-8")
            second = workspace_cmd.workspace_touch_mtimes(config)

            self.assertEqual(len(first), 2)
            self.assertNotEqual(first, second)
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(workspace_cmd._interval(["--interval", "0"]), None)
            self.assertIn("--interval must be positive", stderr.getvalue())

    def test_workspace_next_reports_invalid_child_repos_without_hiding_valid_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            roadmap = parent / "wily-roadmap"
            roadmap.mkdir()
            save_tasks(WilyPaths(roadmap), "Roadmap", [Task(id="R01", title="Roadmap ready", status=TaskStatus.READY)])
            (parent / "wily-workspace.yaml").write_text(
                "\n".join(
                    [
                        "schema: wily-workspace-v1",
                        "title: Wily Plugin Workspace",
                        "repos:",
                        "  - id: wily-roadmap",
                        "    path: ./wily-roadmap",
                        "  - id: missing",
                        "    path: ./missing",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "workspace", "next"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wily-roadmap R01", result.stdout)
            self.assertIn("[missing] ERROR", result.stderr)

    def test_lifecycle_commands_do_not_treat_manifest_only_parent_as_wily_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspace"
            parent.mkdir()
            child = parent / "repo"
            child.mkdir()
            save_tasks(WilyPaths(child), "Child", [Task(id="C01", title="Child ready")])
            (parent / "wily-workspace.yaml").write_text(
                "schema: wily-workspace-v1\ntitle: Manifest Only\nrepos:\n  - id: repo\n    path: ./repo\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "status", "--json"],
                cwd=parent,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, _common.EXIT_FAILURE)
            self.assertIn("no .wily/ directory", result.stderr)
            self.assertFalse((parent / ".wily").exists())

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

    def test_watch_renderer_ascii_timeline_marks_done_current_and_pending(self) -> None:
        output = render_watch(
            project_title="Demo",
            tasks=[
                Task(
                    id="T01",
                    title="Timeline",
                    status=TaskStatus.IN_PROGRESS,
                    assignee="wily",
                ),
            ],
            actors=[],
            observed_commits=[],
            cp_summaries={
                "T01": CpSummary(
                    total=3,
                    done=1,
                    in_progress=1,
                    current_cp="verify",
                    cp_names=["plan", "verify", "ship"],
                    done_cp_names=["plan"],
                )
            },
            mode="solo",
            ui="ascii",
            show_timeline=True,
        )

        self.assertIn("[plan] > {verify} > ship", output)

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
            cp_summaries={
                "T02": CpSummary(
                    total=1,
                    done=0,
                    in_progress=1,
                    current_cp="verify",
                    cp_names=["verify"],
                    last_event_at="2026-05-18T11:00:00Z",
                )
            },
            ascii_mode=True,
            width=30,
        )
        text = "\n".join(t for t, _s in lines)
        self.assertIn("활동", text)
        self.assertIn("wily", text)
        self.assertIn("현재: T02 verify", text)
        self.assertIn("최근 활동: 2026-05-18T11:00:00Z", text)
        self.assertIn("최근 완료: T01", text)

    def test_render_watch_wide_width_includes_activity_panel(self) -> None:
        with patch("wily.ui.watch_render.get_terminal_size", return_value=os.terminal_size((132, 40))):
            output = render_watch(
                project_title="Demo",
                tasks=[
                    Task(id="T01", title="진행 중인 한글 작업", status=TaskStatus.IN_PROGRESS, actor="wily"),
                    Task(id="T02", title="완료된 작업", status=TaskStatus.DONE, actor="wily", done_at="2026-05-18T10:00:00Z"),
                ],
                actors=[Actor(id="wily", display="Wily", capacity=2)],
                observed_commits=[],
                cp_summaries={},
                mode="collab",
                ui="ascii",
            )

        self.assertIn(" | 활동", output)
        self.assertIn("현재: T01", output)
        self.assertIn("여력: 1/2", output)
        for line in output.splitlines():
            self.assertLessEqual(len(line), 132)

    def test_render_watch_rich_wide_activity_panel_does_not_raise_on_mixed_styles(self) -> None:
        with patch("wily.ui.watch_render.get_terminal_size", return_value=os.terminal_size((132, 40))):
            output = render_watch(
                project_title="Demo",
                tasks=[
                    Task(id="T01", title="진행 중인 한글 작업", status=TaskStatus.IN_PROGRESS, actor="wily"),
                    Task(id="T02", title="완료된 작업", status=TaskStatus.DONE, actor="wily", done_at="2026-05-18T10:00:00Z"),
                ],
                actors=[Actor(id="wily", display="Wily", capacity=2)],
                observed_commits=[],
                cp_summaries={},
                mode="collab",
                ui="rich",
            )

        self.assertIn("활동", output)
        self.assertIn("현재: T01", output)

    def test_render_watch_compact_width_does_not_exceed_terminal_width(self) -> None:
        with patch("wily.ui.watch_render.get_terminal_size", return_value=os.terminal_size((72, 24))):
            output = render_watch(
                project_title="Demo",
                tasks=[
                    Task(
                        id="T01",
                        title="한글 제목이 아주 길어도 compact watch 출력 폭을 넘기지 않아야 한다",
                        status=TaskStatus.IN_PROGRESS,
                        actor="wily",
                        claim_at="2026-05-18T10:00:00Z",
                    )
                ],
                actors=[],
                observed_commits=[],
                cp_summaries={},
                mode="solo",
                ui="ascii",
                compact=True,
            )

        for line in output.splitlines():
            self.assertLessEqual(_display_width(line), 72)

    def test_watch_status_args_forward_render_flags(self) -> None:
        stripped = watch_cmd.status_args_from_watch_args(
            ["--here", "--interval", "1", "--ui", "ascii", "--dry-run-pane", "--no-interactive", "--compact", "--show-timeline", "--hide-log"]
        )
        self.assertEqual(stripped, ["--ui", "ascii", "--compact", "--show-timeline", "--hide-log"])

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
                env={
                    **os.environ,
                    "WILY_AGENT_CONFIG": str(root / ".config" / "wily" / "agent" / "config.json"),
                    "WILY_AGENT_REGISTRY": str(root / ".config" / "wily" / "agent" / "registry.json"),
                },
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

    def test_replan_drift_guard_skips_coordination_parent_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            _write_coordination(root)
            paths = WilyPaths(root)
            save_tasks(paths, "demo", [Task(id="T01", title="Parent ready", scope=["roadmap:src/**"])])
            (root / "outside.md").write_text("outside\n", encoding="utf-8")
            subprocess.run(["git", "add", "outside.md"], cwd=root, check=True)

            with chdir_compat(root):
                self.assertEqual(replan_cmd.main(["drift-guard", "--from-hook"]), 0)

            _, tasks = load_tasks(paths)
            self.assertEqual([task.id for task in tasks], ["T01"])
            self.assertFalse(paths.task_dir("T02").exists())

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

    def test_land_help_distinguishes_coordination_force_from_legacy_scope_force(self) -> None:
        self.assertIn("--force                   land before done; in legacy single-repo mode it can include out-of-scope files", land_cmd.HELP)

    def test_land_legacy_single_repo_commits_in_scope_done_task_with_trailer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            (root / "src").mkdir()
            (root / "src" / "feature.txt").write_text("base\n", encoding="utf-8")
            save_tasks(paths, "demo", [Task(id="T01", title="Legacy land", status=TaskStatus.DONE, scope=["src/*"])])
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)
            (root / "src" / "feature.txt").write_text("changed\n", encoding="utf-8")

            with chdir_compat(root):
                self.assertEqual(land_cmd.main(["T01", "--no-push"]), _common.EXIT_OK)

            message = subprocess.run(["git", "show", "-s", "--format=%B", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout
            committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertIn("Wily-Task: T01", message)
            self.assertEqual(committed, ["src/feature.txt"])

    def test_land_blocks_ledger_closure_outside_scope_without_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            (root / "src").mkdir()
            (root / "src" / "feature.txt").write_text("base\n", encoding="utf-8")
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="Previous task", status=TaskStatus.DONE, scope=["legacy/*"]),
                    Task(id="T02", title="Current task", status=TaskStatus.DONE, scope=["src/*"]),
                ],
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)
            before = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()

            (root / "src" / "feature.txt").write_text("changed\n", encoding="utf-8")
            _, tasks = load_tasks(paths)
            tasks[0].scope.append(".wily/tasks/T01/result.md")
            save_tasks(paths, "demo", tasks)
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# T01 result\n\n- finished earlier\n", encoding="utf-8")

            with chdir_compat(root):
                stderr = StringIO()
                with redirect_stderr(stderr):
                    code = land_cmd.main(["T02", "--no-push"])

            after = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(code, _common.EXIT_TRANSITION)
            self.assertEqual(after, before)
            self.assertIn("ledger closure changes detected", stderr.getvalue())
            self.assertIn("--include-ledger-closure", stderr.getvalue())

    def test_land_include_ledger_closure_commits_wily_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git_repo(root)
            paths = WilyPaths(root)
            paths.wily_dir.mkdir()
            (root / "src").mkdir()
            (root / "src" / "feature.txt").write_text("base\n", encoding="utf-8")
            save_tasks(
                paths,
                "demo",
                [
                    Task(id="T01", title="Previous task", status=TaskStatus.DONE, scope=["legacy/*"]),
                    Task(id="T02", title="Current task", status=TaskStatus.DONE, scope=["src/*"]),
                ],
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)

            (root / "src" / "feature.txt").write_text("changed\n", encoding="utf-8")
            _, tasks = load_tasks(paths)
            tasks[0].scope.append(".wily/tasks/T01/result.md")
            save_tasks(paths, "demo", tasks)
            paths.result_md("T01").parent.mkdir(parents=True, exist_ok=True)
            paths.result_md("T01").write_text("# T01 result\n\n- finished earlier\n", encoding="utf-8")

            with chdir_compat(root):
                self.assertEqual(land_cmd.main(["T02", "--include-ledger-closure", "--no-push"]), _common.EXIT_OK)

            committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertIn("src/feature.txt", committed)
            self.assertIn(".wily/tasks.yaml", committed)
            self.assertIn(".wily/tasks/T01/result.md", committed)

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
