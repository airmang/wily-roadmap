# Wily Watch Frontier Compaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `$wily-watch` focused on the next executable or earliest pending stage when long unfinished roadmaps overflow the pane.

**Architecture:** Add stage-aware compaction inside `scripts/wily_watch_ui.py` after the normal full render fails to fit. The compact form renders the done-prefix summary, expands the frontier stage, and folds later stages into one-line future summaries. Existing graph rendering, done expansion scrolling, tmux mouse behavior, and CLI flags stay unchanged.

**Tech Stack:** Python standard library, `unittest`, existing Wily roadmap rendering helpers.

---

### Task 1: Regression Tests

**Files:**
- Modify: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Add a long roadmap fixture and constrained render tests**

Add tests under `RenderWatchTest` that create a roadmap with one done stage, a ready Stage 2 frontier, and later wide pending stages. Assert constrained output includes Stage 2/frontier content, includes future summary rows, and does not degrade into late tail-only output.

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui.RenderWatchTest.test_long_unfinished_roadmap_compacts_around_frontier tests.test_wily_watch_ui.RenderWatchTest.test_tiny_body_still_prefers_frontier
```

Expected: fail because the current renderer tail-slices late stages.

### Task 2: Stage-Aware Compaction

**Files:**
- Modify: `scripts/wily_watch_ui.py`

- [ ] **Step 1: Add helpers for stage summaries and frontier selection**

Add helpers that:

- Select the frontier stage from `_ordered_stages(view.phases)` using `view.ready_ids`, falling back to the earliest non-done stage.
- Render the frontier stage with `_stage_header()` and `_node_line()`.
- Render future stages as one-line summaries like `Stage 3 - 9 phases pending`.

- [ ] **Step 2: Replace unfinished tail slicing**

In `_body_lines()`, after done-prefix collapse still exceeds `max_rows`, call the new stage-aware compact renderer before any line slicing. Preserve `expand_done=True` scroll behavior exactly as-is.

- [ ] **Step 3: Run focused tests and verify pass**

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui.RenderWatchTest.test_long_unfinished_roadmap_compacts_around_frontier tests.test_wily_watch_ui.RenderWatchTest.test_tiny_body_still_prefers_frontier
```

Expected: both tests pass.

### Task 3: Verification and Completion

**Files:**
- Modify as produced by prior tasks.
- Wily state may be updated by `wily complete`.

- [ ] **Step 1: Run full verification**

Run:

```bash
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py scripts/wily_watch_ui.py scripts/wily_runner.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 2: Mark the active Wily phase complete**

Run the Wily completion command for the active phase after verification. Include any resulting `.wily` state changes in the implementation commit.

- [ ] **Step 3: Commit and push**

Commit implementation, tests, plan/spec docs, and Wily completion state. Push `main` to `origin`.
