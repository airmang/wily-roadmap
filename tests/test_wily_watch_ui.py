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
