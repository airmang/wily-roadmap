from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wily_watch_ui

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _write_roadmap(project: Path, body: str) -> None:
    state = project / ".wily"
    state.mkdir(parents=True, exist_ok=True)
    (state / "roadmap.yaml").write_text(body, encoding="utf-8")


class LoadTest(unittest.TestCase):
    def test_load_none_without_wily_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            view = wily_watch_ui._load(Path(tmp))
            self.assertIsNone(view.roadmap)
            self.assertFalse(view.has_state)

    def test_load_none_roadmap_when_state_exists_without_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".wily").mkdir()
            view = wily_watch_ui._load(Path(tmp))
            self.assertTrue(view.has_state)
            self.assertIsNone(view.roadmap)

    def test_load_parses_phases_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_roadmap(Path(tmp), "\n".join([
                'roadmap_version: 2',
                'phases:',
                '  - id: "01"',
                '    title: "A"',
                '    status: "done"',
                '    depends_on: []',
                '  - id: "02"',
                '    title: "B"',
                '    status: "pending"',
                '    depends_on: ["01"]',
            ]))
            view = wily_watch_ui._load(Path(tmp))
            self.assertEqual(view.version, 2)
            self.assertEqual(len(view.phases), 2)
            self.assertEqual(view.done, 1)
            self.assertEqual(view.total, 2)
            self.assertEqual({str(p["id"]) for p in view.ready}, {"02"})
            self.assertEqual(set(view.by_id), {"01", "02"})


