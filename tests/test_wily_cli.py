from __future__ import annotations

import os
import re
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
            self.assertTrue((project / ".wily" / "sessions").is_dir())
            self.assertTrue((project / ".wily" / "revisions").is_dir())
            self.assertIn("Ship useful app", (project / ".wily" / "project.md").read_text(encoding="utf-8"))

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

    def test_watch_defaults_to_tmux_pane_mode_outside_tmux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily_with_env(project, "watch", env={"TMUX": ""})

            self.assertEqual(result.returncode, 1)
            self.assertIn("tmux 세션이 아니라서 pane을 열 수 없습니다.", result.stderr)
            self.assertIn("python3", result.stderr)
            self.assertIn("watch --here", result.stderr)

    def test_watch_pane_mode_builds_tmux_split_command_when_inside_tmux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            result = self.run_wily_with_env(project, "watch", "--dry-run-pane", env={"TMUX": "/tmp/tmux"})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("tmux split-window -h", result.stdout)
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


if __name__ == "__main__":
    unittest.main()
