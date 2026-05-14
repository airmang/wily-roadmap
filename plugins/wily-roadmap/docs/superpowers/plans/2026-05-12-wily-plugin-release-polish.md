# Wily Plugin Release Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify Wily Roadmap is locally release-ready and fix only documentation or discovery drift found by the checks.

**Architecture:** Keep this phase as a local release-readiness gate, not a feature expansion. Validate the plugin manifest, skill discovery contracts, CLI command contracts, and documentation against current behavior; make small targeted edits only when a check exposes drift.

**Tech Stack:** Codex plugin manifest JSON, Markdown skill files, Python standard library scripts, Python `unittest`, `rg`.

---

## File Structure

- `.codex-plugin/plugin.json` — plugin discovery metadata, skill directory, interface copy, default prompts.
- `skills/wily-*/SKILL.md` — command skill entrypoints and response contracts.
- `skills/wily-workflow/SKILL.md` and `skills/wily-workflow/references/*.md` — workflow-level routing and policy references.
- `scripts/wily.py`, `scripts/wily_state_summary.py`, `scripts/wily_watch_ui.py` — local CLI and deterministic renderers.
- `tests/test_wily_command_skills.py`, `tests/test_wily_cli.py`, `tests/test_wily_state_summary.py`, `tests/test_wily_watch_ui.py` — release-readiness regression coverage.
- `.wily/phases/05-plugin-discovery-release-polish/plan.md` — Wily phase pointer to this plan.

## Task 1: Baseline Release Audit

**Files:**
- Read: `.codex-plugin/plugin.json`
- Read: `skills/wily-*/SKILL.md`
- Read: `skills/wily-workflow/SKILL.md`
- Read: `skills/wily-workflow/references/*.md`
- Read: `scripts/wily.py`
- Read: `scripts/wily_state_summary.py`
- Read: `scripts/wily_watch_ui.py`
- Read: `tests/test_wily_command_skills.py`
- Read: `tests/test_wily_cli.py`

- [ ] **Step 1: Validate plugin manifest JSON**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Expected: exit code `0`.

- [ ] **Step 2: Inspect manifest fields**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path(".codex-plugin/plugin.json").read_text(encoding="utf-8"))
print(manifest["name"])
print(manifest["version"])
print(manifest["skills"])
print(manifest["interface"]["displayName"])
print("\n".join(manifest["interface"]["defaultPrompt"]))
PY
```

Expected output includes:

```text
wily-roadmap
0.1.0
./skills/
Wily Roadmap
$wily-init: create a roadmap for this repo
$wily-status: show current roadmap state
$wily-watch: watch roadmap state in a tmux pane
$wily-next: show the next ready phase
```

- [ ] **Step 3: List discoverable command skills**

Run:

```bash
find skills -maxdepth 2 -name SKILL.md | sort
```

Expected output includes exactly these command skills plus `wily-workflow`:

```text
skills/wily-block/SKILL.md
skills/wily-complete/SKILL.md
skills/wily-init/SKILL.md
skills/wily-next/SKILL.md
skills/wily-replan/SKILL.md
skills/wily-retry/SKILL.md
skills/wily-start/SKILL.md
skills/wily-status/SKILL.md
skills/wily-watch/SKILL.md
skills/wily-workflow/SKILL.md
```

- [ ] **Step 4: Record any drift**

If a field or skill is missing, write down the exact missing item before editing. If there is no drift, do not edit manifest or skill files in this task.

## Task 2: Manifest and Skill Discovery Tests

**Files:**
- Modify if needed: `tests/test_wily_command_skills.py`
- Modify only if drift is found: `.codex-plugin/plugin.json`
- Modify only if drift is found: `skills/wily-*/SKILL.md`

- [ ] **Step 1: Run current discovery tests**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: all tests pass.

- [ ] **Step 2: Add a failing test only if Task 1 found uncovered drift**

If Task 1 found manifest drift that existing tests did not cover, add the smallest focused test to `tests/test_wily_command_skills.py`. For example, if the manifest `skills` path is not covered, add:

```python
    def test_plugin_manifest_points_to_skills_directory(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["skills"], "./skills/")
