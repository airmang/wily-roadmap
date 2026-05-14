# Wily Command Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add precise `$wily-*` skill entrypoints for Wily roadmap commands while keeping `$wily-workflow` as the general router.

**Architecture:** Each command gets a small skill directory under `skills/`. Command skills delegate shared policy to `wily-workflow/references/` and deterministic state changes to `scripts/wily.py`.

**Tech Stack:** Codex skill Markdown, plugin JSON, Python `unittest`.

---

### Task 1: Skill Entry Tests

**Files:**
- Create: `tests/test_wily_command_skills.py`

- [ ] **Step 1: Assert all command skills exist**

Check `skills/wily-init`, `wily-status`, `wily-next`, `wily-start`, `wily-complete`, `wily-block`, `wily-retry`, and `wily-replan` each has `SKILL.md`.

- [ ] **Step 2: Assert frontmatter names match commands**

Check each file contains `name: <command>`.

- [ ] **Step 3: Assert each command explains its helper command or state behavior**

Check each command skill mentions either `scripts/wily.py <command>` or the correct approval/verification boundary.

- [ ] **Step 4: Assert plugin starter prompts use command entrypoints**

Check `.codex-plugin/plugin.json` default prompts include `$wily-init`, `$wily-status`, and `$wily-next`.

### Task 2: Command Skill Files

**Files:**
- Create: `skills/wily-init/SKILL.md`
- Create: `skills/wily-status/SKILL.md`
- Create: `skills/wily-next/SKILL.md`
- Create: `skills/wily-start/SKILL.md`
- Create: `skills/wily-complete/SKILL.md`
- Create: `skills/wily-block/SKILL.md`
- Create: `skills/wily-retry/SKILL.md`
- Create: `skills/wily-replan/SKILL.md`

- [ ] **Step 1: Keep each skill short**

Each command skill should define trigger, purpose, helper command, approval boundary, and response shape.

- [ ] **Step 2: Keep shared policy in existing references**

Do not duplicate the full Wily workflow policy in every command file.

### Task 3: Plugin Starter Prompts

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `skills/wily-workflow/SKILL.md`

- [ ] **Step 1: Update default prompts**

Use three command-style starter prompts: `$wily-init`, `$wily-status`, and `$wily-next`.

- [ ] **Step 2: Document command entrypoints in workflow skill**

Make clear `$wily-workflow` is the general router and `$wily-*` skills are precise commands.

### Task 4: Verification

**Files:**
- Validate all changed files.

- [ ] **Step 1: Run all tests**

Run `python3 -m unittest discover`.

- [ ] **Step 2: Validate manifest and compile scripts**

Run `python3 -m json.tool .codex-plugin/plugin.json >/dev/null` and `python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py`.

- [ ] **Step 3: Search for blocked strings**

Run blocked-string search for old external workflow names and placeholders.
