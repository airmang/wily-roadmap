from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "wily_state_summary.py"
sys.path.insert(0, str(ROOT / "scripts"))
import wily_state_summary  # noqa: E402


class WilyStateSummaryTest(unittest.TestCase):
    def run_summary(self, project: Path) -> str:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_reports_no_state_without_wily_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            output = self.run_summary(project)

        self.assertIn("상태 디렉터리: 없음", output)
        self.assertIn("Git: not a git repo", output)

    def test_summarizes_ready_and_blocked_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Ship release-ready app"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Audit current implementation"',
                        '    path: "phases/01-audit"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    parallel_group: null',
                        '',
                        '  - id: "02"',
                        '    title: "Core engine"',
                        '    path: "phases/02-core-engine"',
                        '    status: "ready"',
                        '    depends_on: ["01"]',
                        '    parallel_group: null',
                        '',
                        '  - id: "03"',
                        '    title: "Packaging"',
                        '    path: "phases/03-packaging"',
                        '    status: "blocked"',
                        '    depends_on: ["02"]',
                        '    parallel_group: null',
                        '    blocker: "Release certificate missing"',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("상태 디렉터리: .wily", output)
        self.assertIn("로드맵 버전: 1", output)
        self.assertIn("진행: 완료 1, 실행 가능 1, 진행 중 0, 차단 1, 대체됨 0", output)
        self.assertIn("다음 단계: 02 - Core engine", output)
        self.assertEqual(output.count("Roadmap:"), 1)
        self.assertNotIn("Phase 흐름:", output)
        self.assertIn("Stage 1:", output)
        self.assertIn("  [01 완료] Audit current implementation", output)
        self.assertIn("  |", output)
        self.assertIn("Stage 2:", output)
        self.assertIn("  [02 실행 가능] Core engine", output)
        self.assertIn("Stage 3:", output)
        self.assertIn("  [03 차단] Packaging", output)
        self.assertIn("    의존: 02", output)
        self.assertIn("실행 가능 단계:", output)
        self.assertIn("  - 02 Core engine", output)
        self.assertIn("차단된 단계:", output)
        self.assertIn("  - 03 Packaging (의존: 02)", output)
        self.assertIn("    blocker: Release certificate missing", output)

    def test_treats_pending_phases_with_completed_dependencies_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
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
                        '',
                        '  - id: "03"',
                        '    title: "Future packaging"',
                        '    path: "phases/03-future-packaging"',
                        '    status: "pending"',
                        '    depends_on: ["02"]',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("진행: 완료 1, 실행 가능 1, 진행 중 0, 차단 0, 대체됨 0", output)
        self.assertIn("다음 단계: 02 - Next layer", output)
        self.assertEqual(output.count("Roadmap:"), 1)
        self.assertNotIn("Phase 흐름:", output)
        self.assertIn("  [02 실행 가능] Next layer", output)
        self.assertIn("    의존: 01", output)
        self.assertIn("실행 가능 단계:", output)
        self.assertIn("  - 02 Next layer", output)
        self.assertNotIn("  - 03 Future packaging", output)

    def test_groups_parallel_phases_by_dependency_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Foundation"',
                        '    path: "phases/01-foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '',
                        '  - id: "02"',
                        '    title: "Command consistency"',
                        '    path: "phases/02-command-consistency"',
                        '    status: "done"',
                        '    depends_on: ["01"]',
                        '',
                        '  - id: "03"',
                        '    title: "Status output"',
                        '    path: "phases/03-status-output"',
                        '    status: "done"',
                        '    depends_on: ["02"]',
                        '',
                        '  - id: "04-1"',
                        '    title: "Improve init roadmap authoring"',
                        '    path: "phases/04-1-improve-init-roadmap-authoring"',
                        '    status: "pending"',
                        '    depends_on: ["03"]',
                        '    parallel_group: "04"',
                        '',
                        '  - id: "04-2"',
                        '    title: "Harden lifecycle status CLI"',
                        '    path: "phases/04-2-harden-lifecycle-status-cli"',
                        '    status: "pending"',
                        '    depends_on: ["03"]',
                        '    parallel_group: "04"',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("Stage 4:", output)
        self.assertIn(
            "  +--> [04-1 실행 가능] Improve init roadmap authoring",
            output,
        )
        self.assertIn("  |", output)
        self.assertIn(
            "  +--> [04-2 실행 가능] Harden lifecycle status CLI",
            output,
        )
        self.assertIn("    병렬: 04", output)

    def test_shows_multi_dependency_without_tree_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'phases:',
                        '  - id: "03"',
                        '    title: "Status output"',
                        '    path: "phases/03-status-output"',
                        '    status: "done"',
                        '    depends_on: []',
                        '',
                        '  - id: "04-1"',
                        '    title: "Init authoring"',
                        '    path: "phases/04-1-init-authoring"',
                        '    status: "done"',
                        '    depends_on: ["03"]',
                        '    parallel_group: "04"',
                        '',
                        '  - id: "04-2"',
                        '    title: "Lifecycle CLI"',
                        '    path: "phases/04-2-lifecycle-cli"',
                        '    status: "done"',
                        '    depends_on: ["03"]',
                        '    parallel_group: "04"',
                        '',
                        '  - id: "05"',
                        '    title: "Plugin discovery and release polish"',
                        '    path: "phases/05-plugin-discovery-release-polish"',
                        '    status: "pending"',
                        '    depends_on: ["04-1", "04-2"]',
                        '    parallel_group: null',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("Stage 3:", output)
        self.assertIn(
            "  [05 실행 가능] Plugin discovery and release polish",
            output,
        )
        self.assertIn("    의존: 04-1, 04-2", output)
        self.assertIn("    ^-- 04-1", output)
        self.assertIn("    ^-- 04-2", output)

    def test_summarizes_superseded_replacement_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'phases:',
                        '  - id: "04"',
                        '    title: "Old integration plan"',
                        '    path: "phases/04-old-integration"',
                        '    status: "superseded"',
                        '    depends_on: ["03"]',
                        '    parallel_group: null',
                        '',
                        '  - id: "04R"',
                        '    title: "Adapt foundation"',
                        '    path: "phases/04r-adapt-foundation"',
                        '    status: "ready"',
                        '    depends_on: ["03"]',
                        '    replaces: ["04"]',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("로드맵 버전: 2", output)
        self.assertIn("다음 단계: 04R - Adapt foundation", output)
        self.assertIn("대체:", output)
        self.assertIn("  - 04R 대체: 04", output)
        self.assertIn("대체된 단계:", output)
        self.assertIn("  - 04 Old integration plan", output)

    def test_parse_roadmap_preserves_folded_block_scalar(self) -> None:
        roadmap = wily_state_summary.parse_roadmap(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'phases:',
                    '  - id: "01"',
                    '    title: "Block scalar phase"',
                    '    status: "pending"',
                    '    summary: >-',
                    '      First sentence',
                    '      continues here.',
                ]
            )
        )

        self.assertEqual(
            roadmap["phases"][0]["summary"],
            "First sentence continues here.",
        )

    def test_parse_roadmap_preserves_literal_block_scalar(self) -> None:
        roadmap = wily_state_summary.parse_roadmap(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'phases:',
                    '  - id: "01"',
                    '    title: "Literal scalar phase"',
                    '    status: "pending"',
                    '    summary: |',
                    '      Line one',
                    '      Line two',
                ]
            )
        )

        self.assertEqual(roadmap["phases"][0]["summary"], "Line one\nLine two\n")

    def test_parse_roadmap_preserves_phase_block_list(self) -> None:
        roadmap = wily_state_summary.parse_roadmap(
            "\n".join(
                [
                    'roadmap_version: 1',
                    'phases:',
                    '  - id: "01"',
                    '    title: "Foundation"',
                    '    status: "done"',
                    '    depends_on: []',
                    '  - id: "02"',
                    '    title: "Block list phase"',
                    '    status: "pending"',
                    '    depends_on:',
                    '      - "01"',
                ]
            )
        )

        self.assertEqual(len(roadmap["phases"]), 2)
        self.assertEqual(roadmap["phases"][1]["depends_on"], ["01"])


if __name__ == "__main__":
    unittest.main()
