# Wily CLI Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic local `scripts/wily.py` helper for creating and inspecting `.wily` roadmap state.

**Architecture:** Keep Codex responsible for goal interpretation and phase design, while the script handles repeatable filesystem work and roadmap inspection. Reuse `scripts/wily_state_summary.py` for roadmap parsing and summary output so the command helper and status summary stay consistent.

**Tech Stack:** Python standard library, `unittest`, Markdown/YAML-like text files.

---

### Task 1: CLI Behavior Tests

**Files:**
- Create: `tests/test_wily_cli.py`

- [ ] **Step 1: Test `init` creates local state**

Create a temporary project, run `python3 scripts/wily.py init "Ship useful app"`, and assert `.wily/project.md`, `.wily/roadmap.yaml`, `.wily/status.md`, `.wily/decisions.md`, `.wily/phases`, `.wily/sessions`, and `.wily/revisions` exist.

- [ ] **Step 2: Test `status` delegates to summary**

Create a temporary project with a ready phase in `.wily/roadmap.yaml`, run `python3 scripts/wily.py status`, and assert output includes `Roadmap version: 1` and `Next: 01 - First phase`.

- [ ] **Step 3: Test `next` prints phase metadata**

Create a ready phase folder with `phase.md`, `plan.md`, `prompt.md`, and `verification.md`, run `python3 scripts/wily.py next`, and assert those sections are printed.

- [ ] **Step 4: Test `replan` records revision**

Run `python3 scripts/wily.py replan "Switch target"` and assert `.wily/revisions/` contains a revision note and `roadmap.yaml` version increments.

- [ ] **Step 5: Run tests before implementation**

Run: `python3 -m unittest tests.test_wily_cli`

Expected: fail because `scripts/wily.py` does not exist yet.

### Task 2: CLI Implementation

**Files:**
- Create: `scripts/wily.py`

- [ ] **Step 1: Implement command dispatch**

Support `init`, `status`, `next`, `replan`, and `watch`. Return non-zero for unknown commands.

- [ ] **Step 2: Implement `init`**

Create `.wily` directories and baseline files. If a goal argument is provided, write it into `project.md` and `roadmap.yaml`. If no goal is provided, write a status message explaining that the user goal is needed.

- [ ] **Step 3: Implement `status`**

Call `wily_state_summary.summarize_state` or the same fallback output used by `wily_state_summary.py`.

- [ ] **Step 4: Implement `next`**

Read `roadmap.yaml`, select the first ready phase, and print phase details from the phase folder when present.

- [ ] **Step 5: Implement `replan`**

Increment `roadmap_version`, append a revision note, and preserve completed phases.

- [ ] **Step 6: Implement `watch`**

Render current status once by default. Keep continuous refresh out of scope until tmux support is added.

- [ ] **Step 7: Run CLI tests**

Run: `python3 -m unittest tests.test_wily_cli`

Expected: all tests pass.

### Task 3: Documentation Wiring

**Files:**
- Modify: `skills/wily-workflow/SKILL.md`
- Modify: `skills/wily-workflow/references/routing-policy.md`

- [ ] **Step 1: Mention script helper**

Document that deterministic command behavior lives in `scripts/wily.py`.

- [ ] **Step 2: Keep natural-language behavior primary**

Make clear the script is a helper; Codex still handles interpretation, approval, and implementation.

### Task 4: Final Verification

**Files:**
- Read/validate modified files.

- [ ] **Step 1: Run all tests**

Run: `python3 -m unittest discover`

Expected: all tests pass.

- [ ] **Step 2: Compile scripts**

Run: `python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py`

Expected: exit code 0.

- [ ] **Step 3: Validate manifest**

Run: `python3 -m json.tool .codex-plugin/plugin.json >/dev/null`

Expected: exit code 0.

- [ ] **Step 4: Search for blocked naming and placeholders**

Run: `python3 -c "from pathlib import Path; blocked=['c'+'rack','T'+'BD','TO'+'DO']; matches=[]; [matches.append(str(p)) for p in Path('.').rglob('*') if p.is_file() and any(token.lower() in p.read_text(errors='ignore').lower() for token in blocked)]; print('\\n'.join(matches)); raise SystemExit(1 if matches else 0)"`

Expected: no matches.