```

Run:

```bash
python3 -m unittest tests.test_wily_command_skills.WilyCommandSkillsTest.test_plugin_manifest_points_to_skills_directory
```

Expected before implementation: fail only if the manifest value is wrong.

- [ ] **Step 3: Fix the uncovered drift**

If the new test failed, update only the drifted value. For the example above, `.codex-plugin/plugin.json` must include:

```json
"skills": "./skills/"
```

- [ ] **Step 4: Re-run discovery tests**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: all tests pass.

## Task 3: CLI and Renderer Contract Verification

**Files:**
- Modify only if drift is found: `scripts/wily.py`
- Modify only if drift is found: `scripts/wily_state_summary.py`
- Modify only if drift is found: `scripts/wily_watch_ui.py`
- Modify only if drift is found: `tests/test_wily_cli.py`
- Modify only if drift is found: `tests/test_wily_state_summary.py`
- Modify only if drift is found: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Run CLI and renderer tests**

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_state_summary tests.test_wily_watch_ui
```

Expected: all tests pass.

- [ ] **Step 2: Compile scripts**

Run:

```bash
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py scripts/wily_watch_ui.py
```

Expected: exit code `0`.

- [ ] **Step 3: Manually inspect current status pane**

Run:

```bash
python3 scripts/wily.py status
```

Expected output starts with `Wily Roadmap`, shows a progress bar, and does not show fallback `Roadmap:` or `Phase 흐름:` headings.

- [ ] **Step 4: Manually inspect watch once output**

Run:

```bash
python3 scripts/wily.py watch --once --ui ascii
```

Expected output uses the same pane style as status and includes `Wily Roadmap`.

## Task 4: Documentation Drift Review

**Files:**
- Modify only if drift is found: `skills/wily-status/SKILL.md`
- Modify only if drift is found: `skills/wily-watch/SKILL.md`
- Modify only if drift is found: `skills/wily-workflow/SKILL.md`
- Modify only if drift is found: `skills/wily-workflow/references/*.md`
- Modify only if drift is found: `docs/superpowers/specs/*.md`
- Modify only if drift is found: `docs/superpowers/plans/*.md`

- [ ] **Step 1: Search for stale or placeholder text**

Run:

```bash
rg -n "TODO|TBD|placeholder|old external workflow|Phase 흐름" .codex-plugin skills scripts tests docs
```

Expected: no actionable stale references in live plugin files. Historical docs may mention old terms only as historical context; if so, leave them unless they instruct current behavior incorrectly.

- [ ] **Step 2: Check status/watch skill wording**

Run:

```bash
sed -n '1,90p' skills/wily-status/SKILL.md
sed -n '1,90p' skills/wily-watch/SKILL.md
```

Expected:
- `wily-status` says it shows the `Wily Roadmap` pane once.
- `wily-watch` says it opens a continuously refreshing pane.
- Neither skill tells the agent to replace the pane with prose.

- [ ] **Step 3: Fix only live-doc drift**

If a live skill or workflow reference contradicts current behavior, edit the smallest relevant Markdown section. Do not rewrite historical implementation plans unless they actively confuse current behavior.

## Task 5: Full Release-Readiness Verification

**Files:**
- Read: all project files relevant to verification.
- Modify: none unless a previous task found drift.

- [ ] **Step 1: Run full tests**

Run:

```bash
python3 -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 2: Validate manifest**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Expected: exit code `0`.

- [ ] **Step 3: Compile scripts**

Run:

```bash
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py scripts/wily_watch_ui.py
```

Expected: exit code `0`.

- [ ] **Step 4: Search for blocked strings**

Run:

```bash
rg -n "TODO|TBD|placeholder|old external workflow" .codex-plugin skills scripts tests docs
```

Expected: no actionable live-plugin issues.

- [ ] **Step 5: Review git state**

Run:

```bash
git status --short
```

Expected: either clean, or only intentional release-polish edits from this phase.

## Task 6: Handoff and Completion Gate

**Files:**
- Modify: `.wily/phases/05-plugin-discovery-release-polish/plan.md`
- Read: `.wily/sessions/2026-05-12-084025-phase-05-attempt-1/`

- [ ] **Step 1: Summarize verification evidence**

Record the commands from Task 5 and their results in the current phase session result or handoff summary.

- [ ] **Step 2: Summarize changed files**

Run:

```bash
git status --short
git diff --stat
```

Expected: changed files are explainable as release-readiness edits.

- [ ] **Step 3: Ask before commit, push, publish, or PR**

Do not run any of these without explicit user approval:

```bash
git commit
git push
gh pr create
```

## Self-Review

- Spec coverage: The plan validates manifest, skill discovery, tests, compile checks, documentation drift, and approval-first release actions.
- Placeholder scan: The only appearances of placeholder-like terms are inside explicit search commands and expected-result explanations for the release audit.
- Type consistency: All commands and file paths match the current repository layout.
