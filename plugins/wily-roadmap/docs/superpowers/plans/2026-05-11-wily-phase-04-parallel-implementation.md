# Wily Phase 04 Parallel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Wily phases `04-1` and `04-2` in parallel without overwriting existing workspace changes or mixing init behavior with lifecycle/status behavior.

**Architecture:** Dispatch one worker subagent per phase in an isolated fork/worktree. Each worker follows TDD inside its phase scope, reports changed files, and does not revert edits made by others. The controller integrates both results, resolves shared-file overlap in `scripts/wily.py` and `tests/test_wily_cli.py`, then runs the combined verification suite.

**Tech Stack:** Python standard library, `unittest`, local Codex skills, Wily roadmap state under `.wily/`.

---

## Coordination Rules

**Current sessions:**
- `04-1`: `.wily/sessions/2026-05-11-222656-phase-04-1-attempt-1/input.md`
- `04-2`: `.wily/sessions/2026-05-11-222658-phase-04-2-attempt-1/input.md`

**Shared-file risk:**
- Both phases may touch `scripts/wily.py`.
- Both phases may touch `tests/test_wily_cli.py`.
- `04-2` may also touch files with existing uncommitted edits: `scripts/wily_state_summary.py`, `tests/test_wily_state_summary.py`, and lifecycle skill docs.
- Controller must review `git status --short` before and after integration and must not revert unrelated changes.

**Parallel execution model:**
- Workers run in isolated subagent workspaces.
- Workers may edit overlapping logical files in their own workspace, but final merge is controller-owned.
- Workers must keep changes narrowly scoped and list every changed file in their final answer.
- Workers are not alone in the codebase; they must not revert or overwrite changes made by others.

---

## Subagent Dispatch Plan

### Task 1: Worker A Implements Phase 04-1 Init Authoring

**Ownership:**
- Primary: `scripts/wily.py`, init-related helpers only.
- Primary tests: `tests/test_wily_cli.py`, init-related tests only.
- Docs only if behavior changes: `skills/wily-init/SKILL.md`, `skills/wily-workflow/references/planning-style.md`.
- Reference only: `docs/superpowers/specs/2026-05-11-wily-roadmap-design.md`.

**Prompt to send to worker:**

```text
Implement Wily phase 04-1: Improve init roadmap authoring.

You are not alone in the codebase. Do not revert edits made by others. Keep your edits narrowly scoped to init behavior, and list every file you changed.

Context:
- Phase session input: .wily/sessions/2026-05-11-222656-phase-04-1-attempt-1/input.md
- Compare skills/wily-init/SKILL.md with command_init in scripts/wily.py.
- Existing command_init creates .wily directories and baseline project/status/decisions/roadmap files with write_once.
- Completion criteria:
  - Any deterministic init behavior belongs in scripts/wily.py.
  - $wily-init still scans first and asks for a goal when none is supplied.
  - Existing .wily/ state is never overwritten without approval.
  - Tests document intended init behavior.

Use TDD:
1. Add focused failing tests in tests/test_wily_cli.py for deterministic init behavior.
2. Run the targeted test and confirm it fails for the expected reason.
3. Implement the minimal scripts/wily.py change.
4. Run the targeted tests until they pass.
5. Update skill docs only where script behavior changed.

Scope guard:
- Do not implement automatic project-specific roadmap intelligence.
- Do not change lifecycle commands except where shared helpers require compatibility.
- Do not alter status summary behavior.

Suggested tests:
- init without a goal creates baseline state but prints Goal: needed, preserving the skill contract that Codex asks for the goal.
- init with preexisting .wily files preserves user-authored project.md, roadmap.yaml, status.md, and decisions.md.
- init ensures required directories exist even when partial .wily state already exists.

Verification to run:
- python3 -m unittest tests.test_wily_cli
- python3 -m py_compile scripts/wily.py

Final response format:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Changed files:
- path
Tests run:
- command: result
Summary:
- What behavior changed and why.
Concerns:
- Any shared-file or integration risk.
```

### Task 2: Worker B Implements Phase 04-2 Lifecycle Status Hardening

**Ownership:**
- Primary: `scripts/wily_state_summary.py`.
- Primary tests: `tests/test_wily_state_summary.py`.
- Secondary: lifecycle/status sections of `scripts/wily.py` and `tests/test_wily_cli.py`.
- Docs only if behavior changes: `skills/wily-status/SKILL.md`, `skills/wily-next/SKILL.md`, `skills/wily-start/SKILL.md`, `skills/wily-complete/SKILL.md`, `skills/wily-block/SKILL.md`, `skills/wily-retry/SKILL.md`, `skills/wily-replan/SKILL.md`.

**Prompt to send to worker:**

