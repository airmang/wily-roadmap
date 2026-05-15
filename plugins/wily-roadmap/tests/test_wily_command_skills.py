from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


COMMANDS = {
    "wily-init": "scripts/wily.py init",
    "wily-status": "scripts/wily.py status",
    "wily-watch": "scripts/wily.py watch",
    "wily-issues": "scripts/wily.py issues",
    "wily-next": "scripts/wily.py next",
    "wily-start": "scripts/wily.py start",
    "wily-complete": "scripts/wily.py complete",
    "wily-block": "scripts/wily.py block",
    "wily-retry": "scripts/wily.py retry",
    "wily-replan": "scripts/wily.py replan",
    "wily-run": "scripts/wily.py run",
    "wily-decompose-stage": "scripts/wily.py decompose-stage",
    "wily-update": "scripts/wily.py update",
}

MUTATING_COMMANDS = {
    "wily-init",
    "wily-start",
    "wily-complete",
    "wily-block",
    "wily-retry",
    "wily-replan",
    "wily-run",
    "wily-decompose-stage",
    "wily-update",
}
READONLY_COMMANDS = {"wily-status", "wily-watch", "wily-issues", "wily-next"}
QUIET_RESPONSE_PHRASE = "Do not echo internal helper commands in normal user-facing responses."


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

    def test_command_skills_mark_helper_commands_as_internal(self) -> None:
        for command, helper in COMMANDS.items():
            with self.subTest(command=command):
                text = self.skill_text(command)
                self.assertIn("## Internal Command", text)
                self.assertIn(helper, text)
                self.assertIn(QUIET_RESPONSE_PHRASE, text)

    def test_command_skills_define_boundaries(self) -> None:
        mutating = {"wily-init", "wily-start", "wily-complete", "wily-block", "wily-retry", "wily-replan"}
        readonly = {"wily-status", "wily-watch", "wily-next"}
        for command in mutating:
            with self.subTest(command=command):
                self.assertIn("state-changing", self.skill_text(command))
        for command in readonly:
            with self.subTest(command=command):
                self.assertIn("read-only", self.skill_text(command))

    def test_state_changing_commands_report_only_result_artifact_and_next_action(self) -> None:
        required = (
            "Report only the result, the relevant path or artifact, and the next action or blocker.",
            "Keep safety-critical approval requirements when they apply.",
        )
        for command in MUTATING_COMMANDS:
            with self.subTest(command=command):
                text = self.skill_text(command)
                for phrase in required:
                    self.assertIn(phrase, text)

    def test_readonly_commands_keep_output_concise(self) -> None:
        required = (
            "Report only the requested roadmap output or concise answer.",
            "Avoid procedural narration before or after the result.",
        )
        for command in READONLY_COMMANDS:
            with self.subTest(command=command):
                text = self.skill_text(command)
                for phrase in required:
                    self.assertIn(phrase, text)

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
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertIn("codex", manifest["keywords"])
        self.assertIn("Claude Code", manifest["interface"]["longDescription"])
        self.assertIn("Codex plugin discovery", manifest["interface"]["longDescription"])
        prompts = manifest["interface"]["defaultPrompt"]
        joined = "\n".join(prompts)
        self.assertIn("$wily-init", joined)
        self.assertIn("$wily-status", joined)
        self.assertIn("$wily-issues", joined)
        self.assertIn("$wily-next", joined)
        self.assertIn("$wily-run", joined)
        self.assertIn("$wily-update", joined)

    def test_wily_update_documents_self_update_boundaries(self) -> None:
        skill = self.skill_text("wily-update")
        command = (ROOT / "commands" / "update.md").read_text(encoding="utf-8")

        self.assertIn("$wily-update", skill)
        self.assertIn("scripts/wily.py update", skill)
        self.assertIn("zip-based install", skill)
        self.assertIn("git-managed install", skill)
        self.assertIn("No background checks.", skill)
        self.assertIn("Remote actions remain approval-first.", skill)
        self.assertIn("Run the `wily-update` skill", command)
        self.assertIn("scripts/wily.py update", command)

    def test_wily_run_routes_to_custom_workflow_skillset_without_completion(self) -> None:
        skill = (ROOT / "skills" / "wily-run" / "SKILL.md").read_text(encoding="utf-8")
        command = (ROOT / "commands" / "run.md").read_text(encoding="utf-8")

        self.assertIn("$wily-run <phase-id> [--runner custom-workflow]", skill)
        self.assertIn("custom-workflow-skillset:plan-goal-runner", skill)
        self.assertIn("custom-workflow-skillset:parallel-lane-runner", skill)
        self.assertIn("custom-workflow-result.md", skill)
        self.assertIn("route into Custom Workflow Skillset", skill)
        self.assertIn("does not require bundled runner files", skill)
        self.assertNotIn("bundled default", skill)
        self.assertNotIn("runners/custom-workflow", skill)
        self.assertIn("Run the `wily-run` skill", command)
        self.assertIn("Custom Workflow Skillset", command)
        self.assertIn("custom-workflow-skillset:plan-goal-runner", command)

    def test_readme_documents_repo_local_zsh_launcher(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("zsh", readme)
        self.assertIn("./wily status", readme)
        self.assertIn("./wily watch", readme)
        self.assertIn("does not modify shell startup files", readme)
        self.assertIn("local-first", readme)

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

    def test_wily_init_documents_mature_repo_contract(self) -> None:
        text = self.skill_text("wily-init")
        self.assertIn("## Mature Repository Contract", text)
        self.assertIn("reports existing project hints", text)
        self.assertIn("repairs required directories", text)
        self.assertIn("preserve user-authored `project.md`, `roadmap.yaml`, `status.md`, and `decisions.md`", text)

    def test_wily_init_documents_stage_first_collaboration_authoring(self) -> None:
        text = self.skill_text("wily-init")
        self.assertIn("## Stage-First Roadmap Authoring", text)
        self.assertIn("Create top-level `stages:` entries, not top-level implementation `phases:`", text)
        self.assertIn("Use `depends_on` to make the Stage DAG explicit.", text)
        self.assertIn("Record `owner` and `write_scope` when collaboration or parallel work is expected.", text)
        self.assertIn("Do not create child Phases during init.", text)
        self.assertIn("$wily-decompose-stage", text)

    def test_workflow_docs_describe_stage_as_primary_collaboration_unit(self) -> None:
        paths = [
            ROOT / "skills" / "wily-workflow" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "references" / "routing-policy.md",
            ROOT / "skills" / "wily-workflow" / "references" / "planning-style.md",
            ROOT / "skills" / "wily-workflow" / "references" / "collaboration-policy.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Stage", text)
                self.assertIn("Phase", text)
                self.assertIn("write_scope", text)

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

    def test_workflow_documents_claude_code_compatibility(self) -> None:
        workflow = (ROOT / "skills" / "wily-workflow" / "SKILL.md").read_text(encoding="utf-8")
        compatibility = (
            ROOT / "skills" / "wily-workflow" / "references" / "agent-compatibility.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Agent compatibility", workflow)
        self.assertIn("references/agent-compatibility.md", workflow)
        self.assertIn("Claude Code", compatibility)
        self.assertIn("Use the `$wily-*` text commands as user-facing entrypoints.", compatibility)
        self.assertIn("Run `python3 <plugin-root>/scripts/wily.py <command>`", compatibility)
        self.assertIn("Keep Wily local-first and approval-first in every agent environment.", compatibility)

    def test_workflow_documents_github_issues_policy(self) -> None:
        workflow = (ROOT / "skills" / "wily-workflow" / "SKILL.md").read_text(encoding="utf-8")
        policy = (
            ROOT / "skills" / "wily-workflow" / "references" / "github-issues-policy.md"
        ).read_text(encoding="utf-8")

        self.assertIn("references/github-issues-policy.md", workflow)
        self.assertIn("GitHub Issues are optional", policy)
        self.assertIn("GitHub Issues are the collaboration source of truth", policy)
        self.assertIn("Wily is the roadmap and execution source of truth", policy)
        self.assertIn("Do not add unlinked issues to the roadmap without user approval.", policy)

    def test_live_skill_guidance_is_not_codex_only(self) -> None:
        paths = [
            ROOT / "skills" / "wily-init" / "SKILL.md",
            ROOT / "skills" / "wily-start" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "references" / "planning-style.md",
            ROOT / "skills" / "wily-workflow" / "references" / "routing-policy.md",
        ]
        forbidden = (
            "leaves Codex responsible",
            "fresh Codex session",
            "Codex-sized phases",
            "Codex still owns",
            "one focused Codex session",
            "Codex judgment",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_wily_watch_opens_tmux_pane_by_default(self) -> None:
        text = self.skill_text("wily-watch")
        self.assertIn("python3 <plugin-root>/scripts/wily.py watch --pane", text)
        self.assertIn("$wily-watch opens a tmux pane when already running inside tmux.", text)
        self.assertIn("targets the current pane from `TMUX_PANE` when available", text)
        self.assertIn("Outside tmux, `$wily-watch` runs the live dashboard in the current interactive terminal.", text)
        self.assertIn("In Codex app, open a side terminal and run `./wily watch`.", text)
        self.assertIn("Uses Rich when installed, otherwise falls back to ASCII.", text)
        self.assertIn("Run `$wily-watch --install-ui` to install the optional Rich UI dependency.", text)
        self.assertIn("leading fully completed stages collapse", text)
        self.assertIn("left-click the collapsed done-stage summary", text)
        self.assertIn("Right-click opens a tmux context menu.", text)
        self.assertIn("shared assignment metadata", text)
        self.assertIn("mouse wheel to scroll", text)
        self.assertIn("phases done across M stages", text)
        self.assertIn("unfinished, current, ready, and blocked phases stay visible", text)


if __name__ == "__main__":
    unittest.main()
