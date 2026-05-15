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

    def test_digit_style_legacy_phase_roadmap_remains_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Roblox planet digging collaboration"',
                        'phases:',
                        '  - id: "p00-foundation"',
                        '    title: "프로젝트 셋업과 공통 인터페이스 (완료)"',
                        '    status: "done"',
                        '    lead: "shared"',
                        '    depends_on: []',
                        '    path: "phases/p00-foundation"',
                        '    summary: "Rojo 7 골격, 공통 모듈, 데이터 스키마 5종."',
                        '    current_session: "sessions/2026-05-15-003641-phase-phase-00-foundation-attempt-1"',
                        '',
                        '  - id: "p01-wily-hit-core"',
                        '    title: "MVP 0-A 타격 / EXP / 레벨 코어 (Wily 단독)"',
                        '    status: "pending"',
                        '    lead: "wily"',
                        '    depends_on: ["p00-foundation"]',
                        '    path: "phases/p01-wily-hit-core"',
                        '    summary: "타격 입력·서버 검증·EXP·레벨업·HUD를 한 사람이 끝낸다."',
                        '',
                        '  - id: "p02-right-terrain"',
                        '    title: "MVP 0-B 지형 / 파괴 / 깊이 (Right 단독)"',
                        '    status: "pending"',
                        '    lead: "right"',
                        '    depends_on: ["p01-wily-hit-core"]',
                        '    path: "phases/p02-right-terrain"',
                        '    parallel_group: "after-p01"',
                        '    summary: "4x4x4 블록 그리드와 깊이 계산."',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("로드맵 버전: 1", output)
        self.assertIn("진행: 완료 1, 실행 가능 1", output)
        self.assertIn("다음 단계: p01-wily-hit-core - MVP 0-A 타격 / EXP / 레벨 코어 (Wily 단독)", output)
        self.assertIn("  - p01-wily-hit-core MVP 0-A 타격 / EXP / 레벨 코어 (Wily 단독)", output)
        self.assertNotIn("Stage decomposition required", output)

    def test_stage_roadmap_treats_pending_stage_with_done_dependency_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'goal: "Ship with Stage first planning"',
                        'stages:',
                        '  - id: "s00-foundation"',
                        '    title: "Foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    path: "stages/s00-foundation"',
                        '    execution_mode: "direct"',
                        '',
                        '  - id: "s01-mvp0"',
                        '    title: "MVP 0 loop"',
                        '    status: "pending"',
                        '    depends_on: ["s00-foundation"]',
                        '    path: "stages/s01-mvp0"',
                        '    execution_mode: "direct"',
                        '    decomposition_status: "none"',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("진행: 완료 1, 실행 가능 1", output)
        self.assertIn("다음 단계: s01-mvp0 - MVP 0 loop", output)
        self.assertIn("Stage Roadmap:", output)
        self.assertIn("  [s01-mvp0 실행 가능] MVP 0 loop", output)

    def test_stage_summary_lists_parallel_ready_stage_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".wily").mkdir()
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 2',
                        'stages:',
                        '  - id: "s00-foundation"',
                        '    title: "Foundation"',
                        '    status: "done"',
                        '    depends_on: []',
                        '    path: "stages/s00-foundation"',
                        '    execution_mode: "direct"',
                        '',
                        '  - id: "s01-wily-hit"',
                        '    title: "Wily hit loop"',
                        '    status: "pending"',
                        '    owner: "wily"',
                        '    depends_on: ["s00-foundation"]',
                        '    path: "stages/s01-wily-hit"',
                        '    write_scope: ["src/server/HitService.lua"]',
                        '    execution_mode: "direct"',
                        '',
                        '  - id: "s02-right-terrain"',
                        '    title: "Right terrain"',
                        '    status: "pending"',
                        '    owner: "right"',
                        '    depends_on: ["s00-foundation"]',
                        '    path: "stages/s02-right-terrain"',
                        '    write_scope: ["src/server/world"]',
                        '    execution_mode: "direct"',
                    ]
                ),
                encoding="utf-8",
            )

            output = self.run_summary(project)

        self.assertIn("병렬 가능 Stage 후보:", output)
        self.assertIn("  - s01-wily-hit @wily", output)
        self.assertIn("  - s02-right-terrain @right", output)
        self.assertIn("write_scope 겹침 없음", output)

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
