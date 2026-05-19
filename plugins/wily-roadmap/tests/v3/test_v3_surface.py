from __future__ import annotations

import json
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT.parents[1] / ".agents" / "plugins" / "marketplace.json"

COMMANDS = {"init", "next", "claim", "go", "done", "block", "replan", "land", "watch", "status", "cp", "agent"}
SKILLS = {f"wily-{name}" for name in COMMANDS} | {"wily-execute"}


class V3SurfaceTest(unittest.TestCase):
    def test_plugin_manifest_exposes_v3_only(self) -> None:
        data = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["skills"], "./skills/")
        self.assertEqual(data["version"], "3.0.1")
        manifest_text = json.dumps(data).lower()
        self.assertNotIn("stage", manifest_text)
        self.assertNotIn("wily-" + "board-sync", manifest_text)
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

    def test_agent_command_and_skill_surface_are_declared(self) -> None:
        command = (ROOT / "commands" / "agent.md").read_text(encoding="utf-8")
        skill = (ROOT / "skills" / "wily-agent" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("wily-agent", command)
        for token in ("install", "configure", "start", "stop", "status", "check", "launchd", "foreground"):
            self.assertIn(token, skill)
        for token in ("$wily-agent install", "$wily-agent start", "Do not ask the user to find the plugin root"):
            self.assertIn(token, skill)
        self.assertIn("local-first", skill)
        self.assertIn("approval-first", skill)

    def test_plugin_manifest_and_readme_document_agent_onboarding(self) -> None:
        data = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        prompt = "\n".join(data["interface"]["defaultPrompt"])
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("$wily-agent", prompt)
        for token in ("wily agent login", "wily agent install", "wily agent start", "wily agent status", "wily agent check"):
            self.assertIn(token, readme)

    def test_readme_documents_v3_board_reflection_contract(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("snapshots and heartbeats", readme)
        self.assertIn("live-*` commands are not a Wily Board v3 reflection mechanism", readme)
        self.assertIn("wily cp", readme)

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

    def test_custom_workflow_checkpoint_contract_uses_wily_cp(self) -> None:
        go = (ROOT / "skills" / "wily-go" / "SKILL.md").read_text(encoding="utf-8")
        execute = (ROOT / "skills" / "wily-execute" / "SKILL.md").read_text(encoding="utf-8")
        cp = (ROOT / "skills" / "wily-cp" / "SKILL.md").read_text(encoding="utf-8")
        command = (ROOT / "commands" / "cp.md").read_text(encoding="utf-8")

        for text in (go, execute, cp, command):
            with self.subTest(path="cp-contract"):
                self.assertIn("wily cp", text)
                self.assertIn("import-status", text)
                self.assertIn("progress.jsonl", text)

    def test_goal_text_uses_ordered_cp_checklist(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from wily.cli.go import goal_text
            from wily.models import Task
            from wily.paths import WilyPaths

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                text = goal_text(root, WilyPaths(root), Task(id="T99", title="Demo", scope=["src/demo.py"]), acceptance="done")

            self.assertIn("- [ ] 1. Start checkpoint: `wily cp T99 start <cp-name>`", text)
            self.assertIn("- [ ] 2. Finish checkpoint after verification: `wily cp T99 done <cp-name>`", text)
            self.assertIn("- [ ] 3. Backfill if needed: `wily cp T99 import-status`", text)
            self.assertIn(".wily/handoffs/T99/status.md", text)
            self.assertIn("Custom Workflow interface contract", text)
        finally:
            sys.path.pop(0)

    def test_wily_execute_documents_cp_automation_gap_and_import_backfill(self) -> None:
        execute = (ROOT / "skills" / "wily-execute" / "SKILL.md").read_text(encoding="utf-8")
        go = (ROOT / "skills" / "wily-go" / "SKILL.md").read_text(encoding="utf-8")
        cp = (ROOT / "skills" / "wily-cp" / "SKILL.md").read_text(encoding="utf-8")

        for text in (execute, go, cp):
            with self.subTest(skill="cp-contract"):
                self.assertIn("Custom Workflow interface contract", text)
                self.assertIn("cp automation gap", text)
                self.assertIn("wily cp <id> import-status", text)
                self.assertIn(".wily/handoffs/<id>/status.md", text)

    def test_custom_workflow_checkpoint_contract_is_explicit(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from pathlib import Path
            from wily.cli.go import goal_text
            from wily.models import Task
            from wily.paths import WilyPaths

            text = goal_text(
                Path("/tmp/demo"),
                WilyPaths(Path("/tmp/demo")),
                Task(id="T01", title="First", intent="do it", acceptance="done"),
                acceptance="done",
            )
        finally:
            sys.path.pop(0)

        self.assertIn("- [ ] Before each checkpoint: run `wily cp T01 start <cp-name>`", text)
        self.assertIn("- [ ] After checkpoint verification passes: run `wily cp T01 done <cp-name>`", text)
        self.assertIn("- [ ] If a custom-workflow status board already exists: run `wily cp T01 import-status", text)

        execute = (ROOT / "skills" / "wily-execute" / "SKILL.md").read_text(encoding="utf-8")
        go = (ROOT / "skills" / "wily-go" / "SKILL.md").read_text(encoding="utf-8")
        cp = (ROOT / "skills" / "wily-cp" / "SKILL.md").read_text(encoding="utf-8")
        for text in (execute, go, cp):
            with self.subTest(path="cp-gap-contract"):
                self.assertIn("custom-workflow does not update Wily by itself", text)
                self.assertIn(".wily/handoffs/<task-id>/status.md", text)
                self.assertIn("interface contract", text)

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

    def test_command_help_surfaces_usage_and_options(self) -> None:
        script = ROOT / "scripts" / "wily.py"

        result = subprocess.run(
            [sys.executable, str(script), "help", "claim"],
            cwd=ROOT.parents[1],
            env={**os.environ, "WILY_LOCALE": "en"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: wily claim <task-id>", result.stdout)
        self.assertIn("--allow-empty", result.stdout)
        self.assertIn("transition a task into progress", result.stdout)

        result = subprocess.run(
            [sys.executable, str(script), "done", "--help"],
            cwd=ROOT.parents[1],
            env={**os.environ, "WILY_LOCALE": "en"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: wily done <task-id>", result.stdout)
        self.assertIn("--ac-check", result.stdout)

    def test_command_modules_declare_help_metadata(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            for command in COMMANDS:
                with self.subTest(command=command):
                    module = __import__(f"wily.cli.{command}", fromlist=["DESCRIPTION", "USAGE"])
                    self.assertTrue(getattr(module, "DESCRIPTION").strip())
                    self.assertTrue(getattr(module, "USAGE").startswith(f"usage: wily {command}"))
        finally:
            sys.path.pop(0)

    def test_i18n_selects_default_korean_and_english_locale(self) -> None:
        script = ROOT / "scripts" / "wily.py"

        korean = subprocess.run(
            [sys.executable, str(script), "help", "claim"],
            cwd=ROOT.parents[1],
            env={key: value for key, value in os.environ.items() if key != "WILY_LOCALE"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(korean.returncode, 0, korean.stderr)
        self.assertIn("사용법", korean.stdout)
        self.assertIn("태스크를 진행 중으로 전환", korean.stdout)

        english = subprocess.run(
            [sys.executable, str(script), "help", "claim"],
            cwd=ROOT.parents[1],
            env={**os.environ, "WILY_LOCALE": "en"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(english.returncode, 0, english.stderr)
        self.assertIn("Usage", english.stdout)
        self.assertIn("transition a task into progress", english.stdout)

    def test_removed_command_keys_are_plain_strings(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from wily.cli._common import REMOVED_COMMANDS

            self.assertIn("live-worked", REMOVED_COMMANDS)
            self.assertIn("live-heartbeat", REMOVED_COMMANDS)
            self.assertIn("live-event", REMOVED_COMMANDS)
            self.assertIn("board", REMOVED_COMMANDS)
            self.assertIn("decompose-stage", REMOVED_COMMANDS)
        finally:
            sys.path.pop(0)

    def test_cli_flag_helpers_live_in_common_only(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from wily.cli import _common

            self.assertEqual(_common.extract_value(["T1", "--note", "done"], "--note"), "done")
            self.assertEqual(_common.extract_value(["T1", "--note=done"], "--note"), "done")
            self.assertEqual(_common.extract_values(["--ac-check", "1=pass", "--ac-check=2=fail"], "--ac-check"), ["1=pass", "2=fail"])
            self.assertEqual(_common.missing_value_flag(["T1", "--note", "--json"], {"--note"}), "--note")
            self.assertEqual(_common.positionals(["T1", "--note", "done", "--json"], value_flags={"--note"}), ["T1"])
            cleaned, as_json = _common.consume_json_flag(["--json", "T1", "--note", "done"])
            self.assertTrue(as_json)
            self.assertEqual(cleaned, ["T1", "--note", "done"])

            for command in ("done", "cp", "claim"):
                with self.subTest(command=command):
                    module = __import__(f"wily.cli.{command}", fromlist=["main"])
                    names = {name for name, value in inspect.getmembers(module, inspect.isfunction)}
                    self.assertFalse({"_extract_value", "_missing_value_flag", "_positionals"} & names)
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
