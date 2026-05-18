from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT.parents[1] / ".agents" / "plugins" / "marketplace.json"

COMMANDS = {"init", "next", "claim", "go", "done", "block", "replan", "land", "watch", "status"}
SKILLS = {f"wily-{name}" for name in COMMANDS} | {"wily-execute"}


class V3SurfaceTest(unittest.TestCase):
    def test_plugin_manifest_exposes_v3_only(self) -> None:
        data = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["skills"], "./skills/")
        self.assertEqual(data["version"], "3.0.1")
        self.assertNotIn("board", json.dumps(data).lower())
        self.assertNotIn("stage", json.dumps(data).lower())

    def test_command_directories_are_exactly_v3(self) -> None:
        docs = {path.stem for path in (ROOT / "commands").glob("*.md")}
        self.assertEqual(docs, COMMANDS)

    def test_marketplace_points_to_plugin(self) -> None:
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        plugin = data["plugins"][0]
        self.assertEqual(plugin["source"]["path"], "./plugins/wily-roadmap")
        self.assertEqual(plugin["version"], "3.0.1")

    def test_skill_directories_are_exactly_v3(self) -> None:
        dirs = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(dirs, SKILLS)
        execute = (ROOT / "skills" / "wily-execute" / "SKILL.md").read_text(encoding="utf-8")
        for token in ("wily claim", "wily go", "custom-workflow-skillset:plan-goal-runner", "wily done"):
            self.assertIn(token, execute)

    def test_replan_skill_routes_natural_language_work_to_task_addition(self) -> None:
        replan = (ROOT / "skills" / "wily-replan" / "SKILL.md").read_text(encoding="utf-8")
        command = (ROOT / "commands" / "replan.md").read_text(encoding="utf-8")

        for text in (replan, command):
            with self.subTest(path="replan-contract"):
                self.assertIn("natural-language work request", text)
                self.assertIn("create or revise a Roadmap Task", text)
                self.assertIn("Do not implement the requested work", text)
                self.assertIn("stop after the task draft is committed", text)

    def test_watch_skill_documents_korean_ui_and_parallel_guidance(self) -> None:
        watch = (ROOT / "skills" / "wily-watch" / "SKILL.md").read_text(encoding="utf-8")
        command = (ROOT / "commands" / "watch.md").read_text(encoding="utf-8")

        for text in (watch, command):
            with self.subTest(path="watch-guidance"):
                self.assertIn("Korean UI", text)
                self.assertIn("병렬 가능", text)
                self.assertIn("scope conflict", text)
                self.assertIn("작업자 여력", text)

    def test_v2_runtime_files_are_removed(self) -> None:
        removed = {
            ROOT / "scripts" / "wily_state_summary.py",
            ROOT / "scripts" / "wily_watch_ui.py",
            ROOT / "scripts" / "wily_runner.py",
            ROOT / "scripts" / "wily_projection.py",
            ROOT / "tests" / "test_wily_cli.py",
            ROOT / "tests" / "test_wily_command_skills.py",
            ROOT / "tests" / "test_wily_state_summary.py",
            ROOT / "tests" / "test_wily_watch_ui.py",
        }
        for path in removed:
            with self.subTest(path=path):
                self.assertFalse(path.exists())

    def test_root_readme_documents_external_cleanup(self) -> None:
        readme = (ROOT.parents[1] / "README.md").read_text(encoding="utf-8")
        self.assertIn("~/.codex/hooks.json", readme)
        self.assertIn(".github/workflows/wily-" + "board-sync.yml", readme)
        self.assertIn("~/.wily/board.json", readme)

    def test_claude_user_prompt_hook_compat_script_allows_prompt(self) -> None:
        script = ROOT.parents[1] / "scripts" / "user_prompt_submit_goal_classifier.py"
        self.assertTrue(script.exists())
        result = subprocess.run(
            [sys.executable, str(script)],
            input='{"prompt":"v3 smoke"}',
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
