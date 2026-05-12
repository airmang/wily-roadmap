# Wily Watch Stage Compaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make long watch panes clearly collapse completed stage groups while preserving unfinished/current/ready/blocked phases.

**Architecture:** Keep the existing render pipeline, but make the leading-done collapse summary explicit about completed stages as well as phase count. When height is constrained, the renderer collapses only leading fully done stages, keeps later unfinished lines, and avoids hiding current, ready, blocked, or pending work.

**Tech Stack:** Python watch renderer, `unittest`, Markdown skill documentation.

---

## Tasks

- [ ] Add long-roadmap tests that assert the short pane shows completed stage count and preserves unfinished phases.
- [ ] Update `_summary_line` and `_collapse_leading_done` in `scripts/wily_watch_ui.py` to track collapsed stage count.
- [ ] Preserve existing phase-count wording enough for current tests while adding stage meaning.
- [ ] Update `skills/wily-watch/SKILL.md` with the completed-stage compaction contract.
- [ ] Run `python3 -m unittest tests.test_wily_watch_ui`, `python3 -m unittest discover`, and `python3 -m py_compile scripts/wily_watch_ui.py`.
