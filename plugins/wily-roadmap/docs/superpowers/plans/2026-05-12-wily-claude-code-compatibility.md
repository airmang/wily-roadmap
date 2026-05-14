# Wily Claude Code Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Wily's workflow instructions usable from Claude Code as well as Codex while preserving Codex plugin discovery.

**Architecture:** Treat compatibility as a documentation contract, not a runtime abstraction layer. Keep `.codex-plugin/plugin.json` and `skills/` valid for Codex discovery, add a small platform-neutral compatibility reference for Claude Code invocation, and update only Codex-specific wording that affects current user-facing guidance.

**Tech Stack:** Markdown skill files and references, Codex plugin manifest JSON, Python standard library `unittest`.

---

## File Structure

- Modify: `tests/test_wily_command_skills.py` - add focused document tests for Claude Code guidance, platform-neutral workflow wording, and preserved Codex discovery metadata.
- Create: `skills/wily-workflow/references/agent-compatibility.md` - define how agents map Wily command skills and helper commands in Codex and Claude Code.
- Modify: `skills/wily-workflow/SKILL.md` - widen workflow wording from Codex-only to agent-neutral where appropriate and link the compatibility reference.
- Modify: `skills/wily-workflow/references/planning-style.md` - replace "Codex session" phase sizing with agent-neutral focused implementation session language.
- Modify: `skills/wily-workflow/references/routing-policy.md` - replace "Codex judgment" wording with agent-neutral responsibility wording.
- Modify: `skills/wily-init/SKILL.md` - replace Codex-only repository scan wording with agent-neutral wording.
- Modify: `skills/wily-start/SKILL.md` - replace "fresh Codex session" with "fresh agent session".
- Modify: `.codex-plugin/plugin.json` - keep Codex discovery fields intact while broadening human-facing descriptions.
- Modify: `.wily/phases/06-2-claude-code-compatibility/plan.md` - point the phase at this detailed plan after implementation planning is accepted.

## Task 1: Lock The Compatibility Contract With Tests

**Files:**
- Modify: `tests/test_wily_command_skills.py`

- [ ] **Step 1: Add a failing test for the new compatibility reference**

Add this method inside `WilyCommandSkillsTest`, after `test_workflow_docs_describe_status_pane_not_old_phase_flow`:

```python
    def test_workflow_documents_claude_code_compatibility(self) -> None:
        workflow = (ROOT / "skills" / "wily-workflow" / "SKILL.md").read_text(encoding="utf-8")
        compatibility = (
            ROOT / "skills" / "wily-workflow" / "references" / "agent-compatibility.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Agent compatibility", workflow)
        self.assertIn("references/agent-compatibility.md", workflow)
        self.assertIn("Claude Code", compatibility)
        self.assertIn("Use the `$wily-*` text commands as user-facing entrypoints.", compatibility)
        self.assertIn("Run `python3 <plugin-root>/scripts/wily.py <command>`", compatibility)
        self.assertIn("Keep Wily local-first and approval-first in every agent environment.", compatibility)
```

- [ ] **Step 2: Add a failing test for platform-neutral live skill wording**

Add this method after the compatibility reference test:

```python
    def test_live_skill_guidance_is_not_codex_only(self) -> None:
        paths = [
            ROOT / "skills" / "wily-init" / "SKILL.md",
            ROOT / "skills" / "wily-start" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "SKILL.md",
            ROOT / "skills" / "wily-workflow" / "references" / "planning-style.md",
            ROOT / "skills" / "wily-workflow" / "references" / "routing-policy.md",
        ]
        forbidden = (
            "leaves Codex responsible",
            "fresh Codex session",
            "Codex-sized phases",
            "Codex still owns",
            "one focused Codex session",
            "Codex judgment",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase, text)
```

- [ ] **Step 3: Add a failing test that Codex plugin discovery remains intact**

Extend `test_plugin_default_prompts_use_command_entrypoints` with these assertions:

```python
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertIn("codex", manifest["keywords"])
        self.assertIn("Claude Code", manifest["interface"]["longDescription"])
        self.assertIn("Codex plugin discovery", manifest["interface"]["longDescription"])
```

- [ ] **Step 4: Run the focused tests and confirm they fail for the intended reason**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: FAIL because `agent-compatibility.md` does not exist yet and live docs still contain Codex-only phrases.

