from __future__ import annotations

import os
import re
import json
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "wily.py"
LAUNCHER = ROOT / "wily"
ZSH = shutil.which("zsh")
sys.path.insert(0, str(ROOT / "scripts"))
import wily  # noqa: E402
import wily_state_summary  # noqa: E402
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ISOLATED_BOARD_ENV = {
    "WILY_BOARD_USER_CONFIG": str(Path(tempfile.gettempdir()) / "wily-board-test-missing.json")
}


def strip_ansi(value: str) -> str:
    return ANSI_RE.sub("", value)


def isolated_env(**values: str) -> dict[str, str]:
    return {**ISOLATED_BOARD_ENV, **values}


class WatchInputTest(unittest.TestCase):
    def test_keyboard_actions(self) -> None:
        self.assertEqual(wily.watch_action_from_input("d"), "toggle_done")
        self.assertEqual(wily.watch_action_from_input("r"), "refresh")
        self.assertEqual(wily.watch_action_from_input("q"), "quit")
        self.assertEqual(wily.watch_action_from_input("\x03"), "quit")
        self.assertIsNone(wily.watch_action_from_input("x"))

    def test_left_mouse_press_on_body_toggles_done(self) -> None:
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;4M", summary_row=4, body_rows=1),
            "toggle_done",
        )
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;6M", summary_row=4, body_rows=3),
            "toggle_done",
        )

    def test_middle_mouse_press_does_not_toggle_done(self) -> None:
        self.assertIsNone(wily.watch_action_from_input("\x1b[<1;12;4M", summary_row=4, body_rows=1))

    def test_right_mouse_press_opens_tmux_menu_action(self) -> None:
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<2;12;4M", summary_row=4, body_rows=1),
            "tmux_menu",
        )
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<2;12;22M", summary_row=4, body_rows=2, expand_done=True),
            "tmux_menu",
        )

    def test_sgr_mouse_release_or_outside_body_is_ignored(self) -> None:
        self.assertIsNone(wily.watch_action_from_input("\x1b[<0;12;4m", summary_row=4, body_rows=1))
        self.assertIsNone(wily.watch_action_from_input("\x1b[<0;12;8M", summary_row=4, body_rows=2))

    def test_expanded_done_only_left_click_on_body_toggles(self) -> None:
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;4M", summary_row=4, body_rows=2, expand_done=True),
            "toggle_done",
        )
        self.assertIsNone(
            wily.watch_action_from_input("\x1b[<0;12;22M", summary_row=4, body_rows=2, expand_done=True),
        )
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<2;12;4M", summary_row=4, body_rows=2, expand_done=True),
            "tmux_menu",
        )

    def test_mouse_wheel_returns_scroll_actions(self) -> None:
        self.assertEqual(wily.watch_action_from_input("\x1b[<64;12;4M", expand_done=True), "scroll_up")
        self.assertEqual(wily.watch_action_from_input("\x1b[<65;12;4M", expand_done=True), "scroll_down")
        self.assertIsNone(wily.watch_action_from_input("\x1b[<64;12;4M", expand_done=False))


class UsageContractTest(unittest.TestCase):
    def test_live_usage_prefers_v2_canonical_phase_refs(self) -> None:
        self.assertIn("<stage-id>/<phase-id>", wily.heartbeat_usage())
        self.assertIn("[<stage-id>/<phase-id>|item-id]", wily.live_worked_usage())
        self.assertIn("live-worked [<stage-id>/<phase-id>|item-id]", wily.usage())

    def test_parse_sgr_mouse_event_includes_button_code(self) -> None:
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<0;9;12M"), (0, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<2;9;12M"), (2, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<64;9;12M"), (64, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<0;9;12m"), (0, 9, 12, False))
        self.assertIsNone(wily.parse_watch_mouse_event("not mouse"))

    def test_apply_watch_scroll_action_updates_offset(self) -> None:
        self.assertEqual(wily.apply_watch_scroll_action(0, "scroll_down", max_offset=3), 1)
        self.assertEqual(wily.apply_watch_scroll_action(3, "scroll_down", max_offset=3), 3)
        self.assertEqual(wily.apply_watch_scroll_action(2, "scroll_up", max_offset=3), 1)
        self.assertEqual(wily.apply_watch_scroll_action(0, "scroll_up", max_offset=3), 0)
        self.assertEqual(wily.apply_watch_scroll_action(2, "refresh", max_offset=3), 2)

    def test_tmux_context_menu_command_uses_mouse_position(self) -> None:
        command = wily.tmux_context_menu_command(12, 4)
        self.assertEqual(command[:2], ["tmux", "display-menu"])
        self.assertIn("-x", command)
        self.assertIn("12", command)
        self.assertIn("-y", command)
        self.assertIn("4", command)
        self.assertIn("Horizontal Split", command)
        self.assertIn("Vertical Split", command)


class CollaborationPolicyTest(unittest.TestCase):
    def check_ignore(self, path: str) -> int:
        if not (ROOT / ".git").exists():
            self.skipTest("git metadata is not available")
        return subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode

    def test_shared_wily_state_is_trackable_and_sessions_remain_local(self) -> None:
        self.assertEqual(self.check_ignore(".wily/roadmap.yaml"), 1)
        self.assertEqual(self.check_ignore(".wily/project.md"), 1)
        self.assertEqual(self.check_ignore(".wily/phases/08-2-collaborative-wily-state-sync/phase.md"), 1)
        self.assertEqual(self.check_ignore(".wily/revisions/2026-05-14-163046-replan-7.md"), 1)
        self.assertEqual(self.check_ignore(".wily/sessions/example"), 0)


class ReferenceOnlyWorkflowTest(unittest.TestCase):
    def test_custom_workflow_bundle_is_not_part_of_live_plugin(self) -> None:
        self.assertFalse((ROOT / "runners" / "custom-workflow").exists())

    def test_workflow_guidance_routes_to_custom_workflow_skillset(self) -> None:
        workflow = (ROOT / "skills" / "wily-workflow" / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            ROOT / "skills" / "wily-workflow" / "references" / "runner-adapter-contract.md"
        ).read_text(encoding="utf-8")

        combined = workflow + "\n" + reference
        self.assertIn("custom-workflow-skillset:plan-goal-runner", combined)
        self.assertIn("custom-workflow-skillset:parallel-lane-runner", combined)
        self.assertIn("custom-workflow-result.md", combined)
        self.assertNotIn("bundled default runner", combined)
        self.assertNotIn("runners/custom-workflow/runner.yaml", combined)


