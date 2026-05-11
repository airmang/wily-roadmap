from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wily_watch_ui


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