class TruncateAndEmitTest(unittest.TestCase):
    def test_truncate_keeps_short_text(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abc", 10), "abc")

    def test_truncate_crops_with_ellipsis(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abcdefgh", 5), "abcd…")

    def test_truncate_handles_tiny_limits(self) -> None:
        self.assertEqual(wily_watch_ui._truncate("abcdef", 1), "…")
        self.assertEqual(wily_watch_ui._truncate("abcdef", 0), "")

    def test_emit_plain_text_strips_empty_spans(self) -> None:
        self.assertEqual(
            wily_watch_ui._emit(
                [[(" hello", ""), ("  ", "")], [(" world", "bold")]],
                rich=False,
                width=20,
            ),
            " hello\n world",
        )


class ChromeTest(unittest.TestCase):
    def test_header_left_and_right_within_width(self) -> None:
        line = wily_watch_ui._header_line(version=2, interval=2.0, width=40, ascii_=True)
        text = "".join(span for span, _style in line)
        self.assertEqual(len(text), 40)
        self.assertTrue(text.startswith(" Wily Roadmap"))
        self.assertIn("v2", text)
        self.assertTrue(text.rstrip().endswith("~ 2s"))

    def test_progress_bar_half_full(self) -> None:
        line = wily_watch_ui._progress_line(done=3, total=6, width=40, ascii_=True)
        text = "".join(span for span, _style in line)
        self.assertIn("3/6", text)
        self.assertIn("50%", text)
        self.assertIn("#", text)
        self.assertIn("-", text)

    def test_progress_zero_total(self) -> None:
        line = wily_watch_ui._progress_line(done=0, total=0, width=40, ascii_=True)
        text = "".join(span for span, _style in line)
        self.assertIn("0/0", text)
        self.assertIn("0%", text)

    def test_footer_clean_and_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            line = wily_watch_ui._footer_line(Path(tmp), width=60, ascii_=True)
            text = "".join(span for span, _style in line)
            self.assertIn("git:", text)
            self.assertIn(Path(tmp).name, text)
            self.assertIn("^C to stop", text)

    def test_header_tiny_width_does_not_exceed_width(self) -> None:
        line = wily_watch_ui._header_line(version=2, interval=2.0, width=12, ascii_=True)
        text = "".join(span for span, _style in line)
        self.assertLessEqual(len(text), 12)

    def test_footer_tiny_width_does_not_exceed_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            line = wily_watch_ui._footer_line(Path(tmp), width=12, ascii_=True)
            text = "".join(span for span, _style in line)
            self.assertLessEqual(len(text), 12)


class NodeLineTest(unittest.TestCase):
    def _phases(self):
        return [
            {"id": "01", "title": "Settle Korean response-style update", "status": "done", "depends_on": []},
            {"id": "02", "title": "Harden command skill consistency", "status": "in_progress", "depends_on": ["01"]},
            {"id": "04-1", "title": "Improve init roadmap authoring", "status": "pending", "depends_on": ["03"]},
            {"id": "03", "title": "Korean stage-based DAG status output", "status": "done", "depends_on": ["02"]},
        ]

    def test_status_ready_when_id_is_executable(self) -> None:
        phase = self._phases()[2]

        self.assertEqual(wily_watch_ui._phase_status(phase, {"04-1"}), "ready")

    def test_status_from_field_otherwise(self) -> None:
        phase = self._phases()[1]

        self.assertEqual(wily_watch_ui._phase_status(phase, set()), "in_progress")

    def test_unmet_deps_lists_non_done_or_missing(self) -> None:
        by_id = wily_watch_ui._phase_index(self._phases())

        self.assertEqual(
            wily_watch_ui._unmet_deps({"depends_on": ["01", "02", "missing"]}, by_id),
            ["02", "missing"],
        )
        self.assertEqual(wily_watch_ui._unmet_deps({"depends_on": ["01"]}, by_id), [])

    def test_unmet_deps_treats_none_as_empty(self) -> None:
        by_id = wily_watch_ui._phase_index(self._phases())

        self.assertEqual(wily_watch_ui._unmet_deps({"depends_on": None}, by_id), [])

    def test_node_line_plain_done(self) -> None:
        phases = self._phases()
        by_id = wily_watch_ui._phase_index(phases)

        line = wily_watch_ui._node_line(
            phases[0],
            set(),
            by_id,
            prefix=" ",
            id_width=4,
            width=80,
            ascii_=True,
        )
        text = "".join(span for span, _style in line)

        self.assertTrue(text.startswith(" * 01"))
        self.assertIn("Settle Korean response-style update", text)

    def test_node_line_pending_shows_unmet_deps(self) -> None:
        phases = self._phases()
        by_id = wily_watch_ui._phase_index(phases)
        by_id["03"]["status"] = "pending"

        line = wily_watch_ui._node_line(
            by_id["04-1"],
            set(),
            by_id,
            prefix=" +--",
            id_width=4,
            width=80,
            ascii_=True,
        )
        text = "".join(span for span, _style in line)

        self.assertTrue(text.startswith(" +--o 04-1  Improve init roadmap authoring"))
        self.assertIn("needs 03", text)

    def test_node_line_rich_path_pending_shows_unmet_deps_label(self) -> None:
        phases = self._phases()
        by_id = wily_watch_ui._phase_index(phases)
        by_id["03"]["status"] = "pending"

        line = wily_watch_ui._node_line(
            by_id["04-1"],
            set(),
            by_id,
            prefix=" ├──",
            id_width=4,
            width=80,
            ascii_=False,
        )
        text = "".join(span for span, _style in line)

        self.assertIn("needs 03", text)

    def test_node_line_truncates_to_width(self) -> None:
        phases = self._phases()
        by_id = wily_watch_ui._phase_index(phases)

        line = wily_watch_ui._node_line(
            phases[0],
            set(),
            by_id,
            prefix=" ",
            id_width=2,
            width=20,
            ascii_=True,
        )
        text = "".join(span for span, _style in line)

        self.assertLessEqual(len(text), 20)
        self.assertTrue(text.endswith("…"))

    def test_node_line_truncates_when_fixed_parts_exceed_width(self) -> None:
        phase = {"id": "very-long-id", "title": "Title", "status": "pending", "depends_on": ["missing"]}

        line = wily_watch_ui._node_line(
            phase,
            set(),
            {},
            prefix=" +--",
            id_width=len("very-long-id"),
            width=10,
            ascii_=True,
        )
        text = "".join(span for span, _style in line)

        self.assertLessEqual(len(text), 10)


class GraphTest(unittest.TestCase):
    linear = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "ready", "depends_on": ["02"]},
    ]
    fan = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "done", "depends_on": ["02"]},
        {"id": "04-1", "title": "D1", "status": "pending", "depends_on": ["03"]},
        {"id": "04-2", "title": "D2", "status": "pending", "depends_on": ["03"]},
        {"id": "05", "title": "E", "status": "pending", "depends_on": ["04-1", "04-2"]},
    ]
    skip = [
        {"id": "01", "title": "A", "status": "done", "depends_on": []},
        {"id": "02", "title": "B", "status": "done", "depends_on": ["01"]},
        {"id": "03", "title": "C", "status": "done", "depends_on": ["02"]},
        {"id": "05", "title": "E", "status": "pending", "depends_on": ["03", "01"]},
    ]
    two_wide = [
        {"id": "a1", "title": "A1", "status": "done", "depends_on": []},
        {"id": "a2", "title": "A2", "status": "done", "depends_on": []},
        {"id": "b1", "title": "B1", "status": "pending", "depends_on": ["a1", "a2"]},
        {"id": "b2", "title": "B2", "status": "pending", "depends_on": ["a1", "a2"]},
    ]
    initial_fan_in = [
        {"id": "a1", "title": "A1", "status": "done", "depends_on": []},
        {"id": "a2", "title": "A2", "status": "done", "depends_on": []},
        {"id": "b", "title": "B", "status": "pending", "depends_on": ["a1", "a2"]},
    ]

    def test_renderable_true_for_linear_and_fan(self) -> None:
        self.assertTrue(wily_watch_ui._pipeline_renderable(self.linear))
        self.assertTrue(wily_watch_ui._pipeline_renderable(self.fan))

    def test_not_renderable_for_skip_level_or_consecutive_wide(self) -> None:
        self.assertFalse(wily_watch_ui._pipeline_renderable(self.skip))
        self.assertFalse(wily_watch_ui._pipeline_renderable(self.two_wide))

    def test_graph_lines_linear_uses_link_rail(self) -> None:
        lines = wily_watch_ui._graph_lines(self.linear, set(), width=60, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in lines]

        self.assertEqual(rendered[0], " * 01  A")
        self.assertEqual(rendered[1], " |")
        self.assertEqual(rendered[2], " * 02  B")
        self.assertEqual(rendered[3], " |")
        self.assertTrue(rendered[4].startswith(" > 03  C"))

    def test_graph_lines_fan_uses_branch_and_merge(self) -> None:
        lines = wily_watch_ui._graph_lines(self.fan, set(), width=70, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in lines]

        self.assertTrue(any(line.startswith(" +--o 04-1") and line.endswith("D1") for line in rendered))
        self.assertTrue(any(line.startswith(" +--o 04-2") and line.endswith("D2") for line in rendered))
        self.assertIn(" v", rendered)
        self.assertTrue(any(line.lstrip().startswith("o 05") and "deps 04-1 04-2" in line for line in rendered))

    def test_graph_lines_rich_path_fan_uses_deps_label(self) -> None:
        lines = wily_watch_ui._graph_lines(self.fan, set(), width=70, ascii_=False)
        rendered = ["".join(span for span, _style in line).rstrip() for line in lines]

        self.assertTrue(any("deps 04-1 04-2" in line for line in rendered))

    def test_graph_lines_initial_fan_in_uses_branch_and_merge(self) -> None:
        self.assertTrue(wily_watch_ui._pipeline_renderable(self.initial_fan_in))

        lines = wily_watch_ui._graph_lines(self.initial_fan_in, set(), width=60, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in lines]

        self.assertTrue(any(line.startswith(" +--* a1") for line in rendered))
        self.assertTrue(any(line.startswith(" +--* a2") for line in rendered))
        self.assertIn(" v", rendered)
        self.assertTrue(any(line.lstrip().startswith("o b") and "deps a1 a2" in line for line in rendered))