class WilyCliTest(unittest.TestCase):
    def run_wily(self, project: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, **ISOLATED_BOARD_ENV},
        )

    def run_wily_with_env(
        self,
        project: Path,
        *args: str,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, **ISOLATED_BOARD_ENV, **env},
        )

    def run_launcher(
        self,
        project: Path,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if ZSH is None:
            self.skipTest("zsh is not installed")
        return subprocess.run(
            [ZSH, str(LAUNCHER), *args],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, **ISOLATED_BOARD_ENV, **(env or {})},
        )

    def create_state(self, project: Path) -> Path:
        state = project / ".wily"
        for name in ("phases", "sessions", "revisions"):
            (state / name).mkdir(parents=True, exist_ok=True)
        (state / "project.md").write_text("# Wily Project\n", encoding="utf-8")
        (state / "status.md").write_text("# Wily Status\n", encoding="utf-8")
        (state / "decisions.md").write_text("# Wily Decisions\n", encoding="utf-8")
        return state

    def write_ready_phase(self, project: Path) -> None:
        self.create_state(project)
        phase_dir = project / ".wily" / "phases" / "01-first-phase"
        phase_dir.mkdir(parents=True, exist_ok=True)
        (phase_dir / "phase.md").write_text("# Phase\n\nRoadmap-level phase definition\n", encoding="utf-8")
        (phase_dir / "prompt.md").write_text("Run this phase\n", encoding="utf-8")
        (phase_dir / "verification.md").write_text("python3 -m unittest\n", encoding="utf-8")
        (phase_dir / "handoff.md").write_text("Resume from here\n", encoding="utf-8")
        (phase_dir / "planner.md").write_text(
            "\n".join(
                [
                    "# Planner Adapter",
                    "",
                    "Recommended planner: superpowers:writing-plans",
                    "",
                    "Use this planner to create the implementation plan.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (phase_dir / "plan.md").write_text("", encoding="utf-8")
        (project / ".wily" / "roadmap.yaml").write_text(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'goal: "Ship useful app"',
                    'phases:',
                    '  - id: "01"',
                    '    title: "First phase"',
                    '    path: "phases/01-first-phase"',
                    '    status: "ready"',
                    '    depends_on: []',
                ]
            ),
            encoding="utf-8",
        )

    def write_blocked_dependency_phase(self, project: Path) -> None:
        self.create_state(project)
        phase_dir = project / ".wily" / "phases" / "02-blocked-phase"
        phase_dir.mkdir(parents=True, exist_ok=True)
        for name, content in {
            "phase.md": "# Phase\n\nBlocked by dependency\n",
            "prompt.md": "Run blocked phase\n",
            "verification.md": "python3 -m unittest\n",
            "handoff.md": "Resume from here\n",
            "planner.md": "# Planner Adapter\n\nRecommended planner: superpowers:writing-plans\n",
            "plan.md": "",
        }.items():
            (phase_dir / name).write_text(content, encoding="utf-8")
        (project / ".wily" / "roadmap.yaml").write_text(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'goal: "Ship useful app"',
                    'phases:',
                    '  - id: "01"',
                    '    title: "Unfinished dependency"',
                    '    path: "phases/01-unfinished-dependency"',
                    '    status: "pending"',
                    '    depends_on: []',
                    '',
                    '  - id: "02"',
                    '    title: "Blocked phase"',
                    '    path: "phases/02-blocked-phase"',
                    '    status: "pending"',
                    '    depends_on: ["01"]',
                ]
            ),
            encoding="utf-8",
        )

    def assert_git_ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def init_git_project_with_origin(self, project: Path, remote: Path) -> None:
        self.assert_git_ok(project, "init", "-b", "main")
        self.assert_git_ok(project, "config", "user.email", "wily@example.test")
        self.assert_git_ok(project, "config", "user.name", "Wily Test")
        self.assert_git_ok(project.parent, "init", "--bare", str(remote))
        self.assert_git_ok(project, "add", ".")
        self.assert_git_ok(project, "commit", "-m", "initial")
        self.assert_git_ok(project, "remote", "add", "origin", str(remote))
        self.assert_git_ok(project, "push", "-u", "origin", "main")

    def write_pending_unblocked_phase(self, project: Path) -> None:
        self.create_state(project)
        phase_dir = project / ".wily" / "phases" / "02-unblocked-phase"
        phase_dir.mkdir(parents=True, exist_ok=True)
        for name, content in {
            "phase.md": "# Phase\n\nPending with completed dependency\n",
            "prompt.md": "Run unblocked phase\n",
            "verification.md": "python3 -m unittest\n",
            "handoff.md": "Resume from here\n",
            "planner.md": "# Planner Adapter\n\nRecommended planner: superpowers:writing-plans\n",
            "plan.md": "",
        }.items():
            (phase_dir / name).write_text(content, encoding="utf-8")
        (project / ".wily" / "roadmap.yaml").write_text(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'goal: "Ship useful app"',
                    'phases:',
                    '  - id: "01"',
                    '    title: "Finished dependency"',
                    '    path: "phases/01-finished-dependency"',
                    '    status: "done"',
                    '    depends_on: []',
                    '',
                    '  - id: "02"',
                    '    title: "Unblocked phase"',
                    '    path: "phases/02-unblocked-phase"',
                    '    status: "pending"',
                    '    depends_on: ["01"]',
                ]
            ),
            encoding="utf-8",
        )

    def write_stage_roadmap(self, project: Path) -> None:
        state = self.create_state(project)
        (state / "stages").mkdir(parents=True, exist_ok=True)
        stage_dir = state / "stages" / "s01-mvp0"
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / "stage.md").write_text("# Stage s01-mvp0\n\nMVP 0 loop.\n", encoding="utf-8")
        (stage_dir / "prompt.md").write_text("Run the whole stage directly.\n", encoding="utf-8")
        (stage_dir / "verification.md").write_text("python3 -m unittest\n", encoding="utf-8")
        (stage_dir / "handoff.md").write_text("Start from Stage context.\n", encoding="utf-8")
        (stage_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")
        (state / "roadmap.yaml").write_text(
            "\n".join(
                [
                    'roadmap_version: 2',
                    'goal: "Ship stage-first app"',
                    'stages:',
                    '  - id: "s00-foundation"',
                    '    title: "Foundation"',
                    '    path: "stages/s00-foundation"',
                    '    status: "done"',
                    '    depends_on: []',
                    '    execution_mode: "direct"',
                    '',
                    '  - id: "s01-mvp0"',
                    '    title: "MVP 0 loop"',
                    '    path: "stages/s01-mvp0"',
                    '    status: "pending"',
                    '    depends_on: ["s00-foundation"]',
                    '    execution_mode: "direct"',
                    '    decomposition_status: "none"',
                ]
            ),
            encoding="utf-8",
        )

    def test_init_creates_wily_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily(project, "init", "Ship useful app")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Initialized .wily", result.stdout)
            self.assertTrue((project / ".wily" / "project.md").is_file())
            self.assertTrue((project / ".wily" / "roadmap.yaml").is_file())
            self.assertTrue((project / ".wily" / "status.md").is_file())
            self.assertTrue((project / ".wily" / "decisions.md").is_file())
            self.assertTrue((project / ".wily" / "phases").is_dir())
            self.assertTrue((project / ".wily" / "stages").is_dir())
            self.assertTrue((project / ".wily" / "sessions").is_dir())
            self.assertTrue((project / ".wily" / "revisions").is_dir())
            self.assertIn("Ship useful app", (project / ".wily" / "project.md").read_text(encoding="utf-8"))
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn("stages: []", roadmap)
            self.assertNotIn("phases: []", roadmap)

    def test_init_without_goal_creates_baseline_state_and_reports_goal_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily(project, "init")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Initialized .wily", result.stdout)
            self.assertIn("Goal: needed", result.stdout)
            self.assertIn(
                "Next action: scan the repository, summarize current state, and ask for the intended final outcome.",
                result.stdout,
            )
            self.assertTrue((project / ".wily" / "project.md").is_file())
            self.assertTrue((project / ".wily" / "roadmap.yaml").is_file())
            self.assertTrue((project / ".wily" / "status.md").is_file())
            self.assertTrue((project / ".wily" / "decisions.md").is_file())
            self.assertTrue((project / ".wily" / "stages").is_dir())

    def test_init_in_mature_repo_reports_existing_project_hints_without_goal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "README.md").write_text("# Existing Project\n", encoding="utf-8")
            (project / "scripts").mkdir()
            (project / "scripts" / "build.py").write_text("print('build')\n", encoding="utf-8")
            (project / "tests").mkdir()
            (project / "tests" / "test_existing.py").write_text("def test_existing(): pass\n", encoding="utf-8")

            result = self.run_wily(project, "init")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Initialized .wily", result.stdout)
            self.assertIn("Goal: needed", result.stdout)
            self.assertIn("Existing project hints: README.md, scripts/, tests/", result.stdout)
            self.assertIn("Next action: scan the repository, summarize current state, and ask for the intended final outcome.", result.stdout)
            self.assertTrue((project / ".wily" / "roadmap.yaml").is_file())
            self.assertIn(
                "기존 프로젝트 단서: README.md, scripts/, tests/",
                (project / ".wily" / "project.md").read_text(encoding="utf-8"),
            )

    def test_init_defaults_authoring_files_to_korean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily(project, "init")

            self.assertEqual(result.returncode, 0, result.stderr)
            project_text = (project / ".wily" / "project.md").read_text(encoding="utf-8")
            roadmap_text = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            status_text = (project / ".wily" / "status.md").read_text(encoding="utf-8")
            decisions_text = (project / ".wily" / "decisions.md").read_text(encoding="utf-8")
            self.assertIn("목표: 사용자 목표 필요", project_text)
            self.assertIn('goal: "사용자 목표 필요"', roadmap_text)
            self.assertIn("stages: []", roadmap_text)
            self.assertNotIn("phases: []", roadmap_text)
            self.assertIn("상태가 초기화되었습니다.", status_text)
            self.assertIn("아직 기록된 결정이 없습니다.", decisions_text)

    def test_init_preserves_existing_wily_authoring_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            authored = {
                "project.md": "# Project\n\nUser-authored project notes.\n",
                "roadmap.yaml": 'roadmap_version: 7\ngoal: "Keep this roadmap"\nphases: []\n',
                "status.md": "# Status\n\nUser-authored status.\n",
                "decisions.md": "# Decisions\n\nUser-authored decisions.\n",
            }
            for name, content in authored.items():
                (state / name).write_text(content, encoding="utf-8")

            result = self.run_wily(project, "init", "Replacement goal")

            self.assertEqual(result.returncode, 0, result.stderr)
            for name, content in authored.items():
                self.assertEqual((state / name).read_text(encoding="utf-8"), content)
            self.assertIn(
                "Preserved existing .wily files: decisions.md, project.md, roadmap.yaml, status.md",
                result.stdout,
            )

    def test_init_repairs_required_directories_for_partial_wily_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "project.md").write_text("# Existing Project\n", encoding="utf-8")

            result = self.run_wily(project, "init", "Ship useful app")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((state / "phases").is_dir())
            self.assertTrue((state / "stages").is_dir())
            self.assertTrue((state / "sessions").is_dir())
            self.assertTrue((state / "revisions").is_dir())
            self.assertEqual((state / "project.md").read_text(encoding="utf-8"), "# Existing Project\n")

    def test_status_uses_polished_roadmap_pane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Ship useful app"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                        '    parallel_group: null',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "status")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("v1", result.stdout)
            self.assertIn("0/1", result.stdout)
            self.assertIn("First phase", result.stdout)
            self.assertNotIn("로드맵 버전:", result.stdout)
            self.assertNotIn("Roadmap:", result.stdout)
            self.assertNotIn("Phase 흐름:", result.stdout)

    def test_watch_prints_polished_pane_preview_once_with_once_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("v1", result.stdout)
            self.assertIn("0/1", result.stdout)
            self.assertIn("0%", result.stdout)
            self.assertIn("> 01  First phase", result.stdout)
            self.assertIn("git:", result.stdout)
            self.assertNotIn("Phase 흐름:", result.stdout)
            self.assertNotIn("Repo: ", result.stdout)

    def test_next_recommends_ready_stage_without_decomposing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next stage: s01-mvp0 - MVP 0 loop", result.stdout)
            self.assertIn("Stage path:", result.stdout)
            self.assertNotIn("Phase path:", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('decomposition_status: "none"', roadmap)

    def test_next_lists_parallel_ready_stage_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'stages:',
                        '  - id: "s00-foundation"',
                        '    title: "Foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    path: "stages/s00-foundation"',
                        '',
                        '  - id: "s01-server"',
                        '    title: "Server work"',
                        '    status: "pending"',
                        '    owner: "wily"',
                        '    depends_on: ["s00-foundation"]',
                        '    path: "stages/s01-server"',
                        '    write_scope: ["src/server"]',
                        '',
                        '  - id: "s02-client"',
                        '    title: "Client work"',
                        '    status: "pending"',
                        '    owner: "right"',
                        '    depends_on: ["s00-foundation"]',
                        '    path: "stages/s02-client"',
                        '    write_scope: ["src/client"]',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ready stage candidates:", result.stdout)
            self.assertIn("- s01-server @wily", result.stdout)
            self.assertIn("- s02-client @right", result.stdout)
            self.assertIn("Parallel-safe: write_scope does not overlap", result.stdout)

    def test_next_reports_active_stage_local_phase_when_no_stage_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            stage_dir = state / "stages" / "s14"
            stage_dir.mkdir(parents=True)
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 14',
                        'stages:',
                        '  - id: "s13"',
                        '    title: "Parser hardening"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    path: "stages/s13"',
                        '',
                        '  - id: "s14"',
                        '    title: "Stage and mobile watch"',
                        '    status: "in_progress"',
                        '    depends_on: ["s13"]',
                        '    path: "stages/s14"',
                        '    current_session: "sessions/active-stage"',
                    ]
                ),
                encoding="utf-8",
            )
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s14"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "14-1"',
                        '    title: "Stage hierarchy"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "14-2"',
                        '    title: "Mobile watch layout"',
                        '    status: "in_progress"',
                        '    depends_on: ["14-1"]',
                        '    current_session: "sessions/active-phase"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Active stage: s14 - Stage and mobile watch", result.stdout)
            self.assertIn("Active phase: 14-2 - Mobile watch layout", result.stdout)
            self.assertIn("Session: sessions/active-phase", result.stdout)

    def test_next_reports_ready_child_phase_for_active_decomposed_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            stage_dir = state / "stages" / "s22"
            stage_dir.mkdir(parents=True)
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s20"',
                        '    title: "Done prerequisite"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    path: "stages/s20"',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    status: "in_progress"',
                        '    depends_on: ["s20"]',
                        '    path: "stages/s22"',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                        '    current_session: "sessions/old-phase"',
                    ]
                ),
                encoding="utf-8",
            )
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s22"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "22-1"',
                        '    title: "Done guardrail"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "22-2"',
                        '    title: "Surface verification"',
                        '    status: "pending"',
                        '    depends_on: ["22-1"]',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Active stage: s22 - Realtime activity heartbeat", result.stdout)
            self.assertIn("Next phase: 22-2 - Surface verification", result.stdout)

    def test_start_stage_creates_stage_session_without_child_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)

            result = self.run_wily(project, "start", "s01-mvp0")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Started stage s01-mvp0", result.stdout)
            session = next((project / ".wily" / "sessions").glob("*stage-s01-mvp0-attempt-1"))
            self.assertTrue((session / "input.md").is_file())
            self.assertIn("Stage: s01-mvp0 - MVP 0 loop", (session / "input.md").read_text(encoding="utf-8"))
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('id: "s01-mvp0"', roadmap)
            self.assertIn('status: "in_progress"', roadmap)
            self.assertNotIn('phases:', roadmap)

    def test_decompose_stage_dry_run_does_not_mutate_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            before = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")

            result = self.run_wily(project, "decompose-stage", "s01-mvp0", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Stage decomposition proposal: s01-mvp0", result.stdout)
            self.assertIn("parallel lanes", result.stdout)
            self.assertEqual((project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8"), before)

    def test_decompose_stage_apply_fixture_records_phase_and_parallel_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)

            result = self.run_wily(project, "decompose-stage", "s01-mvp0", "--apply-fixture")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Decomposed stage s01-mvp0", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('execution_mode: "decomposed"', roadmap)
            self.assertIn('decomposition_status: "applied"', roadmap)
            self.assertNotIn('id: "s01-mvp0-p01"', roadmap)
            self.assertNotIn('lanes:', roadmap)
            stage_state = project / ".wily" / "stages" / "s01-mvp0" / "stage.yaml"
            self.assertTrue(stage_state.is_file())
            stage_text = stage_state.read_text(encoding="utf-8")
            self.assertIn('id: "s01-mvp0-p01"', stage_text)
            self.assertIn('lanes:', stage_text)
            self.assertIn('write_scope: ["src/server"]', stage_text)
            self.assertTrue((project / ".wily" / "stages" / "s01-mvp0" / "phases" / "s01-mvp0-p01" / "phase.md").is_file())

    def test_migrate_state_dry_run_reports_v2_changes_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "mixed-legacy", project)
            roadmap_path = project / ".wily" / "roadmap.yaml"
            before = roadmap_path.read_text(encoding="utf-8")

            result = self.run_wily(project, "migrate-state", "--to", "wily-roadmap-v2", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Migration mode: dry-run", result.stdout)
            self.assertIn("Target schema: wily-roadmap-v2", result.stdout)
            self.assertIn("Would write backup:", result.stdout)
            self.assertIn("Would write reports:", result.stdout)
            self.assertIn("s02/p01 <- legacy-refactor", result.stdout)
            self.assertEqual(roadmap_path.read_text(encoding="utf-8"), before)
            self.assertFalse((project / ".wily" / "backups").exists())
            self.assertFalse((project / ".wily" / "migrations").exists())

    def test_migrate_state_apply_writes_v2_stage_local_phases_backup_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "mixed-legacy", project)

            result = self.run_wily(project, "migrate-state", "--to", "wily-roadmap-v2", "--apply")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Migration mode: apply", result.stdout)
            self.assertIn("Migration applied.", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('roadmap_schema: "wily-roadmap-v2"', roadmap)
            self.assertIn('stages:', roadmap)
            self.assertNotIn("\nphases:", roadmap)
            stage_state = (project / ".wily" / "stages" / "s02-refactor" / "stage.yaml").read_text(encoding="utf-8")
            self.assertIn('schema: "wily-roadmap-v2"', stage_state)
            self.assertIn('id: "p01"', stage_state)
            self.assertIn('title: "Legacy refactor"', stage_state)
            self.assertIn('depends_on: ["s01/p01"]', stage_state)
            self.assertTrue((project / ".wily" / "phases" / "legacy-refactor").exists())
            self.assertTrue(any((project / ".wily" / "backups").glob("*-wily-roadmap-v2")))
            report_json = next((project / ".wily" / "migrations").glob("*-wily-roadmap-v2.json"))
            report = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertEqual(report["target_schema"], "wily-roadmap-v2")
            self.assertEqual(report["phase_mappings"]["legacy-refactor"], "s02/p01")
            self.assertEqual(report["mode"], "apply")

    def test_v2_start_rejects_stage_id_with_next_phase_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "already-v2", project)

            result = self.run_wily(project, "start", "s02")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Stage is not executable: s02", result.stderr)
            self.assertIn("Next phase: s02/p01", result.stderr)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "ready"', roadmap)

    def test_v2_start_accepts_namespaced_stage_local_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "already-v2", project)

            result = self.run_wily(project, "start", "s02/p01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Started phase s02/p01", result.stdout)
            stage_state = (project / ".wily" / "stages" / "s02-refactor" / "stage.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', stage_state)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('id: "s02"', roadmap)
            self.assertIn('status: "in_progress"', roadmap)

    def test_v2_next_reports_next_stage_and_executable_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "already-v2", project)
            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next stage: s02 - Refactor", result.stdout)
            self.assertIn("Next phase: s02/p01 - Refactor", result.stdout)
            self.assertIn("Phase path:", result.stdout)

    def test_decompose_stage_from_json_records_user_authored_decomposition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps(
                    [
                        {
                            "id": "s01-custom",
                            "title": "Custom user-authored phase",
                            "status": "pending",
                            "depends_on": [],
                            "lanes": [
                                {
                                    "id": "api-lane",
                                    "title": "API work",
                                    "write_scope": ["src/api"],
                                }
                            ],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "decompose-stage", "s01-mvp0", "--from-json", str(proposal))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Decomposed stage s01-mvp0", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertNotIn('id: "s01-custom"', roadmap)
            self.assertNotIn('id: "api-lane"', roadmap)
            stage_text = (project / ".wily" / "stages" / "s01-mvp0" / "stage.yaml").read_text(encoding="utf-8")
            self.assertIn('id: "s01-custom"', stage_text)
            self.assertIn('title: "Custom user-authored phase"', stage_text)
            self.assertIn('id: "api-lane"', stage_text)
            self.assertIn('write_scope: ["src/api"]', stage_text)

    def test_decompose_stage_from_json_emits_board_live_draft_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps(
                    [
                        {
                            "id": "s01-custom",
                            "title": "Custom user-authored phase",
                            "status": "pending",
                            "depends_on": [],
                            "owner": "codex",
                            "task": "split the work",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            emitted: list[tuple[dict, str, str, str]] = []

            def record_event(root: Path, item: dict, event: str, live_status: str, note: str = "") -> bool:
                emitted.append((item, event, live_status, note))
                return True

            stdout = io.StringIO()
            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                    "WILY_BOARD_AGENT": "codex",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event), patch("sys.stdout", stdout):
                result = wily.command_decompose_stage(project, ["s01-mvp0", "--from-json", str(proposal)])

            self.assertEqual(result, 0)
            self.assertEqual(len(emitted), 1)
            payload, event, live_status, note = emitted[0]
            self.assertEqual(event, "stage_decomposed_local")
            self.assertEqual(live_status, "active")
            self.assertEqual(note, "")
            self.assertEqual(payload["draft_kind"], "stage_decomposition")
            self.assertEqual(payload["item_type"], "stage")
            self.assertEqual(payload["item_id"], "s01-mvp0")
            self.assertEqual(payload["stage_id"], "s01-mvp0")
            self.assertEqual(payload["agent"], "codex")
            self.assertEqual(payload["phases"][0]["id"], "s01-custom")
            self.assertEqual(payload["phases"][0]["task"], "split the work")
            self.assertIn("Board live draft sent for s01-mvp0: 1 phases", stdout.getvalue())

    def test_decompose_stage_from_json_warns_when_board_live_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps([{"id": "s01-custom", "title": "Custom user-authored phase"}]),
                encoding="utf-8",
            )
            stderr = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stderr", stderr), patch.object(
                wily, "emit_board_live_event"
            ) as emit:
                result = wily.command_decompose_stage(project, ["s01-mvp0", "--from-json", str(proposal)])

            self.assertEqual(result, 0)
            emit.assert_not_called()
            self.assertIn("Board live draft not sent: missing Wily Board live config", stderr.getvalue())

    def test_decompose_stage_from_json_warns_when_board_live_draft_send_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps([{"id": "s01-custom", "title": "Custom user-authored phase"}]),
                encoding="utf-8",
            )
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", return_value=False), patch("sys.stderr", stderr):
                result = wily.command_decompose_stage(project, ["s01-mvp0", "--from-json", str(proposal)])

            self.assertEqual(result, 0)
            self.assertIn("Board live draft failed for s01-mvp0", stderr.getvalue())
            self.assertIn("wily board sync-local s01-mvp0", stderr.getvalue())
            self.assertIn("actual-site verification remains incomplete", stderr.getvalue())

    def test_board_sync_local_replays_existing_decomposed_stage_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps(
                    [
                        {
                            "id": "s01-custom",
                            "title": "Custom user-authored phase",
                            "status": "pending",
                            "depends_on": [],
                            "owner": "codex",
                            "task": "split the work",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"WILY_BOARD_USER_CONFIG": str(project / "missing-board.json")}, clear=True):
                self.assertEqual(wily.command_decompose_stage(project, ["s01-mvp0", "--from-json", str(proposal)]), 0)

            emitted: list[tuple[dict, str, str, str]] = []

            def record_event(root: Path, item: dict, event: str, live_status: str, note: str = "") -> tuple[bool, str]:
                emitted.append((item, event, live_status, note))
                return True, ""

            stdout = io.StringIO()
            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                    "WILY_BOARD_AGENT": "codex",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event), patch("sys.stdout", stdout):
                result = wily.command_board(project, ["sync-local", "s01-mvp0"])

            self.assertEqual(result, 0)
            self.assertEqual(len(emitted), 1)
            payload, event, live_status, note = emitted[0]
            self.assertEqual(event, "stage_decomposed_local")
            self.assertEqual(live_status, "active")
            self.assertEqual(note, "")
            self.assertEqual(payload["stage_id"], "s01-mvp0")
            self.assertEqual(payload["title"], "MVP 0 loop")
            self.assertEqual(payload["status"], "pending")
            self.assertEqual(payload["depends_on"], ["s00-foundation"])
            self.assertEqual(payload["execution_mode"], "decomposed")
            self.assertEqual(payload["raw_path"], "stages/s01-mvp0")
            self.assertEqual(payload["position"], 2)
            self.assertEqual(payload["phases"][0]["id"], "s01-custom")
            self.assertIn("Board local draft synced for s01-mvp0: 1 phases", stdout.getvalue())

    def test_decompose_stage_from_json_rejects_empty_decomposition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text("[]", encoding="utf-8")

            result = self.run_wily(project, "decompose-stage", "s01-mvp0", "--from-json", str(proposal))

            self.assertEqual(result.returncode, 1)
            self.assertIn("Invalid decomposition JSON: expected at least one phase.", result.stderr)
            self.assertFalse((project / ".wily" / "stages" / "s01-mvp0" / "stage.yaml").exists())

    def test_decompose_stage_from_json_reports_board_http_failure_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            proposal = project / "decomposition.json"
            proposal.write_text(
                json.dumps([{"id": "s01-custom", "title": "Custom user-authored phase"}]),
                encoding="utf-8",
            )
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", return_value=(False, "HTTP 401")), patch("sys.stderr", stderr):
                result = wily.command_decompose_stage(project, ["s01-mvp0", "--from-json", str(proposal)])

            self.assertEqual(result, 0)
            self.assertIn("Board live draft failed for s01-mvp0", stderr.getvalue())
            self.assertIn("HTTP 401", stderr.getvalue())

    def test_status_reads_decomposed_phase_counts_from_stage_local_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_stage_roadmap(project)
            run = self.run_wily(project, "decompose-stage", "s01-mvp0", "--apply-fixture")
            self.assertEqual(run.returncode, 0, run.stderr)

            result = self.run_wily(project, "status")

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("MVP 0 loop", out)
            self.assertIn("2 phases", out)

    def test_watch_stage_mode_renders_stage_header_from_stage_id_not_dependency_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            stage_dir = state / "stages" / "s22"
            stage_dir.mkdir(parents=True)
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s22"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "22-1"',
                        '    title: "Watch contract"',
                        '    status: "pending"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s16"',
                        '    title: "Live overlay"',
                        '    path: "stages/s16"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "s17"',
                        '    title: "Heartbeat freshness"',
                        '    path: "stages/s17"',
                        '    status: "done"',
                        '    depends_on: ["s16"]',
                        '  - id: "s18"',
                        '    title: "Collaboration ops"',
                        '    path: "stages/s18"',
                        '    status: "done"',
                        '    depends_on: ["s17"]',
                        '  - id: "s19"',
                        '    title: "Risk view"',
                        '    path: "stages/s19"',
                        '    status: "done"',
                        '    depends_on: ["s18"]',
                        '  - id: "s20"',
                        '    title: "Personal visibility"',
                        '    path: "stages/s20"',
                        '    status: "done"',
                        '    depends_on: ["s16"]',
                        '  - id: "s21"',
                        '    title: "UI redesign"',
                        '    path: "stages/s21"',
                        '    status: "pending"',
                        '    depends_on: ["s22"]',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    path: "stages/s22"',
                        '    status: "ready"',
                        '    depends_on: ["s20"]',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                "--show-done",
                env={"COLUMNS": "110", "LINES": "80"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("Stage 22", out)
            self.assertIn("> s22  Realtime activity heartbeat", out)
            self.assertIn("22-1  Watch contract", out)
            stage_18_index = out.index("Stage 18")
            stage_22_index = out.index("Stage 22")
            self.assertGreater(stage_22_index, stage_18_index)

    def test_next_reports_first_child_phase_for_ready_decomposed_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            stage_dir = state / "stages" / "s22"
            stage_dir.mkdir(parents=True)
            (stage_dir / "stage.md").write_text("# Stage\n\nRealtime work\n", encoding="utf-8")
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s22"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "22-1"',
                        '    title: "Watch contract"',
                        '    status: "pending"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s20"',
                        '    title: "Done prerequisite"',
                        '    path: "stages/s20"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    path: "stages/s22"',
                        '    status: "ready"',
                        '    depends_on: ["s20"]',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next stage: s22 - Realtime activity heartbeat", result.stdout)
            self.assertIn("Next phase: 22-1 - Watch contract", result.stdout)

    def test_compact_status_keeps_frontier_stage_header_in_stage_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            for index in range(1, 22):
                stage_id = f"s{index:02d}"
                stage_dir = state / "stages" / stage_id
                stage_dir.mkdir(parents=True)
                (stage_dir / "stage.yaml").write_text(
                    "\n".join(
                        [
                            f'stage_id: "{stage_id}"',
                            'execution_mode: "decomposed"',
                            'decomposition_status: "applied"',
                            'phases:',
                            f'  - id: "{index:02d}-1"',
                            f'    title: "Done phase {index}"',
                            '    status: "done"',
                            '    depends_on: []',
                        ]
                    ),
                    encoding="utf-8",
                )
            (state / "stages" / "s14" / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s14"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "14-1"',
                        '    title: "Done child"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "14-2"',
                        '    title: "Superseded child"',
                        '    status: "superseded"',
                        '    depends_on: ["14-1"]',
                    ]
                ),
                encoding="utf-8",
            )
            stage_dir = state / "stages" / "s22"
            stage_dir.mkdir(parents=True)
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s22"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "22-1"',
                        '    title: "Watch contract"',
                        '    status: "pending"',
                        '    depends_on: []',
                        '  - id: "22-2"',
                        '    title: "Next work"',
                        '    status: "pending"',
                        '    depends_on: ["22-1"]',
                    ]
                ),
                encoding="utf-8",
            )
            roadmap_lines = ['roadmap_version: 22', 'stages:']
            for index in range(1, 22):
                stage_id = f"s{index:02d}"
                roadmap_lines.extend(
                    [
                        f'  - id: "{stage_id}"',
                        f'    title: "Done stage {index}"',
                        f'    path: "stages/{stage_id}"',
                        '    status: "done"',
                        f'    depends_on: {f"[\\\"s{index - 1:02d}\\\"]" if index > 1 else "[]"}',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                    ]
                )
            roadmap_lines.extend(
                [
                    '  - id: "s22"',
                    '    title: "Realtime activity heartbeat"',
                    '    path: "stages/s22"',
                    '    status: "ready"',
                    '    depends_on: ["s21"]',
                    '    execution_mode: "decomposed"',
                    '    decomposition_status: "applied"',
                ]
            )
            (state / "roadmap.yaml").write_text("\n".join(roadmap_lines), encoding="utf-8")

            result = self.run_wily_with_env(
                project,
                "status",
                env={"COLUMNS": "80", "LINES": "24"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("Stage 22", out)
            self.assertIn("22-1  Watch contract", out)

    def test_watch_flags_ready_decomposed_stage_with_missing_child_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s20"',
                        '    title: "Done prerequisite"',
                        '    path: "stages/s20"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    path: "stages/s22"',
                        '    status: "ready"',
                        '    depends_on: ["s20"]',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "100", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("missing child phases", out)

    def test_watch_renders_local_live_registry_chip_without_changing_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            stage_dir = state / "stages" / "s22"
            stage_dir.mkdir(parents=True)
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s22"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "22-4"',
                        '    title: "Board and Watch live rendering"',
                        '    status: "pending"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    path: "stages/s22"',
                        '    status: "ready"',
                        '    depends_on: []',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                    ]
                ),
                encoding="utf-8",
            )
            active_dir = state / "local" / "live" / "active"
            active_dir.mkdir(parents=True)
            now = datetime.now(timezone.utc).isoformat()
            (active_dir / "session-1.json").write_text(
                json.dumps(
                    {
                        "item_type": "phase",
                        "item_id": "22-4",
                        "phase_id": "22-4",
                        "stage_id": "s22",
                        "actor": "airmang",
                        "agent": "codex",
                        "live_status": "active",
                        "last_seen_at": now,
                        "last_worked_at": now,
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "120", "LINES": "40"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("0/1 - 0%", out)
            self.assertIn("22-4  Board and Watch live rendering", out)
            self.assertIn("codex working", out)

    def test_watch_renders_local_only_live_item_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 22',
                        'stages:',
                        '  - id: "s22"',
                        '    title: "Realtime activity heartbeat"',
                        '    path: "stages/s22"',
                        '    status: "pending"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )
            active_dir = state / "local" / "live" / "active"
            active_dir.mkdir(parents=True)
            now = datetime.now(timezone.utc)
            (active_dir / "session-2.json").write_text(
                json.dumps(
                    {
                        "item_type": "phase",
                        "item_id": "22-local",
                        "phase_id": "22-local",
                        "stage_id": "s22",
                        "actor": "airmang",
                        "agent": "claude",
                        "live_status": "active",
                        "last_seen_at": now.isoformat(),
                        "last_worked_at": (now - timedelta(minutes=5)).isoformat(),
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "120", "LINES": "40"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            out = strip_ansi(result.stdout)
            self.assertIn("Local activity", out)
            self.assertIn("22-local", out)
            self.assertIn("claude active", out)

    def test_complete_stage_local_child_phase_updates_stage_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = self.create_state(project)
            session = state / "sessions" / "2026-05-15-000000-phase-p02-attempt-1"
            session.mkdir(parents=True)
            (session / "status.yaml").write_text('phase: "p02"\nattempt: 1\nstatus: "started"\n', encoding="utf-8")
            stage_dir = state / "stages" / "s01"
            stage_dir.mkdir(parents=True)
            (stage_dir / "stage.yaml").write_text(
                "\n".join(
                    [
                        'stage_id: "s01"',
                        'execution_mode: "decomposed"',
                        'decomposition_status: "applied"',
                        'phases:',
                        '  - id: "p01"',
                        '    title: "Done child"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "p02"',
                        '    title: "Current child"',
                        '    status: "in_progress"',
                        '    depends_on: ["p01"]',
                        '    current_session: "sessions/2026-05-15-000000-phase-p02-attempt-1"',
                    ]
                ),
                encoding="utf-8",
            )
            (state / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'stages:',
                        '  - id: "s01"',
                        '    title: "Parent stage"',
                        '    path: "stages/s01"',
                        '    status: "in_progress"',
                        '    depends_on: []',
                        '    execution_mode: "decomposed"',
                        '    decomposition_status: "applied"',
                        '    current_session: "sessions/2026-05-15-000000-phase-p02-attempt-1"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "complete", "p02")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Completed phase p02", result.stdout)
            self.assertIn('status: "done"', (stage_dir / "stage.yaml").read_text(encoding="utf-8"))
            self.assertIn('status: "done"', (state / "roadmap.yaml").read_text(encoding="utf-8"))
            self.assertIn('status: "verified"', (session / "status.yaml").read_text(encoding="utf-8"))

    def test_run_creates_custom_workflow_skillset_request_without_bundled_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "run", "01", "--runner", "custom-workflow")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Prepared phase 01 for Custom Workflow Skillset", result.stdout)
            self.assertIn("Workflow engine: custom-workflow-skillset", result.stdout)
            self.assertIn("Custom Workflow request:", result.stdout)
            self.assertIn("Result target:", result.stdout)
            self.assertIn("Native goal command:", result.stdout)
            self.assertIn("custom-workflow-skillset:plan-goal-runner", result.stdout)
            self.assertIn("/goal Execute Wily phase 01", result.stdout)

            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', roadmap)
            self.assertNotIn('status: "done"', roadmap)
            session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            status = (session / "status.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "started"', status)
            self.assertIn('workflow_engine: "custom-workflow-skillset"', status)
            self.assertFalse((session / "runner").exists())
            request = session / "custom-workflow-request.md"
            result_target = session / "custom-workflow-result.md"
            external_request = project / "agent-handoffs" / "01-first-phase-custom-workflow-request.md"
            external_result = project / "agent-handoffs" / "01-first-phase-custom-workflow-result.md"
            self.assertTrue(request.is_file())
            self.assertTrue(result_target.is_file())
            self.assertTrue(external_request.is_file())
            self.assertTrue(external_result.is_file())
            request_text = request.read_text(encoding="utf-8")
            self.assertIn("custom-workflow-skillset:plan-goal-runner", request_text)
            self.assertIn("custom-workflow-skillset:parallel-lane-runner", request_text)
            self.assertIn("custom-workflow-result.md", request_text)
            self.assertIn("$wily-complete <stage-id>/<phase-id>", request_text)
            self.assertIn("$wily-block <stage-id>/<phase-id>", request_text)
            self.assertNotIn("$wily-complete <phase-id>", request_text)
            self.assertNotIn("$wily-block <phase-id>", request_text)

    def test_run_dry_run_resolves_v2_stage_local_phase_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "already-v2", project)
            before = (project / ".wily" / "stages" / "s02-refactor" / "stage.yaml").read_text(encoding="utf-8")

            result = self.run_wily(project, "run", "s02/p01", "--runner", "custom-workflow", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry run: phase s02/p01 is executable", result.stdout)
            self.assertIn("Workflow engine: custom-workflow-skillset", result.stdout)
            self.assertIn("custom-workflow-skillset:plan-goal-runner", result.stdout)
            self.assertEqual((project / ".wily" / "stages" / "s02-refactor" / "stage.yaml").read_text(encoding="utf-8"), before)
            self.assertFalse((project / ".wily" / "sessions").exists())
            self.assertFalse((project / "agent-handoffs").exists())

    def test_run_keeps_runner_and_autonomy_flags_as_external_workflow_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "run", "01", "--runner", "custom-workflow", "--autonomy", "conservative")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Workflow engine: custom-workflow-skillset", result.stdout)
            self.assertIn("Autonomy: conservative", result.stdout)
            session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            request = (session / "custom-workflow-request.md").read_text(encoding="utf-8")
            self.assertIn("- Workflow engine: `custom-workflow-skillset`", request)
            self.assertIn("- Runner alias: `custom-workflow`", request)
            self.assertIn("- Autonomy mode: `conservative`", request)

    def test_run_rejects_non_executable_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_blocked_dependency_phase(project)

            result = self.run_wily(project, "run", "02")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Phase is not executable: 02", result.stderr)
            self.assertFalse((project / "agent-handoffs").exists())

    def test_run_dispatches_pending_phase_when_dependencies_are_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_pending_unblocked_phase(project)

            result = self.run_wily(project, "run", "02")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Prepared phase 02 for Custom Workflow Skillset", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('id: "02"', roadmap)
            self.assertIn('status: "in_progress"', roadmap)
            self.assertTrue((project / "agent-handoffs" / "02-unblocked-phase-custom-workflow-request.md").is_file())

    def test_run_attaches_existing_in_progress_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")

            result = self.run_wily(project, "run", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list((project / ".wily" / "sessions").glob("*phase-01-attempt-*"))), 1)
            self.assertIn("Prepared phase 01 for Custom Workflow Skillset", result.stdout)

    def test_complete_snapshots_custom_workflow_result_into_session_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            run = self.run_wily(project, "run", "01")
            self.assertEqual(run.returncode, 0, run.stderr)
            session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            external_result = project / "agent-handoffs" / "01-first-phase-custom-workflow-result.md"
            external_result.write_text(
                "\n".join(
                    [
                        "# Custom Workflow Result",
                        "",
                        "Recommended Wily status: done",
                        "",
                        "Verification: python3 -m unittest passed.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "complete", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Completed phase 01", result.stdout)
            self.assertIn("Recommended Wily status: done", (session / "result.md").read_text(encoding="utf-8"))
            self.assertIn("python3 -m unittest passed", (session / "custom-workflow-result.md").read_text(encoding="utf-8"))

    def test_complete_ignores_pending_custom_workflow_result_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            run = self.run_wily(project, "run", "01")
            self.assertEqual(run.returncode, 0, run.stderr)
            session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))

            result = self.run_wily(project, "complete", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual("# Result\n\nPending.\n", (session / "result.md").read_text(encoding="utf-8"))

    def test_watch_ascii_ui_does_not_print_rich_install_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text("roadmap_version: 1\nphases: []\n", encoding="utf-8")

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("no phases yet", result.stdout)
            self.assertNotIn("Rich UI is not installed", result.stdout)

    def test_repo_launcher_status_delegates_from_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Launcher smoke"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Launcher phase"',
                        '    path: "phases/01-launcher-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_launcher(project, "status", env={"COLUMNS": "80", "LINES": "30"})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("Launcher phase", result.stdout)
            self.assertNotIn(str(ROOT / ".wily"), result.stdout)

    def test_repo_launcher_watch_passes_arguments_to_wily_py(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Watch through launcher"',
                        '    path: "phases/01-watch-through-launcher"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_launcher(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("Watch through launcher", result.stdout)
            self.assertNotIn("Rich UI is not installed", result.stdout)

    def test_repo_launcher_is_zsh_and_local_first(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("#!/usr/bin/env zsh"))
        self.assertIn('exec python3 "$repo_root/scripts/wily.py" "$@"', text)
        for forbidden in ("git push", "gh pr", ".zshrc", ".zprofile", "curl ", "rm -rf"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_watch_rich_ui_uses_thin_dashboard_not_panels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                "--ui",
                "rich",
                env={"COLUMNS": "80", "LINES": "30", "WILY_FORCE_NO_RICH": ""},
            )

            if "Rich UI is not installed." in result.stdout:
                self.skipTest("Rich is not installed")
            self.assertEqual(result.returncode, 0, result.stderr)
            plain = strip_ansi(result.stdout)
            self.assertIn("Wily Roadmap", plain)
            self.assertIn("v1", plain)
            self.assertIn("0/1", plain)
            self.assertIn("First phase", plain)
            self.assertNotIn("╭", plain)
            self.assertNotIn("┏", plain)

    def test_watch_auto_ui_prints_rich_install_hint_when_rich_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text("roadmap_version: 1\nphases: []\n", encoding="utf-8")

            result = self.run_wily_with_env(
                project,
                "watch",
                "--once",
                env={"WILY_FORCE_NO_RICH": "1"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Rich UI is not installed.", result.stdout)
            self.assertIn("$wily-watch --install-ui", result.stdout)
            self.assertIn("Fallback: using ASCII watch UI.", result.stdout)

    def test_watch_install_ui_dry_run_prints_pip_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily(project, "watch", "--install-ui", "--dry-run-install")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("-m venv", result.stdout)
            self.assertIn(".venv-watch", result.stdout)
            self.assertIn("-m pip install -r", result.stdout)
            self.assertIn("requirements-watch.txt", result.stdout)

    def test_watch_defaults_to_here_mode_outside_tmux_interactive(self) -> None:
        self.assertEqual(
            wily.watch_launch_mode([], in_tmux=False, stdin_tty=True, stdout_tty=True),
            "here",
        )
        self.assertEqual(
            wily.watch_launch_mode([], in_tmux=True, stdin_tty=True, stdout_tty=True),
            "pane",
        )
        self.assertEqual(
            wily.watch_launch_mode(["--here"], in_tmux=True, stdin_tty=True, stdout_tty=True),
            "here",
        )

    def test_watch_without_tty_outside_tmux_reports_side_terminal_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily_with_env(project, "watch", env={"TMUX": ""})

            self.assertEqual(result.returncode, 1)
            self.assertIn("interactive terminal", result.stderr)
            self.assertIn("./wily watch", result.stderr)
            self.assertIn("Codex app", result.stderr)

    def test_watch_pane_mode_builds_tmux_split_command_when_inside_tmux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily_with_env(
                project,
                "watch",
                "--dry-run-pane",
                env={"TMUX": "/tmp/tmux", "TMUX_PANE": ""},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("tmux split-window -h", result.stdout)
            self.assertIn("watch --here", result.stdout)

    def test_watch_pane_mode_targets_current_tmux_pane_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily_with_env(
                project,
                "watch",
                "--dry-run-pane",
                env={"TMUX": "/tmp/tmux", "TMUX_PANE": "%42"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("tmux split-window -t %42 -h", result.stdout)
            self.assertIn("watch --here", result.stdout)

    def test_next_prints_ready_phase_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            phase_dir = project / ".wily" / "phases" / "01-first-phase"
            phase_dir.mkdir(parents=True)
            (phase_dir / "phase.md").write_text("# Phase\n\nPurpose text\n", encoding="utf-8")
            (phase_dir / "plan.md").write_text("# Plan\n\nStep text\n", encoding="utf-8")
            (phase_dir / "prompt.md").write_text("Run this phase\n", encoding="utf-8")
            (phase_dir / "verification.md").write_text("python3 -m unittest\n", encoding="utf-8")
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "First phase"',
                        '    path: "phases/01-first-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next phase: 01 - First phase", result.stdout)
            self.assertIn("## Phase", result.stdout)
            self.assertIn("Purpose text", result.stdout)
            self.assertIn("## Existing Implementation Plan", result.stdout)
            self.assertIn("Step text", result.stdout)
            self.assertIn("## Prompt", result.stdout)
            self.assertIn("Run this phase", result.stdout)
            self.assertIn("## Verification", result.stdout)
            self.assertIn("python3 -m unittest", result.stdout)

    def test_next_prints_planner_handoff_and_optional_plan_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## Planner Adapter", result.stdout)
            self.assertIn("Recommended planner: superpowers:writing-plans", result.stdout)
            self.assertIn("## Handoff", result.stdout)
            self.assertIn("Resume from here", result.stdout)
            self.assertIn("## Existing Implementation Plan", result.stdout)
            self.assertIn("No implementation plan exists yet.", result.stdout)

    def test_next_prints_pending_phase_when_dependencies_are_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            phase_dir = project / ".wily" / "phases" / "02-next-layer"
            phase_dir.mkdir(parents=True)
            (phase_dir / "phase.md").write_text("# Phase\n\nPending but unblocked\n", encoding="utf-8")
            (phase_dir / "prompt.md").write_text("Run next layer\n", encoding="utf-8")
            (phase_dir / "verification.md").write_text("python3 -m unittest\n", encoding="utf-8")
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Finished foundation"',
                        '    path: "phases/01-finished-foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '',
                        '  - id: "02"',
                        '    title: "Next layer"',
                        '    path: "phases/02-next-layer"',
                        '    status: "pending"',
                        '    depends_on: ["01"]',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "next")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next phase: 02 - Next layer", result.stdout)
            self.assertIn("Pending but unblocked", result.stdout)
            self.assertIn("Run next layer", result.stdout)

    def test_issues_reports_unlinked_and_linked_issues_from_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Ship useful app"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Existing linked phase"',
                        '    path: "phases/01-existing-linked-phase"',
                        '    status: "pending"',
                        '    depends_on: []',
                        '    github_issues: ["#123"]',
                    ]
                ),
                encoding="utf-8",
            )
            issues = (
                '[{"number":123,"title":"Existing linked phase","state":"OPEN","url":"https://github.com/o/r/issues/123"},'
                '{"number":128,"title":"Add settings export","state":"OPEN","url":"https://github.com/o/r/issues/128"}]'
            )

            result = self.run_wily_with_env(project, "issues", env={"WILY_ISSUES_JSON": issues})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("GitHub Issues", result.stdout)
            self.assertIn("Linked issues:", result.stdout)
            self.assertIn("#123 Existing linked phase -> 01", result.stdout)
            self.assertIn("Unlinked open issues:", result.stdout)
            self.assertIn("#128 Add settings export", result.stdout)
            self.assertIn("Suggested roadmap additions:", result.stdout)
            self.assertIn("Run with `--add-to-roadmap` only after approval.", result.stdout)

    def test_issues_add_to_roadmap_creates_local_phase_for_unlinked_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Ship useful app"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Foundation"',
                        '    path: "phases/01-foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )
            issues = '[{"number":128,"title":"Add settings export","state":"OPEN","url":"https://github.com/o/r/issues/128"}]'

            result = self.run_wily_with_env(project, "issues", "--add-to-roadmap", env={"WILY_ISSUES_JSON": issues})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Added roadmap phases from GitHub issues:", result.stdout)
            self.assertIn("02 #128 Add settings export", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('roadmap_version: 2', roadmap)
            self.assertIn('title: "#128 Add settings export"', roadmap)
            self.assertIn('github_issues: ["#128"]', roadmap)
            self.assertIn('github_urls: ["https://github.com/o/r/issues/128"]', roadmap)
            phase_dir = project / ".wily" / "phases" / "02-github-issue-128-add-settings-export"
            self.assertTrue((phase_dir / "phase.md").is_file())
            self.assertIn("https://github.com/o/r/issues/128", (phase_dir / "phase.md").read_text(encoding="utf-8"))

    def test_issues_add_to_roadmap_handles_empty_phase_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "roadmap_version: 1\ngoal: \"Ship useful app\"\nphases: []\n",
                encoding="utf-8",
            )
            issues = '[{"number":128,"title":"Add settings export","state":"OPEN","url":"https://github.com/o/r/issues/128"}]'

            result = self.run_wily_with_env(project, "issues", "--add-to-roadmap", env={"WILY_ISSUES_JSON": issues})

            self.assertEqual(result.returncode, 0, result.stderr)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('  - id: "01"', roadmap)
            self.assertIn('title: "#128 Add settings export"', roadmap)

    def test_issues_without_source_reports_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text("roadmap_version: 1\nphases: []\n", encoding="utf-8")

            result = self.run_wily_with_env(project, "issues", env={"PATH": ""})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("GitHub issue source not configured.", result.stdout)
            self.assertIn("Core Wily commands do not require GitHub Issues.", result.stdout)

    def test_serialize_parse_preserves_replacement_metadata(self) -> None:
        roadmap = {
            "roadmap_version": 2,
            "phases": [
                {
                    "id": "04",
                    "title": "Old integration plan",
                    "path": "phases/04-old-integration",
                    "status": "superseded",
                    "depends_on": ["03"],
                    "superseded_by": ["04R"],
                },
                {
                    "id": "04R",
                    "title": "Adapt foundation",
                    "path": "phases/04r-adapt-foundation",
                    "status": "ready",
                    "depends_on": ["03"],
                    "replaces": ["04"],
                },
            ],
        }

        serialized = wily.serialize_roadmap(roadmap)
        parsed = wily_state_summary.parse_roadmap(serialized)

        self.assertEqual(parsed["roadmap_version"], 2)
        self.assertEqual(parsed["phases"][0]["status"], "superseded")
        self.assertEqual(parsed["phases"][0]["superseded_by"], ["04R"])
        self.assertEqual(parsed["phases"][1]["replaces"], ["04"])

    def test_serialize_parse_preserves_multiline_phase_scalar(self) -> None:
        roadmap = {
            "roadmap_version": 1,
            "phases": [
                {
                    "id": "01",
                    "title": "Multiline phase",
                    "status": "pending",
                    "summary": "Line one\nLine two\n",
                    "depends_on": [],
                },
            ],
        }

        serialized = wily.serialize_roadmap(roadmap)
        parsed = wily_state_summary.parse_roadmap(serialized)

        self.assertEqual(parsed["phases"][0]["summary"], "Line one\nLine two\n")

    def test_replan_records_revision_and_increments_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Ship useful app"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Finished work"',
                        '    path: "phases/01-finished-work"',
                        '    status: "done"',
                        '    depends_on: []',
                        '',
                        '  - id: "02"',
                        '    title: "Future work"',
                        '    path: "phases/02-future-work"',
                        '    status: "pending"',
                        '    depends_on: ["01"]',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "replan", "Switch target")

            self.assertEqual(result.returncode, 0, result.stderr)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn("roadmap_version: 2", roadmap)
            self.assertIn('status: "done"', roadmap)
            revisions = sorted((project / ".wily" / "revisions").glob("*.md"))
            self.assertEqual(len(revisions), 1)
            self.assertIn("Switch target", revisions[0].read_text(encoding="utf-8"))

    def test_start_creates_session_and_marks_phase_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "start", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Started phase 01", result.stdout)
            sessions = sorted((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            self.assertEqual(len(sessions), 1)
            session = sessions[0]
            self.assertTrue((session / "status.yaml").is_file())
            self.assertTrue((session / "input.md").is_file())
            self.assertTrue((session / "result.md").is_file())
            self.assertTrue((session / "verification.md").is_file())
            self.assertTrue((session / "changed-files.md").is_file())
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', roadmap)
            self.assertIn('current_session: "sessions/', roadmap)

    def test_start_does_not_emit_board_live_event_without_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            with patch.dict(os.environ, isolated_env(), clear=True), patch.object(wily, "emit_board_live_event") as emit:
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            emit.assert_not_called()

    def test_start_emits_board_live_event_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            emitted: list[tuple[str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "start", "claimed")])

    def test_start_warns_when_board_reports_other_fresh_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            warning = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily,
                "fetch_board_live_claims",
                return_value=[{"actor": "Julirsia", "last_seen_label": "20s ago"}],
            ), patch.object(
                wily, "emit_board_live_event"
            ), patch(
                "sys.stderr", warning
            ):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            self.assertIn("Board claim warning", warning.getvalue())
            self.assertIn("Julirsia", warning.getvalue())

    def test_start_warns_when_bridge_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            stderr = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stderr", stderr):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("not configured", stderr.getvalue())
            self.assertIn("wily board check", stderr.getvalue())

    def test_start_surfaces_bridge_emit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily, "emit_board_live_event", return_value=(False, "HTTP 502")
            ), patch("sys.stderr", stderr):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("HTTP 502", stderr.getvalue())

    def test_complete_surfaces_bridge_emit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily, "emit_board_live_event", return_value=(False, "HTTP 502")
            ), patch("sys.stderr", stderr):
                result = wily.command_complete(project, ["01"])

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("HTTP 502", stderr.getvalue())

    def test_block_surfaces_bridge_emit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily, "emit_board_live_event", return_value=(False, "HTTP 502")
            ), patch("sys.stderr", stderr):
                result = wily.command_block(project, ["01", "Permission missing"])

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("HTTP 502", stderr.getvalue())

    def test_live_worked_surfaces_bridge_emit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily, "emit_board_live_event", return_value=(False, "HTTP 502")
            ), patch("sys.stderr", stderr):
                result = wily.command_live_worked(project, ["01", "--agent", "codex"])

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("HTTP 502", stderr.getvalue())

    def test_live_heartbeat_surfaces_bridge_emit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next(
                (project / ".wily" / "local" / "live" / "active").glob("*.json")
            )
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]
            stderr = io.StringIO()

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(
                wily, "emit_board_live_event", return_value=(False, "HTTP 502")
            ), patch("sys.stderr", stderr):
                result = wily.command_live_heartbeat(
                    project, ["01", "--session", session_id, "--count", "1"]
                )

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stderr.getvalue())
            self.assertIn("HTTP 502", stderr.getvalue())

    def test_status_warns_when_bridge_not_configured_with_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            stdout = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stdout", stdout):
                result = wily.command_status(project)

            self.assertEqual(result, 0)
            self.assertIn("Board bridge", stdout.getvalue())
            self.assertIn("not connected", stdout.getvalue())

    def test_board_live_config_loads_repo_local_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            local = project / ".wily" / "local"
            local.mkdir(parents=True)
            (local / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                        "agent": "codex",
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, isolated_env(), clear=True):
                config = wily.board_live_config(project)

            self.assertEqual(config["WILY_BOARD_URL"], "https://board.local")
            self.assertEqual(config["WILY_BOARD_SECRET"], "secret")
            self.assertEqual(config["WILY_BOARD_REPO"], "R-W-LAB/wily-roadmap")
            self.assertEqual(config["WILY_BOARD_ACTOR"], "airmang")
            self.assertEqual(config["WILY_BOARD_AGENT"], "codex")

    def test_board_live_config_loads_repo_root_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "root-secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                        "agent": "codex",
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, isolated_env(), clear=True):
                config = wily.board_live_config(project)

            self.assertEqual(config["WILY_BOARD_URL"], "https://board.local")
            self.assertEqual(config["WILY_BOARD_SECRET"], "root-secret")
            self.assertEqual(config["WILY_BOARD_REPO"], "R-W-LAB/wily-roadmap")
            self.assertEqual(config["WILY_BOARD_ACTOR"], "airmang")
            self.assertEqual(config["WILY_BOARD_AGENT"], "codex")

    def test_board_check_reports_missing_config_and_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            hooks_path = project / "hooks.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                result = wily.command_board(project, ["check", "--hooks-path", str(hooks_path)])

            self.assertEqual(result, 1)
            combined = stdout.getvalue() + stderr.getvalue()
            self.assertIn("Board live config: missing", combined)
            self.assertIn("WILY_BOARD_URL", combined)
            self.assertIn("Codex hook: missing", combined)

    def test_board_check_redacts_secret_and_detects_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "do-not-print",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                    }
                ),
                encoding="utf-8",
            )
            hooks_path = project / "hooks.json"
            self.assertEqual(wily.command_hooks(project, ["install", "--target", "codex", "--path", str(hooks_path)]), 0)
            stdout = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stdout", stdout):
                result = wily.command_board(project, ["check", "--hooks-path", str(hooks_path)])

            output = stdout.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("Board live config: ok", output)
            self.assertIn("https://board.local", output)
            self.assertIn("R-W-LAB/wily-roadmap", output)
            self.assertIn("airmang", output)
            self.assertIn("secret: <redacted>", output)
            self.assertIn("Codex hook: ok", output)
            self.assertNotIn("do-not-print", output)

    def _probe_response(self, status: int) -> MagicMock:
        response = MagicMock()
        response.status = status
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=None)
        return response

    def test_probe_board_endpoint_returns_ok_on_2xx_response(self) -> None:
        values = {
            "WILY_BOARD_URL": "https://board.example",
            "WILY_BOARD_SECRET": "secret",
            "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
            "WILY_BOARD_ACTOR": "airmang",
        }

        with patch("urllib.request.urlopen", return_value=self._probe_response(200)):
            result = wily.probe_board_endpoint(values)

        self.assertEqual(result, "ok (HTTP 200)")

    def test_probe_board_endpoint_returns_rejected_on_4xx_http_error(self) -> None:
        values = {
            "WILY_BOARD_URL": "https://board.example",
            "WILY_BOARD_SECRET": "secret",
            "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
            "WILY_BOARD_ACTOR": "airmang",
        }
        http_error = urllib.error.HTTPError(
            url="https://board.example/api/live/claims",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            result = wily.probe_board_endpoint(values)

        self.assertIn("rejected", result)
        self.assertIn("401", result)

    def test_probe_board_endpoint_returns_server_error_on_5xx_http_error(self) -> None:
        values = {
            "WILY_BOARD_URL": "https://board.example",
            "WILY_BOARD_SECRET": "secret",
            "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
            "WILY_BOARD_ACTOR": "airmang",
        }
        http_error = urllib.error.HTTPError(
            url="https://board.example/api/live/claims",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            result = wily.probe_board_endpoint(values)

        self.assertIn("server error", result)
        self.assertIn("503", result)

    def test_probe_board_endpoint_returns_unreachable_on_url_error(self) -> None:
        values = {
            "WILY_BOARD_URL": "https://board.example",
            "WILY_BOARD_SECRET": "secret",
            "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
            "WILY_BOARD_ACTOR": "airmang",
        }

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Name or service not known")):
            result = wily.probe_board_endpoint(values)

        self.assertIn("unreachable", result)
        self.assertIn("Name or service not known", result)

    def test_board_check_probe_prints_endpoint_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                    }
                ),
                encoding="utf-8",
            )
            hooks_path = project / "hooks.json"
            self.assertEqual(
                wily.command_hooks(project, ["install", "--target", "codex", "--path", str(hooks_path)]),
                0,
            )
            stdout = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch.object(
                wily, "probe_board_endpoint", return_value="ok (HTTP 200)"
            ), patch("sys.stdout", stdout):
                result = wily.command_board(
                    project, ["check", "--probe", "--hooks-path", str(hooks_path)]
                )

            self.assertEqual(result, 0)
            self.assertIn("endpoint: ok (HTTP 200)", stdout.getvalue())

    def test_board_check_without_probe_keeps_not_probed_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                    }
                ),
                encoding="utf-8",
            )
            hooks_path = project / "hooks.json"
            self.assertEqual(
                wily.command_hooks(project, ["install", "--target", "codex", "--path", str(hooks_path)]),
                0,
            )
            stdout = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch.object(
                wily, "probe_board_endpoint"
            ) as probe, patch("sys.stdout", stdout):
                result = wily.command_board(
                    project, ["check", "--hooks-path", str(hooks_path)]
                )

            self.assertEqual(result, 0)
            self.assertIn("endpoint: not probed", stdout.getvalue())
            probe.assert_not_called()

    def test_board_check_probe_skips_when_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            hooks_path = project / "hooks.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch.object(
                wily, "probe_board_endpoint"
            ) as probe, patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                result = wily.command_board(
                    project, ["check", "--probe", "--hooks-path", str(hooks_path)]
                )

            self.assertEqual(result, 1)
            combined = stdout.getvalue() + stderr.getvalue()
            self.assertIn("endpoint: not probed", combined)
            probe.assert_not_called()

    def test_record_board_emit_result_writes_success_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()

            wily._record_board_emit_result(project, "start", True)

            cache = json.loads(
                (project / ".wily" / "local" / "board-last-emit.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(cache["last_success"]["event"], "start")
            self.assertIn("at", cache["last_success"])
            self.assertNotIn("last_failure", cache)

    def test_record_board_emit_result_writes_failure_entry_preserving_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()

            wily._record_board_emit_result(project, "start", True)
            wily._record_board_emit_result(project, "worked", False, "HTTP 502")

            cache = json.loads(
                (project / ".wily" / "local" / "board-last-emit.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(cache["last_success"]["event"], "start")
            self.assertEqual(cache["last_failure"]["event"], "worked")
            self.assertEqual(cache["last_failure"]["reason"], "HTTP 502")

    def test_emit_board_live_event_records_result_to_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            values = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                "WILY_BOARD_ACTOR": "airmang",
            }
            response = MagicMock()
            response.status = 200
            response.__enter__ = MagicMock(return_value=response)
            response.__exit__ = MagicMock(return_value=None)

            phase = {"id": "01", "item_id": "01", "item_type": "phase", "phase_id": "01"}

            with patch.dict(os.environ, values, clear=True), patch(
                "urllib.request.urlopen", return_value=response
            ):
                ok, err = wily.emit_board_live_event(project, phase, "start", "claimed")

            self.assertTrue(ok)
            cache = json.loads(
                (project / ".wily" / "local" / "board-last-emit.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(cache["last_success"]["event"], "start")

    def test_board_check_prints_last_emit_when_cache_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            state = project / ".wily"
            state.mkdir()
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                    }
                ),
                encoding="utf-8",
            )
            hooks_path = project / "hooks.json"
            self.assertEqual(
                wily.command_hooks(project, ["install", "--target", "codex", "--path", str(hooks_path)]),
                0,
            )
            wily._record_board_emit_result(project, "worked", False, "HTTP 502")
            stdout = io.StringIO()

            with patch.dict(os.environ, isolated_env(), clear=True), patch("sys.stdout", stdout):
                result = wily.command_board(
                    project, ["check", "--hooks-path", str(hooks_path)]
                )

            self.assertEqual(result, 0)
            self.assertIn("last bridge failure", stdout.getvalue())
            self.assertIn("HTTP 502", stdout.getvalue())
            self.assertIn("worked", stdout.getvalue())

    def test_start_writes_live_active_registry_without_board_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            with patch.dict(os.environ, isolated_env(), clear=True):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            active_files = sorted((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            self.assertEqual(len(active_files), 1)
            payload = json.loads(active_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["item_type"], "phase")
            self.assertEqual(payload["item_id"], "01")
            self.assertEqual(payload["phase_id"], "01")
            self.assertEqual(payload["agent"], "codex")
            self.assertTrue((project / ".wily" / "local" / "live" / f"{payload['session_id']}.alive").exists())
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertNotIn("session_id:", roadmap)

    def test_start_spawns_detached_heartbeat_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                    "WILY_BOARD_HEARTBEAT": "1",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event"), patch.object(wily.subprocess, "Popen") as popen:
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            popen.assert_called_once()
            command = popen.call_args.args[0]
            self.assertIn("live-heartbeat", command)
            self.assertIn("01", command)
            self.assertIn("--session", command)
            self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_complete_cleans_live_registry_and_alive_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]

            with patch.dict(os.environ, isolated_env(), clear=True):
                result = wily.command_complete(project, ["01"])

            self.assertEqual(result, 0)
            self.assertEqual(list((project / ".wily" / "local" / "live" / "active").glob("*.json")), [])
            self.assertFalse((project / ".wily" / "local" / "live" / f"{session_id}.alive").exists())

    def test_live_heartbeat_writes_pid_file_and_updates_registry_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]
            emitted: list[tuple[str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_live_heartbeat(project, ["01", "--session", session_id, "--count", "1"])

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "heartbeat", "active")])
            self.assertTrue((project / ".wily" / "local" / "live" / f"{session_id}.pid").exists())
            payload = json.loads(active_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["session_id"], session_id)
            self.assertEqual(payload["live_status"], "active")

    def test_live_heartbeat_releases_when_parent_shell_is_gone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]
            emitted: list[tuple[str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_live_heartbeat(
                    project,
                    ["01", "--session", session_id, "--parent-shell-pid", "999999999", "--count", "1"],
                )

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "release", "released")])
            self.assertFalse(active_file.exists())

    def test_release_cleans_live_registry_without_changing_phase_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)

            result = wily.command_release(project, ["01"])

            self.assertEqual(result, 0)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', roadmap)
            self.assertEqual(list((project / ".wily" / "local" / "live" / "active").glob("*.json")), [])

    def test_start_recovers_orphan_live_registry_without_alive_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            active = project / ".wily" / "local" / "live" / "active"
            active.mkdir(parents=True)
            (active / "orphan.json").write_text(
                json.dumps({"session_id": "orphan", "item_id": "old", "item_type": "phase"}),
                encoding="utf-8",
            )

            with patch.dict(os.environ, isolated_env(), clear=True):
                result = wily.command_start(project, ["01"])

            self.assertEqual(result, 0)
            active_files = sorted(active.glob("*.json"))
            self.assertEqual(len(active_files), 1)
            self.assertNotEqual(active_files[0].name, "orphan.json")

    def test_live_worked_resolves_active_session_and_updates_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)

            result = wily.command_live_worked(project, ["01", "--agent", "codex", "--tool", "Edit"])

            self.assertEqual(result, 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            payload = json.loads(active_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["event"], "worked")
            self.assertEqual(payload["tool"], "Edit")
            self.assertEqual(payload["live_status"], "active")
            self.assertIn("last_worked_at", payload)

    def test_live_worked_from_hook_without_active_session_is_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = wily.command_live_worked(project, ["--from-hook", "--agent", "codex"])

            self.assertEqual(result, 0)

    def test_hooks_install_codex_writes_post_tool_use_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            hook_path = project / "hooks.json"

            result = wily.command_hooks(project, ["install", "--target", "codex", "--path", str(hook_path)])

            self.assertEqual(result, 0)
            payload = json.loads(hook_path.read_text(encoding="utf-8"))
            text = json.dumps(payload)
            self.assertIn("PostToolUse", text)
            self.assertIn("live-worked", text)
            self.assertIn("--from-hook", text)

    def test_hooks_install_claude_writes_post_tool_use_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            settings_path = project / "settings.json"

            result = wily.command_hooks(project, ["install", "--target", "claude", "--path", str(settings_path)])

            self.assertEqual(result, 0)
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
            text = json.dumps(payload)
            self.assertIn("PostToolUse", text)
            self.assertIn("live-worked", text)
            self.assertIn("--from-hook", text)

    def test_checkpoint_sync_reads_custom_workflow_status_board_without_completing_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            handoffs = project / "agent-handoffs"
            handoffs.mkdir()
            status_board = handoffs / "demo-status.md"
            status_board.write_text(
                "\n".join(
                    [
                        "# Goal Status: Demo",
                        "",
                        "State: RUNNING",
                        "Progress: 1 / 3 (33%)",
                        "",
                        "## Now",
                        "",
                        "Current checkpoint: CP02 - Build adapter",
                        "Current action: parsing status board",
                        "Next checkpoint: CP03 - Verify board payload",
                        "Current blocker: none",
                        "",
                        "## Checkpoints",
                        "",
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP01 | DONE | Contract | root | baseline passed |",
                        "| CP02 | RUNNING | Build adapter | root |  |",
                        "| CP03 | TODO | Verify board payload | root |  |",
                        "",
                        "## Verification",
                        "",
                        "| Command / Check | Last run | Exit | Status | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| `python -m unittest` | 2026-05-17T00:00:00Z | 0 | PASS | adapter tests |",
                        "",
                        "## Recent Events",
                        "",
                        "- 2026-05-17T00:00:00Z - Started CP02.",
                    ]
                ),
                encoding="utf-8",
            )
            emitted: list[tuple[dict, str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> tuple[bool, str]:
                emitted.append((phase, event, live_status, note))
                return True, ""

            env = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/demo",
                "WILY_BOARD_ACTOR": "airmang",
                "WILY_BOARD_AGENT": "codex",
            }
            with patch.dict(os.environ, env, clear=True), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_checkpoint_sync(project, ["01", "--status-board", str(status_board)])

            self.assertEqual(result, 0)
            payload_path = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["event"], "checkpoint_updated")
            self.assertEqual(payload["live_status"], "active")
            self.assertEqual(payload["checkpoint"]["current"]["id"], "CP02")
            self.assertEqual(payload["checkpoint"]["next"]["id"], "CP03")
            self.assertEqual(payload["checkpoint"]["progress"]["done"], 1)
            self.assertEqual(payload["checkpoint"]["current_action"], "parsing status board")
            self.assertEqual(payload["checkpoint"]["recent_events"], ["2026-05-17T00:00:00Z - Started CP02."])
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "ready"', roadmap)
            self.assertEqual(emitted[0][1:], ("checkpoint_updated", "active", "parsing status board"))

    def test_checkpoint_sync_records_v2_tuple_identity_and_non_durable_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT / "tests" / "fixtures" / "migration" / "already-v2", project)
            status_board = project / "status.md"
            status_board.write_text(
                "\n".join(
                    [
                        "# Goal Status: Demo",
                        "",
                        "State: RUNNING",
                        "Progress: 1 / 2 (50%)",
                        "Current checkpoint: CP01 - Parser",
                        "Current action: syncing tuple overlay",
                        "Next checkpoint: CP02 - Verify",
                        "Current blocker: none",
                        "",
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP01 | RUNNING | Parser | root |  |",
                        "| CP02 | TODO | Verify | root |  |",
                    ]
                ),
                encoding="utf-8",
            )
            emitted: list[tuple[dict, str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> tuple[bool, str]:
                emitted.append((phase, event, live_status, note))
                return True, ""

            env = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/demo",
                "WILY_BOARD_ACTOR": "airmang",
            }
            with patch.dict(os.environ, env, clear=True), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_checkpoint_sync(project, ["s02/p01", "--status-board", str(status_board)])

            self.assertEqual(result, 0)
            payload_path = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["stage_id"], "s02")
            self.assertEqual(payload["phase_id"], "p01")
            self.assertEqual(payload["checkpoint"]["source"], "custom-workflow")
            self.assertEqual(payload["checkpoint"]["status_board"], "status.md")
            self.assertFalse(payload["checkpoint"]["is_durable"])
            self.assertEqual(payload["checkpoint"]["current"]["id"], "CP01")
            self.assertEqual(emitted[0][0]["stage_id"], "s02")
            self.assertEqual(emitted[0][0]["phase_id"], "p01")
            self.assertEqual(emitted[0][1:], ("checkpoint_updated", "active", "syncing tuple overlay"))

    def test_live_worked_preserves_checkpoint_context_on_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            status_board = project / "status.md"
            status_board.write_text(
                "\n".join(
                    [
                        "# Goal Status: Demo",
                        "",
                        "State: RUNNING",
                        "Progress: 1 / 2 (50%)",
                        "Current checkpoint: CP02 - Build adapter",
                        "Current action: editing bridge",
                        "Next checkpoint: CP03 - Verify",
                        "Current blocker: none",
                        "",
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP02 | RUNNING | Build adapter | root |  |",
                        "| CP03 | TODO | Verify | root |  |",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/demo",
                "WILY_BOARD_ACTOR": "airmang",
                "WILY_BOARD_AGENT": "codex",
            }

            with patch.dict(os.environ, env, clear=True), patch.object(wily, "fetch_board_live_claims", return_value=[]), patch.object(
                wily, "emit_board_live_event", return_value=(True, "")
            ):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
                self.assertEqual(wily.command_checkpoint_sync(project, ["01", "--status-board", str(status_board)]), 0)
                checkpoint_payload = json.loads(
                    next((project / ".wily" / "local" / "live" / "active").glob("*.json")).read_text(encoding="utf-8")
                )
                session_id = checkpoint_payload["session_id"]
                self.assertEqual(wily.command_live_worked(project, ["01", "--summary", "edited bridge"]), 0)

            worked_payload = json.loads(
                (project / ".wily" / "local" / "live" / "active" / f"{session_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(worked_payload["event"], "worked")
            self.assertEqual(worked_payload["session_id"], session_id)
            self.assertEqual(worked_payload["checkpoint"]["current"]["id"], "CP02")
            self.assertEqual(worked_payload["summary"], "edited bridge")
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', roadmap)

    def test_live_heartbeat_preserves_checkpoint_context_on_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            status_board = project / "status.md"
            status_board.write_text(
                "\n".join(
                    [
                        "# Goal Status: Demo",
                        "",
                        "State: RUNNING",
                        "Progress: 1 / 2 (50%)",
                        "Current checkpoint: CP02 - Build adapter",
                        "Current action: editing bridge",
                        "Next checkpoint: CP03 - Verify",
                        "Current blocker: none",
                        "",
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP02 | RUNNING | Build adapter | root |  |",
                        "| CP03 | TODO | Verify | root |  |",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/demo",
                "WILY_BOARD_ACTOR": "airmang",
                "WILY_BOARD_AGENT": "codex",
            }
            emitted: list[dict[str, object]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> tuple[bool, str]:
                emitted.append(dict(phase))
                return True, ""

            with patch.dict(os.environ, env, clear=True), patch.object(wily, "fetch_board_live_claims", return_value=[]), patch.object(
                wily, "emit_board_live_event", side_effect=record_event
            ):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
                self.assertEqual(wily.command_checkpoint_sync(project, ["01", "--status-board", str(status_board)]), 0)
                checkpoint_payload = json.loads(
                    next((project / ".wily" / "local" / "live" / "active").glob("*.json")).read_text(encoding="utf-8")
                )
                session_id = checkpoint_payload["session_id"]
                self.assertEqual(wily.command_live_heartbeat(project, ["01", "--session", session_id, "--count", "1"]), 0)

            heartbeat_payload = json.loads(
                (project / ".wily" / "local" / "live" / "active" / f"{session_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(heartbeat_payload["event"], "heartbeat")
            self.assertEqual(heartbeat_payload["session_id"], session_id)
            self.assertEqual(heartbeat_payload["checkpoint"]["current"]["id"], "CP02")
            self.assertEqual(emitted[-1]["checkpoint"]["current"]["id"], "CP02")

    def test_live_heartbeat_reuses_active_checkpoint_session_without_session_arg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            status_board = project / "status.md"
            status_board.write_text(
                "\n".join(
                    [
                        "# Goal Status: Demo",
                        "",
                        "State: RUNNING",
                        "Progress: 1 / 2 (50%)",
                        "Current checkpoint: CP02 - Build adapter",
                        "Current action: editing bridge",
                        "Next checkpoint: CP03 - Verify",
                        "Current blocker: none",
                        "",
                        "| ID | Status | Checkpoint | Owner | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| CP02 | RUNNING | Build adapter | root |  |",
                        "| CP03 | TODO | Verify | root |  |",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "WILY_BOARD_URL": "https://board.example",
                "WILY_BOARD_SECRET": "secret",
                "WILY_BOARD_REPO": "R-W-LAB/demo",
                "WILY_BOARD_ACTOR": "airmang",
                "WILY_BOARD_AGENT": "codex",
            }

            with patch.dict(os.environ, env, clear=True), patch.object(wily, "fetch_board_live_claims", return_value=[]), patch.object(
                wily, "emit_board_live_event", return_value=(True, "")
            ):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
                self.assertEqual(wily.command_checkpoint_sync(project, ["01", "--status-board", str(status_board)]), 0)
                checkpoint_payload = json.loads(
                    next((project / ".wily" / "local" / "live" / "active").glob("*.json")).read_text(encoding="utf-8")
                )
                session_id = checkpoint_payload["session_id"]
                self.assertEqual(wily.command_live_heartbeat(project, ["01", "--count", "1"]), 0)

            heartbeat_payload = json.loads(
                (project / ".wily" / "local" / "live" / "active" / f"{session_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(heartbeat_payload["event"], "heartbeat")
            self.assertEqual(heartbeat_payload["session_id"], session_id)
            self.assertEqual(heartbeat_payload["checkpoint"]["current"]["id"], "CP02")

    def test_codex_bridge_fixture_converts_item_completed_to_worked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]
            fixture = project / "notifications.jsonl"
            fixture.write_text(
                json.dumps({"method": "turn/started", "params": {}})
                + "\n"
                + json.dumps({"method": "item/completed", "params": {"item": {"type": "tool", "name": "Edit"}}})
                + "\n",
                encoding="utf-8",
            )

            result = wily.command_codex_bridge(project, ["--session", session_id, "--fixture", str(fixture), "--once"])

            self.assertEqual(result, 0)
            payload = json.loads(active_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["event"], "worked")
            self.assertEqual(payload["agent"], "codex-desktop")
            self.assertIn("last_worked_at", payload)

    def test_codex_bridge_missing_fixture_degrades_to_heartbeat_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            with patch.dict(os.environ, isolated_env(), clear=True):
                self.assertEqual(wily.command_start(project, ["01"]), 0)
            active_file = next((project / ".wily" / "local" / "live" / "active").glob("*.json"))
            session_id = json.loads(active_file.read_text(encoding="utf-8"))["session_id"]

            result = wily.command_codex_bridge(
                project,
                ["--session", session_id, "--fixture", str(project / "missing.jsonl"), "--once"],
            )

            self.assertEqual(result, 0)
            payload = json.loads(active_file.read_text(encoding="utf-8"))
            self.assertNotIn("last_worked_at", payload)

    def test_start_preserves_block_yaml_roadmap_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            phase_dir = project / ".wily" / "phases" / "02-block-yaml"
            phase_dir.mkdir(parents=True)
            (phase_dir / "phase.md").write_text("# Phase\n\nBlock YAML phase\n", encoding="utf-8")
            (phase_dir / "prompt.md").write_text("Run this phase\n", encoding="utf-8")
            (phase_dir / "verification.md").write_text("python3 -m unittest\n", encoding="utf-8")
            (phase_dir / "handoff.md").write_text("Resume from here\n", encoding="utf-8")
            (phase_dir / "planner.md").write_text("# Planner\n", encoding="utf-8")
            (phase_dir / "plan.md").write_text("", encoding="utf-8")
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Foundation"',
                        '    path: "phases/01-foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '  - id: "02"',
                        '    title: "Block YAML"',
                        '    path: "phases/02-block-yaml"',
                        '    status: "pending"',
                        '    depends_on:',
                        '      - "01"',
                        '    summary: >-',
                        '      Preserve this summary',
                        '      across start.',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "start", "02")

            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = wily_state_summary.parse_roadmap(
                (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(len(parsed["phases"]), 2)
            phase = parsed["phases"][1]
            self.assertEqual(phase["depends_on"], ["01"])
            self.assertEqual(phase["summary"], "Preserve this summary across start.")
            self.assertEqual(phase["status"], "in_progress")
            self.assertIn("current_session", phase)

    def test_start_writes_external_planner_context_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            phase_dir = project / ".wily" / "phases" / "01-first-phase"
            (phase_dir / "plan.md").write_text("External generated plan\n", encoding="utf-8")

            result = self.run_wily(project, "start", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            sessions = sorted((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            self.assertEqual(len(sessions), 1)
            input_text = (sessions[0] / "input.md").read_text(encoding="utf-8")
            self.assertIn("# Wily Phase Context", input_text)
            self.assertIn("## Phase", input_text)
            self.assertIn("Roadmap-level phase definition", input_text)
            self.assertIn("## Planner Adapter", input_text)
            self.assertIn("Recommended planner: superpowers:writing-plans", input_text)
            self.assertIn("## Prompt", input_text)
            self.assertIn("Run this phase", input_text)
            self.assertIn("## Verification", input_text)
            self.assertIn("python3 -m unittest", input_text)
            self.assertIn("## Handoff", input_text)
            self.assertIn("Resume from here", input_text)
            self.assertIn("## Existing Implementation Plan", input_text)
            self.assertIn("External generated plan", input_text)

    def test_start_records_recommended_planner_in_session_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "start", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            status_files = list((project / ".wily" / "sessions").glob("*phase-01-attempt-1/status.yaml"))
            self.assertEqual(len(status_files), 1)
            status_text = status_files[0].read_text(encoding="utf-8")
            self.assertIn('planner: "superpowers:writing-plans"', status_text)

    def test_start_allows_missing_implementation_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = self.run_wily(project, "start", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            sessions = sorted((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
            self.assertEqual(len(sessions), 1)
            input_text = (sessions[0] / "input.md").read_text(encoding="utf-8")
            self.assertIn("## Existing Implementation Plan", input_text)
            self.assertIn("No implementation plan exists yet.", input_text)
            self.assertIn("Use the recommended planner to create one if this phase needs a detailed plan.", input_text)

    def test_complete_marks_phase_done_and_session_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")

            result = self.run_wily(project, "complete", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Completed phase 01", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "done"', roadmap)
            status_files = list((project / ".wily" / "sessions").glob("*phase-01-attempt-1/status.yaml"))
            self.assertEqual(len(status_files), 1)
            self.assertIn('status: "verified"', status_files[0].read_text(encoding="utf-8"))

    def test_complete_emits_board_live_event_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")
            emitted: list[tuple[str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_complete(project, ["01"])

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "complete", "completed_local")])

    def test_complete_without_current_session_clears_stale_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "roadmap_version: 1",
                        "phases:",
                        '  - id: "01"',
                        '    title: "Blocked phase"',
                        '    path: "phases/01-blocked-phase"',
                        '    status: "blocked"',
                        '    depends_on: []',
                        '    blocker: "Waiting for access"',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "complete", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "done"', roadmap)
            self.assertNotIn("blocker:", roadmap)

    def test_land_refuses_phase_that_is_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            self.write_ready_phase(project)
            self.init_git_project_with_origin(project, Path(tmp) / "remote.git")
            self.assert_git_ok(project, "checkout", "-b", "phase-01")
            (project / "app.txt").write_text("work in progress\n", encoding="utf-8")

            result = self.run_wily(project, "land", "01")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Phase is not done: 01", result.stderr)
            self.assertEqual(
                self.assert_git_ok(project, "branch", "--show-current").stdout.strip(),
                "phase-01",
            )

    def test_land_commits_pushes_fast_forward_merges_and_returns_to_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            self.write_ready_phase(project)
            self.init_git_project_with_origin(project, Path(tmp) / "remote.git")
            self.assert_git_ok(project, "checkout", "-b", "phase-01")
            complete = self.run_wily(project, "complete", "01")
            self.assertEqual(complete.returncode, 0, complete.stderr)
            (project / "app.txt").write_text("landed work\n", encoding="utf-8")

            result = self.run_wily(project, "land", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Commit paths:", result.stdout)
            self.assertIn("A\tapp.txt", result.stdout)
            self.assertIn("M\t.wily/roadmap.yaml", result.stdout)
            self.assertIn("Committed:", result.stdout)
            self.assertIn("Pushed branch: phase-01", result.stdout)
            self.assertIn("Landed on main", result.stdout)
            self.assertIn("Pushed base: main", result.stdout)
            self.assertEqual(
                self.assert_git_ok(project, "branch", "--show-current").stdout.strip(),
                "main",
            )
            self.assertEqual((project / "app.txt").read_text(encoding="utf-8"), "landed work\n")
            self.assertIn(
                "app.txt",
                self.assert_git_ok(project, "ls-tree", "--name-only", "origin/main").stdout,
            )

    def test_clean_dry_run_lists_cleanable_artifacts_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            cleanable = [
                project / ".wily" / "local" / "live" / "session.json",
                project / ".wily" / "local" / "board-last-emit.json",
                project / ".playwright-mcp" / "state.json",
                project / ".pytest_cache" / "README.md",
                project / "pkg" / "__pycache__" / "mod.cpython-314.pyc",
            ]
            for path in cleanable:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("temporary\n", encoding="utf-8")
            preserved = [
                project / ".wily" / "local" / "board.json",
                project / ".wily" / "sessions" / "attempt" / "status.yaml",
            ]
            for path in preserved:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("keep\n", encoding="utf-8")

            result = self.run_wily(project, "clean")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Cleanable artifacts:", result.stdout)
            self.assertIn(".wily/local/live/session.json", result.stdout)
            self.assertIn(".wily/local/board-last-emit.json", result.stdout)
            self.assertIn(".playwright-mcp", result.stdout)
            self.assertIn(".pytest_cache", result.stdout)
            self.assertIn("pkg/__pycache__", result.stdout)
            self.assertIn("Run wily clean --yes", result.stdout)
            for path in cleanable + preserved:
                self.assertTrue(path.exists(), f"{path} should not be deleted by dry-run")

    def test_clean_yes_removes_only_cleanable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            cleanable = [
                project / ".wily" / "local" / "live" / "session.json",
                project / ".wily" / "local" / "board-last-emit.json",
                project / ".playwright-mcp" / "state.json",
                project / ".pytest_cache" / "README.md",
                project / "pkg" / "__pycache__" / "mod.cpython-314.pyc",
            ]
            for path in cleanable:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("temporary\n", encoding="utf-8")
            preserved = [
                project / ".wily" / "local" / "board.json",
                project / ".wily" / "sessions" / "attempt" / "status.yaml",
                project / "agent-handoffs" / "handoff.md",
                project / "src" / "app.py",
            ]
            for path in preserved:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("keep\n", encoding="utf-8")

            result = self.run_wily(project, "clean", "--yes")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Removed cleanable artifacts:", result.stdout)
            self.assertFalse((project / ".wily" / "local" / "live" / "session.json").exists())
            self.assertFalse((project / ".wily" / "local" / "board-last-emit.json").exists())
            self.assertFalse((project / ".playwright-mcp").exists())
            self.assertFalse((project / ".pytest_cache").exists())
            self.assertFalse((project / "pkg" / "__pycache__").exists())
            for path in preserved:
                self.assertTrue(path.exists(), f"{path} should be preserved")

    def test_block_marks_phase_blocked_and_records_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")

            result = self.run_wily(project, "block", "01", "Permission missing")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Blocked phase 01", result.stdout)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "blocked"', roadmap)
            self.assertIn('blocker: "Permission missing"', roadmap)
            status_files = list((project / ".wily" / "sessions").glob("*phase-01-attempt-1/status.yaml"))
            self.assertEqual(len(status_files), 1)
            self.assertIn('status: "blocked"', status_files[0].read_text(encoding="utf-8"))
            self.assertIn('blocker: "Permission missing"', status_files[0].read_text(encoding="utf-8"))

    def test_block_emits_board_live_event_with_reason_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")
            emitted: list[tuple[str, str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status, note))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event):
                result = wily.command_block(project, ["01", "Permission missing"])

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "block", "blocked_local", "Permission missing")])

    def test_live_heartbeat_requires_phase_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            result = wily.command_live_heartbeat(project, [])

            self.assertEqual(result, 2)

    def test_live_heartbeat_requires_board_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)

            with patch.dict(os.environ, isolated_env(), clear=True):
                result = wily.command_live_heartbeat(project, ["01", "--count", "1"])

            self.assertEqual(result, 1)

    def test_live_heartbeat_uses_repo_root_board_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            state = project / ".wily"
            state.mkdir(exist_ok=True)
            (state / "board.json").write_text(
                json.dumps(
                    {
                        "url": "https://board.local",
                        "secret": "root-secret",
                        "repo": "R-W-LAB/wily-roadmap",
                        "actor": "airmang",
                    }
                ),
                encoding="utf-8",
            )
            emitted: list[tuple[str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status))

            with patch.dict(os.environ, isolated_env(), clear=True), patch.object(
                wily, "emit_board_live_event", side_effect=record_event
            ):
                result = wily.command_live_heartbeat(project, ["01", "--count", "1"])

            self.assertEqual(result, 0)
            self.assertEqual(emitted, [("01", "heartbeat", "active")])

    def test_live_heartbeat_emits_active_event_with_count_and_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")
            emitted: list[tuple[str, str, str, str]] = []

            def record_event(root: Path, phase: wily.Phase, event: str, live_status: str, note: str = "") -> None:
                emitted.append((str(phase["id"]), event, live_status, note))

            with patch.dict(
                os.environ,
                {
                    "WILY_BOARD_URL": "https://board.example",
                    "WILY_BOARD_SECRET": "secret",
                    "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
                    "WILY_BOARD_ACTOR": "airmang",
                },
                clear=True,
            ), patch.object(wily, "emit_board_live_event", side_effect=record_event), patch.object(
                wily.time, "sleep"
            ) as sleep:
                result = wily.command_live_heartbeat(
                    project,
                    ["01", "--count", "2", "--interval", "0.01", "--note", "running tests"],
                )

            self.assertEqual(result, 0)
            self.assertEqual(
                emitted,
                [
                    ("01", "heartbeat", "active", "running tests"),
                    ("01", "heartbeat", "active", "running tests"),
                ],
            )
            sleep.assert_called_once_with(0.01)

    def test_block_without_current_session_updates_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "roadmap_version: 1",
                        "phases:",
                        '  - id: "01"',
                        '    title: "Ready phase"',
                        '    path: "phases/01-ready-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_wily(project, "block", "01", "Need dependency")

            self.assertEqual(result.returncode, 0, result.stderr)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "blocked"', roadmap)
            self.assertIn('blocker: "Need dependency"', roadmap)

    def test_retry_creates_next_attempt_and_preserves_previous_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_ready_phase(project)
            self.run_wily(project, "start", "01")
            self.run_wily(project, "block", "01", "Permission missing")

            result = self.run_wily(project, "retry", "01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Started phase 01 attempt 2", result.stdout)
            self.assertEqual(len(list((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))), 1)
            self.assertEqual(len(list((project / ".wily" / "sessions").glob("*phase-01-attempt-2"))), 1)
            roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
            self.assertIn('status: "in_progress"', roadmap)
            self.assertIn('current_session: "sessions/', roadmap)
            self.assertNotIn("blocker:", roadmap)


class SelfUpdateCliTest(unittest.TestCase):
    def run_script(
        self,
        plugin: Path,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(plugin / "scripts" / "wily.py"), *args],
            cwd=plugin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, **(env or {})},
        )

    def copy_plugin(self, target: Path) -> Path:
        plugin = target / "wily-roadmap"
        shutil.copytree(ROOT / "scripts", plugin / "scripts")
        shutil.copytree(ROOT / ".codex-plugin", plugin / ".codex-plugin")
        (plugin / "README.md").write_text("# Wily Roadmap\n", encoding="utf-8")
        return plugin

    def git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def assert_git_ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self.git(cwd, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def init_git_plugin_with_origin(self, tmp: Path) -> tuple[Path, Path]:
        plugin = self.copy_plugin(tmp / "source")
        self.assert_git_ok(plugin, "init", "-b", "main")
        self.assert_git_ok(plugin, "config", "user.email", "wily@example.test")
        self.assert_git_ok(plugin, "config", "user.name", "Wily Test")
        self.assert_git_ok(plugin, "add", ".")
        self.assert_git_ok(plugin, "commit", "-m", "initial")
        remote = tmp / "remote.git"
        self.assert_git_ok(tmp, "init", "--bare", str(remote))
        self.assert_git_ok(plugin, "remote", "add", "origin", str(remote))
        self.assert_git_ok(plugin, "push", "-u", "origin", "main")
        return plugin, remote

    def test_update_check_reports_zip_install_without_changing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(Path(tmp))

            result = self.run_script(plugin, "update", "--check")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Current version: 0.1.0", result.stdout)
            self.assertIn("Install type: zip", result.stdout)
            self.assertIn("./wily update --migrate", result.stdout)
            self.assertFalse((plugin / ".git").exists())

    def test_update_check_refuses_dirty_git_install_before_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin, remote = self.init_git_plugin_with_origin(Path(tmp))
            (plugin / "README.md").write_text("# local edit\n", encoding="utf-8")

            result = self.run_script(
                plugin,
                "update",
                "--check",
                env={"WILY_UPDATE_REPOSITORY_URL": str(remote)},
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Working tree has local changes.", result.stdout)
            self.assertIn("README.md", result.stdout)
            self.assertNotIn("Fetching", result.stdout)

    def test_update_check_reports_already_current_git_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin, remote = self.init_git_plugin_with_origin(Path(tmp))

            result = self.run_script(
                plugin,
                "update",
                "--check",
                env={"WILY_UPDATE_REPOSITORY_URL": str(remote)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Current version: 0.1.0", result.stdout)
            self.assertIn("Install type: git", result.stdout)
            self.assertIn("Already current.", result.stdout)

    def test_update_migrate_clones_zip_install_to_managed_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source, remote = self.init_git_plugin_with_origin(tmp_path / "repo")
            zip_plugin = self.copy_plugin(tmp_path / "zip")

            result = self.run_script(
                zip_plugin,
                "update",
                "--migrate",
                env={"WILY_UPDATE_REPOSITORY_URL": str(remote)},
            )

            managed = zip_plugin.parent / "wily-roadmap-managed"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(managed.is_dir())
            self.assertTrue((managed / ".git").is_dir())
            self.assertTrue((zip_plugin / "scripts" / "wily.py").is_file())
            self.assertIn(str(managed), result.stdout)
            self.assertIn("Original zip install left unchanged.", result.stdout)
            self.assertTrue((source / "scripts" / "wily.py").is_file())


if __name__ == "__main__":
    unittest.main()
