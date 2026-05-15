# Stage Phase Hierarchy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Stage-first Wily roadmaps where a Stage can run directly or be manually decomposed into internal Phases and parallel lanes, while preserving existing shared phase-only roadmaps such as `digit`.

**Architecture:** Keep legacy top-level `phases:` as the compatibility path. Add top-level `stages:` support as a second path, with helper functions that normalize executable units for `next`, `start`, `status`, and `watch`. Keep Stage-internal Phase/lane details in `.wily/stages/<stage-id>/stage.yaml` so shared `roadmap.yaml` stays Stage-level. Add a new explicit `decompose-stage` command and skill; no automatic decomposition occurs.

**Tech Stack:** Python standard library CLI, Wily mini YAML parser/serializer, Codex skill markdown, `unittest`.

---

### Task 1: Compatibility and Stage Model Tests

**Files:**
- Modify: `plugins/wily-roadmap/tests/test_wily_state_summary.py`
- Modify: `plugins/wily-roadmap/tests/test_wily_cli.py`

- [ ] **Step 1: Add a `digit`-style legacy roadmap test**

Add a test that writes the `digit` phase-only shape with `lead`, `parallel_group`, `summary`, and `current_session`, then asserts `p01-wily-hit-core` remains executable and no `stages:` field is required.

- [ ] **Step 2: Add Stage direct execution tests**

Add tests for a roadmap with `stages:` where `s01-mvp0` is pending and `s00-foundation` is done. Assert `wily next` recommends `s01-mvp0`, and `wily start s01-mvp0` creates a `stage-s01-mvp0-attempt-1` session without creating child phases.

- [ ] **Step 3: Add explicit decomposition tests**

Add tests for `wily decompose-stage s01-mvp0 --dry-run` and `wily decompose-stage s01-mvp0 --apply-fixture`. The dry run must not mutate roadmap state. The fixture apply must set `execution_mode: "decomposed"` and create deterministic child phase/lane metadata for test coverage.

### Task 2: Stage-Aware State Helpers

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily_state_summary.py`
- Modify: `plugins/wily-roadmap/scripts/wily.py`

- [ ] **Step 1: Add Stage helpers**

Add helpers for `stages`, `stage_index`, `stage_dependencies_done`, `executable_stages`, `find_stage`, and `find_executable_unit`. Existing `executable_phases` must keep current behavior for legacy roadmaps.

- [ ] **Step 2: Add Stage serialization support**

Extend `serialize_roadmap` so it writes top-level `stages:` entries without child Phase/lane details. Add `stage.yaml` serialization for Stage-local child `phases:` and `lanes:` values in a stable subset that the parser can read back. Preserve unknown scalar fields.

- [ ] **Step 3: Add session creation for Stage units**

Allow `start` to create sessions for stage ids. Stage sessions use `stage-<id>` in the folder name, write Stage context into `input.md`, and mark the Stage `in_progress`.

### Task 3: Explicit Stage Decomposition Command

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily.py`
- Create: `plugins/wily-roadmap/skills/wily-decompose-stage/SKILL.md`
- Modify: `plugins/wily-roadmap/.codex-plugin/plugin.json`
- Modify: `plugins/wily-roadmap/tests/test_wily_command_skills.py`

- [ ] **Step 1: Add `decompose-stage` CLI**

Implement `wily.py decompose-stage <stage-id>`. Default mode reports the Stage and says user-authored decomposition is required. `--dry-run` prints a deterministic proposed shape. `--from-json <path>` applies an approved decomposition into `.wily/stages/<stage-id>/stage.yaml`. Test-only `--apply-fixture` writes a small child phase/lane DAG for regression coverage.

- [ ] **Step 2: Add skill contract**

Create `$wily-decompose-stage` as a state-changing skill. It must say decomposition is explicit, never automatic, and may produce parallel lanes with write scopes for later subagent execution.

- [ ] **Step 3: Register command docs**

Add the skill to command skill tests and plugin default prompts. Do not add hooks, MCP servers, or app integrations.

### Task 4: Status and Watch Readability

**Files:**
- Modify: `plugins/wily-roadmap/scripts/wily_state_summary.py`
- Modify: `plugins/wily-roadmap/scripts/wily_watch_ui.py`
- Modify: `plugins/wily-roadmap/tests/test_wily_watch_ui.py`

- [ ] **Step 1: Render Stage-first roadmaps**

Status summaries should show Stage lines when `stages:` exists. Direct Stage shows as executable. Decomposed Stage shows child Phase frontier and lane count.

- [ ] **Step 2: Keep legacy rendering unchanged**

The `digit` fixture and existing phase-only watch tests must continue to produce the same core output.

### Task 5: Verification

**Files:**
- Modify: `.wily/sessions/2026-05-15-080321-phase-14-1-attempt-1/verification.md`
- Modify: `.wily/sessions/2026-05-15-080321-phase-14-1-attempt-1/result.md`
- Modify: `.wily/sessions/2026-05-15-080321-phase-14-1-attempt-1/changed-files.md`

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest plugins.wily-roadmap.tests.test_wily_state_summary plugins.wily-roadmap.tests.test_wily_cli plugins.wily-roadmap.tests.test_wily_command_skills plugins.wily-roadmap.tests.test_wily_watch_ui
```

If module names fail because of the hyphen in `wily-roadmap`, run discovery from the plugin root:

```bash
cd plugins/wily-roadmap && python3 -m unittest discover
```

- [ ] **Step 2: Run compile check**

Run:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
```

- [ ] **Step 3: Record session evidence**

Update the active Wily session artifacts with changed files, verification commands, and the final implementation result.