class FlatTest(unittest.TestCase):
    def test_flat_lines_have_stage_headers_and_parallel_suffix(self) -> None:
        lines = wily_watch_ui._flat_lines(GraphTest.fan, set(), width=70, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in lines]
        self.assertTrue(rendered[0].startswith(" Stage 1 "))
        self.assertTrue(any(line.startswith(" Stage 4 ") and "parallel" in line for line in rendered))
        self.assertTrue(any(line.startswith(" * 01") and line.endswith("A") for line in rendered))
        self.assertTrue(any(line.lstrip().startswith("o 05") and "needs 04-1 04-2" in line for line in rendered))
        self.assertFalse(any(line.lstrip().startswith("+--") for line in rendered))


class CollapseTest(unittest.TestCase):
    def test_collapse_leading_done_in_graph(self) -> None:
        lines, kinds = wily_watch_ui._graph_lines2(GraphTest.fan, set(), width=70, ascii_=True)
        c_lines, c_kinds = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in c_lines]
        self.assertTrue(rendered[0].lstrip().startswith("* 3 phases done"))
        self.assertTrue(any("04-1" in line for line in rendered))
        self.assertTrue(any("04-2" in line for line in rendered))
        self.assertTrue(any(line.startswith(" o 05") for line in rendered))
        self.assertNotIn("done", c_kinds[1:])

    def test_collapse_noop_when_nothing_done(self) -> None:
        phases = [
            {"id": "01", "title": "A", "status": "pending", "depends_on": []},
            {"id": "02", "title": "B", "status": "pending", "depends_on": ["01"]},
        ]
        lines, kinds = wily_watch_ui._graph_lines2(phases, set(), width=40, ascii_=True)
        c_lines, c_kinds = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        self.assertEqual(c_lines, lines)
        self.assertEqual(c_kinds, kinds)

    def test_collapse_leading_done_in_flat(self) -> None:
        lines, kinds = wily_watch_ui._flat_lines2(GraphTest.fan, set(), width=70, ascii_=True)
        c_lines, _ = wily_watch_ui._collapse_leading_done(lines, kinds, ascii_=True)
        rendered = ["".join(span for span, _style in line).rstrip() for line in c_lines]
        self.assertTrue(rendered[0].lstrip().startswith("* 3 phases done"))
        self.assertTrue(any(line.startswith(" Stage 4 ") for line in rendered))