## Task 2: Add Agent Compatibility Guidance

**Files:**
- Create: `skills/wily-workflow/references/agent-compatibility.md`
- Modify: `skills/wily-workflow/SKILL.md`

- [ ] **Step 1: Create the compatibility reference**

Create `skills/wily-workflow/references/agent-compatibility.md` with:

```markdown
# Agent Compatibility

Wily is maintained as a Codex-discoverable plugin, but its workflow contract is agent-neutral.

## Command Entry Points

Use the `$wily-*` text commands as user-facing entrypoints.

In Codex, plugin discovery can map those commands to Wily skills under `skills/`.

In Claude Code, use the same `$wily-*` command names as plain text instructions. If skill discovery is not available, read the matching `skills/wily-*/SKILL.md` file and follow its internal command and boundary sections.

## Helper Invocation

Run `python3 <plugin-root>/scripts/wily.py <command>` for deterministic local state operations.

The helper script owns file creation, roadmap state transitions, session directories, and watch/status rendering. The active agent still owns repository inspection, user approval, phase design, planner selection, implementation, verification, and concise reporting.

## Boundaries

Keep Wily local-first and approval-first in every agent environment.

Do not push, open pull requests, merge, install remote integrations, delete user work, or run destructive commands unless the user explicitly approves that specific action.

Keep `.codex-plugin/plugin.json` and `skills/` compatible with Codex plugin discovery even when adding Claude Code guidance.
```

- [ ] **Step 2: Link the reference from the workflow skill**

In `skills/wily-workflow/SKILL.md`, add this bullet under `Read detailed policy only when needed:`:

```markdown
- Agent compatibility and Claude Code usage: `references/agent-compatibility.md`
```

- [ ] **Step 3: Run the compatibility reference test**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills.WilyCommandSkillsTest.test_workflow_documents_claude_code_compatibility
```

Expected: PASS.

## Task 3: Replace Codex-Only Live Guidance With Agent-Neutral Wording

**Files:**
- Modify: `skills/wily-workflow/SKILL.md`
- Modify: `skills/wily-workflow/references/planning-style.md`
- Modify: `skills/wily-workflow/references/routing-policy.md`
- Modify: `skills/wily-init/SKILL.md`
- Modify: `skills/wily-start/SKILL.md`

- [ ] **Step 1: Update workflow metadata and purpose**

In `skills/wily-workflow/SKILL.md`, replace:

```markdown
description: "Use when the user wants Wily's personal Codex workflow for software work: initialize or inspect per-repo .wily state, turn a large goal into dependency-aware roadmap phases, choose the next safe phase, execute a phase through an auditable session, revise future roadmap work, summarize progress, or keep remote/destructive actions approval-first."
metadata:
  short-description: Wily Roadmap workflow for Codex
```

with:

```markdown
description: "Use when the user wants Wily's personal agent workflow for software work: initialize or inspect per-repo .wily state, turn a large goal into dependency-aware roadmap phases, choose the next safe phase, execute a phase through an auditable session, revise future roadmap work, summarize progress, or keep remote/destructive actions approval-first."
metadata:
  short-description: Wily Roadmap workflow for agentic coding
```

Also replace:

```markdown
splits large goals into Codex-sized phases
```

with:

```markdown
splits large goals into focused agent-sized phases
```

- [ ] **Step 2: Update workflow helper responsibility wording**

In `skills/wily-workflow/SKILL.md`, replace:

```markdown
Codex still owns interpretation, user approval, phase design, planner selection, implementation, and verification.
```

with:

```markdown
The active agent still owns interpretation, user approval, phase design, planner selection, implementation, and verification.
```

- [ ] **Step 3: Update planning-style phase sizing**

In `skills/wily-workflow/references/planning-style.md`, replace:

```markdown
- be executable in one focused Codex session,
```

with:

```markdown
- be executable in one focused agent session,
```

- [ ] **Step 4: Update routing-policy responsibility wording**

In `skills/wily-workflow/references/routing-policy.md`, replace:

```markdown
The helper does not replace Codex judgment. It creates and reads files; Codex still scans the repository, designs phases, asks for approval, implements approved work, and records verification.
```

with:

```markdown
The helper does not replace agent judgment. It creates and reads files; the active agent still scans the repository, designs phases, asks for approval, implements approved work, and records verification.
```

- [ ] **Step 5: Update command skill wording**

In `skills/wily-init/SKILL.md`, replace:

```markdown
leaves Codex responsible for the repository scan and goal question.
```

with:

```markdown
leaves the active agent responsible for the repository scan and goal question.
```

In `skills/wily-start/SKILL.md`, replace:

```markdown
- Prefer starting in a fresh Codex session.
```

with:

```markdown
- Prefer starting in a fresh agent session.
```

- [ ] **Step 6: Run the platform-neutral wording test**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills.WilyCommandSkillsTest.test_live_skill_guidance_is_not_codex_only
```

