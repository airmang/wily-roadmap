# Wily Watch V3 Tmux UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore tmux right-pane launch and polished terminal watch UI for v3 tasks.

**Architecture:** Keep state loading in `wily.cli.status`, put watch launch logic in `wily.cli.watch`, and keep rendering in `wily.ui.watch_render`. The watch pane invokes the same script with `watch --here`, avoiding v2 stage/phase/board code.

**Tech Stack:** Python stdlib, tmux CLI, existing v3 Wily models and unittest suite.

---

### Task 1: Add Watch Launch Tests

**Files:**
- Modify: `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- Modify: `plugins/wily-roadmap/scripts/wily/cli/watch.py`

- [ ] **Step 1: Write failing tests** for `watch_launch_mode`, `tmux_watch_command`, and watch-only argument stripping.
- [ ] **Step 2: Run targeted tests** with `python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py -k watch`.
- [ ] **Step 3: Implement minimal launch helpers** in `watch.py`.
- [ ] **Step 4: Re-run targeted tests** and confirm they pass.

### Task 2: Restore Current-Terminal Watch Loop

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/cli/status.py`
- Modify: `plugins/wily-roadmap/scripts/wily/cli/watch.py`
- Modify: `plugins/wily-roadmap/tests/v3/test_v3_core.py`

- [ ] **Step 1: Write failing tests** proving `--once` returns status semantics and invalid intervals fail usage.
- [ ] **Step 2: Extract status rendering** so watch can refresh without duplicating status loading.
- [ ] **Step 3: Add `--here` loop** that clears the terminal, prints the rendered snapshot, sleeps, and exits cleanly on Ctrl-C.
- [ ] **Step 4: Run targeted lifecycle/watch tests**.

### Task 3: Polish V3 Watch Renderer

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
- Modify: `plugins/wily-roadmap/tests/v3/test_v3_core.py`

- [ ] **Step 1: Write renderer assertions** for rail rows, checkpoint child rows, blocker child rows, and ASCII output.
- [ ] **Step 2: Adjust renderer spacing and child rows** without adding v2 concepts.
- [ ] **Step 3: Run renderer tests**.

### Task 4: Update Skill And Verify

**Files:**
- Modify: `plugins/wily-roadmap/skills/wily-watch/SKILL.md`

- [ ] **Step 1: Document tmux pane behavior** and fallback behavior concisely.
- [ ] **Step 2: Run `python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`**.
- [ ] **Step 3: Run `python3 plugins/wily-roadmap/scripts/wily.py watch --once --ui ascii`**.
