# Wily Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the plugin from a generic plan-first workflow into the Wily roadmap, phase, session, and revision workflow described in the design spec.

**Architecture:** Keep the plugin local-first and documentation-driven. The skill body explains when to use Wily and the expected operating flow; reference documents define the detailed policies; `scripts/wily_state_summary.py` gives deterministic `.wily/roadmap.yaml` status output.

**Tech Stack:** Markdown skill files, JSON plugin manifest, Python standard library tests and script.

---

### Task 1: Update Plugin Manifest

**Files:**
- Modify: `.codex-plugin/plugin.json`

- [ ] **Step 1: Replace external workflow language**

Change the plugin description and interface copy so it describes Wily roadmap management, not commit-unit development or any external workflow inspiration.

- [ ] **Step 2: Validate JSON**

Run: `python3 -m json.tool .codex-plugin/plugin.json >/dev/null`

Expected: exit code 0.

### Task 2: Rewrite Wily Skill Body

**Files:**
- Modify: `skills/wily-workflow/SKILL.md`

- [ ] **Step 1: Remove old state model**

Replace queue, PR lock, and old plan folder guidance with `.wily/` project, roadmap, phase, session, and revision guidance.

- [ ] **Step 2: Add core command behavior**

Document `wily init`, `wily status`, `wily next`, `wily phase <id>`, `wily start <id>`, `wily complete <id>`, `wily block <id>`, `wily retry <id>`, `wily replan`, `wily watch`, and `wily tmux`.

- [ ] **Step 3: Preserve approval-first rules**

Keep local-first execution, explicit approval for phase starts, and explicit approval for remote or destructive actions.

### Task 3: Replace Reference Policies

**Files:**
- Modify: `skills/wily-workflow/references/routing-policy.md`
- Modify: `skills/wily-workflow/references/planning-style.md`
- Modify: `skills/wily-workflow/references/commit-policy.md`
- Modify: `skills/wily-workflow/references/pr-policy.md`

- [ ] **Step 1: Rename routing around roadmap decisions**

Define how requests map to direct work, roadmap init, phase execution, replan, or status display.

- [ ] **Step 2: Define phase planning style**

Define phase metadata, phase folder format, roadmap graph structure, and status values.

- [ ] **Step 3: Define session execution policy**

Replace commit-unit execution with phase/session execution and retry behavior.

- [ ] **Step 4: Define remote policy**

Keep remote work approval-first without PR-lock state.

### Task 4: Add State Summary Tests

**Files:**
- Create: `tests/test_wily_state_summary.py`

- [ ] **Step 1: Write failing tests**

Add tests for no `.wily` state, roadmap summary with ready and blocked phases, and roadmap replacement metadata.

- [ ] **Step 2: Verify tests fail before script update**

Run: `python3 -m unittest tests.test_wily_state_summary`

Expected: failure because the current script still expects the old state shape.

### Task 5: Rewrite State Summary Script

**Files:**
- Modify: `scripts/wily_state_summary.py`

- [ ] **Step 1: Parse `.wily/roadmap.yaml` with standard library helpers**

Support the simple YAML shape Wily writes: scalar fields, `phases` list, list fields such as `depends_on`, and null values.

- [ ] **Step 2: Summarize roadmap graph**

Print repo, state, git status, roadmap version, done/ready/in-progress/blocked counts, ready phases, blocked phases, superseded phases, and next recommendation.

- [ ] **Step 3: Keep graceful fallback**

If no `.wily` exists, print state none. If `.wily` exists without `roadmap.yaml`, print roadmap missing.

- [ ] **Step 4: Verify tests pass**

Run: `python3 -m unittest tests.test_wily_state_summary`

Expected: all tests pass.

### Task 6: Final Verification

**Files:**
- Read/validate all modified files.

- [ ] **Step 1: Search for old external workflow naming**

Run: `python3 -c "from pathlib import Path; needle='c'+'rack'; matches=[str(p) for p in Path('.').rglob('*') if p.is_file() and needle.lower() in p.read_text(errors='ignore').lower()]; print('\\n'.join(matches)); raise SystemExit(1 if matches else 0)"`

Expected: no matches.

- [ ] **Step 2: Validate plugin JSON**

Run: `python3 -m json.tool .codex-plugin/plugin.json >/dev/null`

Expected: exit code 0.

- [ ] **Step 3: Compile Python**

Run: `python3 -m py_compile scripts/wily_state_summary.py`

Expected: exit code 0.
