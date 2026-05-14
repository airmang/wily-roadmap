# Wily Phase Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic phase lifecycle commands that create session records and update `.wily/roadmap.yaml`.

**Architecture:** Extend `scripts/wily.py` with `start`, `complete`, `block`, and `retry`. Keep phase implementation itself in Codex; the script only records approved lifecycle transitions.

**Tech Stack:** Python standard library and `unittest`.

---

### Task 1: Lifecycle Tests

**Files:**
- Modify: `tests/test_wily_cli.py`

- [ ] **Step 1: Test `start <id>`**

Assert it creates `.wily/sessions/<timestamp>-phase-<id>-attempt-1/`, writes `status.yaml`, `input.md`, `result.md`, `verification.md`, `changed-files.md`, and marks the phase `in_progress`.

- [ ] **Step 2: Test `complete <id>`**

Assert it marks the phase `done` and updates the current session status to `verified`.

- [ ] **Step 3: Test `block <id> <reason>`**

Assert it marks the phase `blocked`, records the blocker in roadmap metadata, and records blocked status in the current session.

- [ ] **Step 4: Test `retry <id>`**

Assert it creates the next attempt session while preserving the previous session and marks the phase `in_progress`.

### Task 2: Lifecycle Implementation

**Files:**
- Modify: `scripts/wily.py`

- [ ] **Step 1: Add phase lookup and roadmap saving helpers**

Find phases by ID and write serialized roadmap state back to disk.

- [ ] **Step 2: Add session creation helpers**

Compute the next attempt number, create session files, and store the relative session path in `current_session`.

- [ ] **Step 3: Add transition commands**

Implement `start`, `complete`, `block`, and `retry` with clear non-zero errors for missing phases.

- [ ] **Step 4: Update usage text**

List the new lifecycle commands.

### Task 3: Documentation Wiring

**Files:**
- Modify: `skills/wily-workflow/SKILL.md`
- Modify: `skills/wily-workflow/references/commit-policy.md`

- [ ] **Step 1: Mention lifecycle helper commands**

Document that helper commands record lifecycle transitions, but Codex still asks for approval before implementation.

### Task 4: Final Verification

**Files:**
- Validate all changed files.

- [ ] **Step 1: Run all tests**

Run: `python3 -m unittest discover`

Expected: all tests pass.

- [ ] **Step 2: Compile scripts**

Run: `python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py`

Expected: exit code 0.

- [ ] **Step 3: Validate manifest and blocked strings**

Run JSON validation and blocked-string search.
