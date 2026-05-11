from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


COMMANDS = {
    "wily-init": "scripts/wily.py init",
    "wily-status": "scripts/wily.py status",
    "wily-next": "scripts/wily.py next",
    "wily-start": "scripts/wily.py start",
    "wily-complete": "scripts/wily.py complete",
    "wily-block": "scripts/wily.py block",
    "wily-retry": "scripts/wily.py retry",
    "wily-replan": "scripts/wily.py replan",
}


class WilyCommandSkillsTest(unittest.TestCase):
    def skill_text(self, command: str) -> str:
        path = ROOT / "skills" / command / "SKILL.md"
        self.assertTrue(path.is_file(), f"Missing {path}")
        return path.read_text(encoding="utf-8")

    def test_command_skill_files_exist_with_matching_names(self) -> None:
        for command in COMMANDS:
            with self.subTest(command=command):
                text = self.skill_text(command)
                self.assertIn(f"name: {command}", text)
                self.assertIn(f"${command}", text)

    def test_command_skills_reference_helper_commands(self) -> None:
        for command, helper in COMMANDS.items():
            with self.subTest(command=command):
                text = self.skill_text(command)
                self.assertIn(helper, text)

    def test_command_skills_define_boundaries(self) -> None:
        mutating = {"wily-init", "wily-start", "wily-complete", "wily-block", "wily-retry", "wily-replan"}
        readonly = {"wily-status", "wily-next"}
        for command in mutating:
            with self.subTest(command=command):
                self.assertIn("state-changing", self.skill_text(command))
        for command in readonly:
            with self.subTest(command=command):
                self.assertIn("read-only", self.skill_text(command))

    def test_plugin_default_prompts_use_command_entrypoints(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        prompts = manifest["interface"]["defaultPrompt"]
        joined = "\n".join(prompts)
        self.assertIn("$wily-init", joined)
        self.assertIn("$wily-status", joined)
        self.assertIn("$wily-next", joined)


if __name__ == "__main__":
    unittest.main()