```text
Implement Wily phase 04-2: Harden lifecycle status CLI.

You are not alone in the codebase. Do not revert edits made by others. Keep your edits narrowly scoped to lifecycle/status behavior, and list every file you changed.

Context:
- Phase session input: .wily/sessions/2026-05-11-222658-phase-04-2-attempt-1/input.md
- Begin with tests/test_wily_cli.py and tests/test_wily_state_summary.py.
- Inspect lifecycle/status functions in scripts/wily.py and scripts/wily_state_summary.py.
- Completion criteria:
  - Status output remains stable and useful for ready, blocked, superseded, and replacement phases.
  - Lifecycle commands preserve session history and current phase state.
  - Tests cover important parse, serialize, and session edge cases.
  - Helper script output stays machine-facing and English where applicable.

Use TDD:
1. Add focused failing tests for one lifecycle/status edge case at a time.
2. Run the targeted test and confirm it fails for the expected reason.
3. Implement minimal parser/serializer/session/status logic.
4. Run targeted tests until they pass.
5. Update command skill docs only where behavior changed.

Scope guard:
- Do not expand the parser into a general YAML implementation.
- Do not change command names or plugin entrypoints.
- Do not alter init roadmap-authoring behavior except to preserve compatibility with shared helpers.

Suggested tests:
- parse/serialize preserves replacement metadata such as replaces lists and superseded phases.
- retry preserves the previous session and clears stale blocker metadata on the retried phase.
- complete/block on a phase without current_session updates roadmap state without crashing.
- status summary remains stable for ready, blocked, superseded, and replacement phases.

Verification to run:
- python3 -m unittest tests.test_wily_cli tests.test_wily_state_summary
- python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py

Final response format:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Changed files:
- path
Tests run:
- command: result
Summary:
- What behavior changed and why.
Concerns:
- Any shared-file or integration risk.
```

---

## Controller Integration

### Task 3: Start Workers in Parallel

- [ ] **Step 1: Record pre-dispatch state**

Run:

```bash
git status --short
```

Expected: note existing user/unrelated modifications and do not revert them.

- [ ] **Step 2: Spawn Worker A and Worker B concurrently**

Use `spawn_agent` with `agent_type: "worker"` for both tasks. Do not set a model override unless there is a concrete reason. Give each worker only its task prompt above plus the repository path.

- [ ] **Step 3: Continue local coordination while workers run**

Do not duplicate their implementation work. Prepare an integration checklist for shared files:

```text
Shared files to review:
- scripts/wily.py
- tests/test_wily_cli.py

Phase-specific files:
- 04-1 docs: skills/wily-init/SKILL.md, skills/wily-workflow/references/planning-style.md
- 04-2 summary: scripts/wily_state_summary.py, tests/test_wily_state_summary.py
- 04-2 docs: lifecycle/status skill docs
```

### Task 4: Integrate Worker Results

- [ ] **Step 1: Review Worker A result**

Check:
- Init tests were written before implementation.
- Existing `.wily/` files are preserved by `write_once` or equivalent deterministic behavior.
- No lifecycle/status behavior was changed unnecessarily.

- [ ] **Step 2: Review Worker B result**

Check:
- Status/lifecycle tests were written before implementation.
- Parser changes stay small and roadmap-format-specific.
- Session history is preserved across retry/block/complete flows.

- [ ] **Step 3: Merge shared-file changes intentionally**

For `scripts/wily.py` and `tests/test_wily_cli.py`, combine changes by function/test region:
- Keep init helpers and init tests from `04-1`.
- Keep lifecycle/session/status tests and implementation from `04-2`.
- If both workers changed the same helper, prefer the smaller helper that satisfies both test sets.

- [ ] **Step 4: Update Wily session artifacts**

After successful integration, update:
- `.wily/sessions/2026-05-11-222656-phase-04-1-attempt-1/changed-files.md`
- `.wily/sessions/2026-05-11-222656-phase-04-1-attempt-1/result.md`
- `.wily/sessions/2026-05-11-222658-phase-04-2-attempt-1/changed-files.md`
- `.wily/sessions/2026-05-11-222658-phase-04-2-attempt-1/result.md`

Do not mark phases complete until verification passes and the user explicitly invokes the completion flow.

### Task 5: Combined Verification

- [ ] **Step 1: Run phase 04-1 verification**

Run:

```bash
python3 -m unittest tests.test_wily_cli
```

Expected: all tests pass.

- [ ] **Step 2: Run phase 04-2 targeted verification**

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_state_summary
```

Expected: all tests pass.

- [ ] **Step 3: Run repository test discovery**

Run:

```bash
python3 -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 4: Compile scripts**

Run:

```bash
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
```

Expected: exit code 0.

- [ ] **Step 5: Manual temporary init smoke test if init behavior changed**

Run in a temporary project:

```bash
python3 /Users/wilycastle/Code/projects/wily-roadmap/scripts/wily.py init "Smoke test goal"
python3 /Users/wilycastle/Code/projects/wily-roadmap/scripts/wily.py status
```

Expected:
- `.wily/` directories and baseline files exist.
- Status can read the generated roadmap.
- Re-running init does not overwrite existing state files.

### Task 6: Final Review

- [ ] **Step 1: Run final diff review**

Run:

```bash
git diff -- scripts/wily.py scripts/wily_state_summary.py tests/test_wily_cli.py tests/test_wily_state_summary.py skills/wily-init/SKILL.md skills/wily-status/SKILL.md skills/wily-next/SKILL.md skills/wily-start/SKILL.md skills/wily-complete/SKILL.md skills/wily-block/SKILL.md skills/wily-retry/SKILL.md skills/wily-replan/SKILL.md skills/wily-workflow/references/planning-style.md
```

Expected: diff is limited to phase `04-1` and `04-2` behavior.

- [ ] **Step 2: Summarize integration**

Final handoff should include:
- Changed files grouped by phase.
- Tests run and results.
- Any preexisting dirty files left untouched.
- Whether either phase is ready for `$wily-complete`.
