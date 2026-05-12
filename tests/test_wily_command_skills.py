from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


COMMANDS = {
    "wily-init": "scripts/wily.py init",
    "wily-status": "scripts/wily.py status",
    "wily-watch": "scripts/wily.py watch",
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
        readonly = {"wily-status", "wily-watch", "wily-next"}
        for command in mutating:
            with self.subTest(command=command):
                self.assertIn("state-changing", self.skill_text(command))
        for command in readonly:
            with self.subTest(command=command):
                self.assertIn("read-only", self.skill_text(command))

    def test_command_skills_do_not_invoke_external_planners_or_test_runners(self) -> None:
        forbidden = (
            "superpowers:",
            "writing-plans",
            "test-driven",
            "TDD",
            "pytest",
            "python3 -m unittest",
            "npm test",
            "cargo test",
            "go test",
            "Use the recommended planner",
        )
        for command in COMMANDS:
            text = self.skill_text(command)
            for phrase in forbidden:
                with self.subTest(command=command, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_wily_start_is_only_session_bookkeeping(self) -> None:
        text = self.skill_text("wily-start")
        required = (
            "$wily-start is session bookkeeping only.",
            "Do not create or update implementation plans.",
            "Do not edit phase target files.",
            "Do not run verification for the phase implementation.",
            "Do not continue into implementation in the same turn.",
            "A separate explicit user request after the start result is required before implementation.",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_plugin_default_prompts_use_command_entrypoints(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "wily-roadmap")
        self.assertEqual(manifest["interface"]["displayName"], "Wily Roadmap")
        prompts = manifest["interface"]["defaultPrompt"]
        joined = "\n".join(prompts)
        self.assertIn("$wily-init", joined)
        self.assertIn("$wily-status", joined)
        self.assertIn("$wily-next", joined)

    def test_skill_frontmatter_quotes_colon_values(self) -> None:
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), f"Missing frontmatter start in {path}")
                _start, frontmatter, _body = text.split("---", 2)
                for line in frontmatter.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or ":" not in stripped:
                        continue
                    _key, value = stripped.split(":", 1)
                    value = value.strip()
                    if ": " in value:
                        self.assertTrue(
                            value.startswith(('"', "'")),
                            f"Frontmatter value containing ': ' must be quoted in {path}: {stripped}",
                        )

    def test_wily_skills_prefer_korean_announcements_for_korean_users(self) -> None:
        expected = (
            "When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean."
        )
        for path in sorted((ROOT / "skills").glob("wily-*/SKILL.md")):
            with self.subTest(path=path):
                self.assertIn(expected, path.read_text(encoding="utf-8"))

    def test_wily_init_authors_roadmaps_in_korean_by_default(self) -> None:
        text = self.skill_text("wily-init")
        self.assertIn(
            "Unless the user explicitly asks for another language, author Roadmap Plan content in Korean.",
            text,
        )
        self.assertIn("Keep YAML field names and status values in English", text)

    def test_wily_status_response_shows_phase_flow_verbatim(self) -> None:
        text = self.skill_text("wily-status")
        self.assertIn("Include the `Wily Roadmap` pane output verbatim in the user response.", text)
        self.assertIn("Do not replace the visual roadmap pane with a prose-only summary.", text)

    def test_workflow_docs_describe_status_pane_not_old_phase_flow(self) -> None:
        paths = [
            ROOT / "skills" / "wily-workflow" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "references" / "planning-style.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Wily Roadmap", text)
                self.assertNotIn("Phase 흐름:", text)

    def test_wily_watch_opens_tmux_pane_by_default(self) -> None:
        text = self.skill_text("wily-watch")
        self.assertIn("python3 <plugin-root>/scripts/wily.py watch --pane", text)
        self.assertIn("$wily-watch opens a tmux pane by default.", text)
        self.assertIn("Use `--here` only when the user asks to run watch in the current pane.", text)
        self.assertIn("Uses Rich when installed, otherwise falls back to ASCII.", text)
        self.assertIn("Run `$wily-watch --install-ui` to install the optional Rich UI dependency.", text)


if __name__ == "__main__":
    unittest.main()