class RenderWatchTest(unittest.TestCase):
    FAN_YAML = "\n".join([
        'roadmap_version: 2',
        'phases:',
        '  - id: "01"',
        '    title: "Settle Korean response-style update"',
        '    status: "done"',
        '    depends_on: []',
        '  - id: "02"',
        '    title: "Harden command skill consistency"',
        '    status: "done"',
        '    depends_on: ["01"]',
        '  - id: "03"',
        '    title: "Korean stage-based DAG status output"',
        '    status: "done"',
        '    depends_on: ["02"]',
        '  - id: "04-1"',
        '    title: "Improve init roadmap authoring"',
        '    status: "pending"',
        '    depends_on: ["03"]',
        '  - id: "04-2"',
        '    title: "Harden lifecycle status CLI"',
        '    status: "pending"',
        '    depends_on: ["03"]',
        '  - id: "05"',
        '    title: "Plugin discovery and release polish"',
        '    status: "pending"',
        '    depends_on: ["04-1", "04-2"]',
    ])

    def _make(self, project: Path, body: str) -> None:
        _write_roadmap(project, body)

    def test_full_render_plain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            lines = out.splitlines()
            self.assertIn("Wily Roadmap", out)
            self.assertIn("3/6", out)
            self.assertIn("50%", out)
            self.assertTrue(any(line.lstrip().startswith("+--> 04-1") for line in lines))
            self.assertTrue(any(line.lstrip().startswith("+--> 04-2") for line in lines))
            self.assertTrue(any(line.strip() == "v" for line in lines))
            self.assertIn("deps 04-1 04-2", out)
            self.assertIn("git:", out)

    def test_render_collapses_when_short(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 8))
            self.assertIn("3 phases done", out)
            self.assertIn("04-1", out)
            self.assertIn("04-2", out)
            self.assertIn("05", out)

    def test_render_falls_back_to_flat_for_skip_dag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), "\n".join([
                'roadmap_version: 1',
                'phases:',
                '  - id: "01"',
                '    title: "A"',
                '    status: "done"',
                '    depends_on: []',
                '  - id: "02"',
                '    title: "B"',
                '    status: "done"',
                '    depends_on: ["01"]',
                '  - id: "03"',
                '    title: "C"',
                '    status: "pending"',
                '    depends_on: ["02", "01"]',
            ]))
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("Stage 1", out)
            self.assertFalse(any(line.lstrip().startswith("+--") for line in out.splitlines()))

    def test_render_narrow_one_liner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(18, 24))
            self.assertEqual(len(out.splitlines()), 1)
            self.assertIn("Wily", out)
            self.assertIn("3/6", out)
            self.assertLessEqual(len(out), 18)

    def test_render_no_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("no roadmap", out)
            self.assertIn("$wily-init", out)
            self.assertIn("git:", out)

    def test_render_zero_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), "roadmap_version: 3\nphases: []\n")
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=False, size=(70, 24))
            self.assertIn("0/0", out)
            self.assertIn("no phases yet", out)

    def test_render_rich_smoke(self) -> None:
        try:
            import rich  # noqa: F401
        except ImportError:
            self.skipTest("rich not installed")
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            out = wily_watch_ui.render_watch(Path(tmp), interval=2.0, rich=True, size=(70, 24))
            plain = ANSI_RE.sub("", out) if "ANSI_RE" in globals() else out
            for pid in ("01", "02", "03", "04-1", "04-2", "05"):
                self.assertIn(pid, plain)


class CliWiringTest(unittest.TestCase):
    def test_watch_once_ascii_uses_new_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_roadmap(Path(tmp), RenderWatchTest.FAN_YAML)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "wily.py"), "watch", "--once", "--ui", "ascii"],
                cwd=tmp,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env={**os.environ, "COLUMNS": "80", "LINES": "30"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("3/6", result.stdout)
            self.assertIn("deps 04-1 04-2", result.stdout)
            self.assertNotIn("Phase 흐름:", result.stdout)
            self.assertNotIn("Repo: ", result.stdout)
