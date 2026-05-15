from __future__ import annotations

import os
import re
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "wily.py"
LAUNCHER = ROOT / "wily"
ZSH = shutil.which("zsh")
sys.path.insert(0, str(ROOT / "scripts"))
import wily  # noqa: E402
import wily_state_summary  # noqa: E402
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(value: str) -> str:
    return ANSI_RE.sub("", value)


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
            env={**os.environ, **env},
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
            env={**os.environ, **(env or {})},
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