Expected: PASS.

## Task 4: Broaden Manifest Description Without Breaking Codex Discovery

**Files:**
- Modify: `.codex-plugin/plugin.json`

- [ ] **Step 1: Update manifest descriptions only**

In `.codex-plugin/plugin.json`, change:

```json
"description": "Personal Codex workflow plugin for Wily roadmap, phase, and session management."
```

to:

```json
"description": "Personal agent workflow plugin for Wily roadmap, phase, and session management."
```

Change:

```json
"shortDescription": "Manage large Codex projects with Wily roadmaps and phases."
```

to:

```json
"shortDescription": "Manage large agentic coding projects with Wily roadmaps and phases."
```

Change `interface.longDescription` to:

```json
"longDescription": "A personal agent workflow plugin for local-first project roadmaps: initialize per-repo .wily state, split large goals into dependency-aware phases, execute phases through auditable sessions, revise future work without rewriting completed history, require approval for remote or destructive actions, document Claude Code usage, and preserve Codex plugin discovery compatibility."
```

Keep these fields unchanged:

```json
"name": "wily-roadmap"
"keywords": [
  "codex",
  "workflow",
  "planning",
  "orchestration"
]
"skills": "./skills/"
```

- [ ] **Step 2: Validate JSON**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Expected: exits 0.

- [ ] **Step 3: Run the manifest test**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills.WilyCommandSkillsTest.test_plugin_default_prompts_use_command_entrypoints
```

Expected: PASS.

## Task 5: Phase Plan Pointer And Final Verification

**Files:**
- Modify: `.wily/phases/06-2-claude-code-compatibility/plan.md`

- [ ] **Step 1: Point the phase plan at this detailed plan**

Replace `.wily/phases/06-2-claude-code-compatibility/plan.md` with:

```markdown
# Implementation Plan

Detailed plan: `docs/superpowers/plans/2026-05-12-wily-claude-code-compatibility.md`

## Summary

- Add an agent compatibility reference for Claude Code and Codex usage.
- Replace Codex-only live guidance with agent-neutral wording where it affects current workflow instructions.
- Preserve `.codex-plugin/plugin.json` and `skills/` compatibility for Codex plugin discovery.
- Add document tests for Claude Code guidance, platform-neutral wording, and manifest compatibility.
```

- [ ] **Step 2: Run required phase verification**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
python3 -m unittest discover
python3 -m py_compile scripts/wily.py
```

Expected: all commands exit 0.

- [ ] **Step 3: Manually inspect from Claude Code's perspective**

Run:

```bash
sed -n '1,180p' skills/wily-workflow/references/agent-compatibility.md
sed -n '1,190p' skills/wily-workflow/SKILL.md
rg -n "Codex|Claude Code|agent" skills/wily-workflow skills/wily-init/SKILL.md skills/wily-start/SKILL.md .codex-plugin/plugin.json
```

Expected:

- Claude Code can use `$wily-*` as plain text command names.
- Claude Code has a fallback path to read `skills/wily-*/SKILL.md`.
- Helper invocation remains `python3 <plugin-root>/scripts/wily.py <command>`.
- Local-first and approval-first boundaries are explicit.
- Codex plugin discovery fields remain present.

## Self-Review

- Spec coverage: The plan documents Claude Code command invocation, skill mapping, local-first boundaries, platform-neutral live wording, preserved Codex discovery, and tests for metadata plus documentation contracts.
- Placeholder scan: No plan step uses placeholder implementation text.
- Naming consistency: The new reference path is consistently `skills/wily-workflow/references/agent-compatibility.md`, and the test method names all live under `WilyCommandSkillsTest`.
