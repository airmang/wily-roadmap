# Wily Custom Workflow Reference-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Remove the bundled Custom Workflow runner from Wily live behavior and keep Custom Workflow only as an external workflow reference.

**Architecture:** Preserve Wily roadmap/session lifecycle and the `$wily-run` command name, but downgrade `$wily-run` from bundled runner dispatch to generic external workflow handoff generation. Remove `runners/custom-workflow/` assets and tests that require them; update live docs and skills so no command implies Custom Workflow ships inside Wily.

**Tech Stack:** Python standard library scripts, Markdown skills/commands, JSON plugin manifest, Python `unittest`, `rg`.

---

## File Structure

- Delete: `runners/custom-workflow/` — the bundled Custom Workflow plugin assets are no longer part of Wily.
- Modify: `scripts/wily_runner.py` — keep the module, but remove manifest loading, bundled default runner discovery, Custom Workflow templates, hooks, archive copying, and runner-local file dependencies. It should generate a generic external workflow handoff.
- Modify: `scripts/wily.py` — keep `run` dispatch importing `wily_runner`, and keep completion/block tolerant of absent runner archives.
- Modify: `skills/wily-run/SKILL.md` — describe external workflow handoff, not bundled runner dispatch.
- Modify: `commands/wily-run.md` — describe external workflow handoff.
- Modify: `skills/wily-workflow/SKILL.md` — remove bundled default runner language.
- Modify: `skills/wily-workflow/references/runner-adapter-contract.md` — replace bundled-runner contract with reference-only external workflow guidance and keep the existing `skills/wily-workflow/SKILL.md` link valid.
- Modify: `.codex-plugin/plugin.json` — change the default prompt wording from configured runner dispatch to external workflow handoff.
- Modify: `tests/test_wily_cli.py` — remove bundled Custom Workflow contract tests and replace `wily run` tests with reference-only handoff behavior.
- Modify: `tests/test_wily_command_skills.py` — update assertions for `$wily-run` and workflow guidance.
- Read: `tests/test_wily_watch_ui.py` — keep generic runner progress tests because they do not require bundled Custom Workflow assets.
- Modify: `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/*` — record result, changed files, and verification evidence before completion.

Historical docs and completed `.wily/phases/09-*` records should remain unless they are live plugin guidance. They record a past decision that this phase reverses.

## Decision

Keep `$wily-run`, but change its meaning:

```text
Before: dispatch selected phase to bundled Custom Workflow runner and create runner artifacts.
After: prepare a generic phase handoff for an external workflow such as Custom Workflow.
```

Do not keep a bundled default runner. Do not load manifests from `runners/<id>/runner.yaml`. Do not create `.wily/sessions/<session>/runner/runner.yaml`. Do not copy bundled templates. Do not install or reference bundled hooks.

The command can still accept `--runner <id>` and `--autonomy <mode>` for compatibility, but `--runner` becomes a label for the external workflow, not a local adapter lookup. The default label should be `external`.

## Task 1: Write Failing Tests For Reference-Only Direction

**Files:**
- Modify: `tests/test_wily_cli.py`
- Modify: `tests/test_wily_command_skills.py`

- [x] **Step 1: Replace bundled runner contract tests**

In `tests/test_wily_cli.py`, remove `RunnerContractTest.AGENT_FILES` and these bundled-runner tests:

- `test_custom_workflow_manifest_declares_default_runner_contract`
- `test_workflow_skill_links_runner_adapter_contract`
- `test_custom_workflow_bundle_contains_manifest_entrypoints_and_scripts`
- `test_custom_workflow_hooks_remain_opt_in_and_reference_helper_scripts`
- `test_custom_workflow_agent_toml_files_parse`
- `test_custom_workflow_execution_package_template_passes_validator`

Add this replacement class:

```python
class ReferenceOnlyWorkflowTest(unittest.TestCase):
    def test_custom_workflow_bundle_is_not_part_of_live_plugin(self) -> None:
        self.assertFalse((ROOT / "runners" / "custom-workflow").exists())

    def test_workflow_guidance_treats_custom_workflow_as_external_reference(self) -> None:
        workflow = (ROOT / "skills" / "wily-workflow" / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            ROOT / "skills" / "wily-workflow" / "references" / "runner-adapter-contract.md"
        ).read_text(encoding="utf-8")

        combined = workflow + "\n" + reference
        self.assertIn("external workflow", combined)
        self.assertIn("reference-only", combined)
        self.assertNotIn("bundled default runner", combined)
        self.assertNotIn("runners/custom-workflow/runner.yaml", combined)
```

- [x] **Step 2: Replace `wily run` dispatch expectations**

In `tests/test_wily_cli.py`, replace `test_run_dispatches_ready_phase_to_custom_workflow_without_completing_it` with:

```python
def test_run_creates_external_workflow_handoff_without_bundled_runner(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        self.write_ready_phase(project)

        result = self.run_wily(project, "run", "01", "--runner", "custom-workflow")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Prepared phase 01 for external workflow", result.stdout)
        self.assertIn("Workflow: custom-workflow", result.stdout)
        self.assertIn("Reference-only handoff:", result.stdout)
        self.assertIn("/goal Execute Wily phase 01", result.stdout)

        roadmap = (project / ".wily" / "roadmap.yaml").read_text(encoding="utf-8")
        self.assertIn('status: "in_progress"', roadmap)
        self.assertNotIn('status: "done"', roadmap)
        session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
        status = (session / "status.yaml").read_text(encoding="utf-8")
        self.assertIn('status: "started"', status)
        self.assertNotIn("runner:", status)
        self.assertFalse((session / "runner").exists())
        self.assertTrue((session / "external-workflow-handoff.md").is_file())
        self.assertTrue((project / "agent-handoffs" / "01-first-phase-external-workflow.md").is_file())
```

- [x] **Step 3: Replace override/default tests**

Replace runner/autonomy tests with compatibility-label tests:

```python
def test_run_keeps_runner_and_autonomy_flags_as_external_workflow_metadata(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        self.write_ready_phase(project)

        result = self.run_wily(project, "run", "01", "--runner", "custom-workflow", "--autonomy", "conservative")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Workflow: custom-workflow", result.stdout)
        self.assertIn("Autonomy: conservative", result.stdout)
        session = next((project / ".wily" / "sessions").glob("*phase-01-attempt-1"))
        handoff = (session / "external-workflow-handoff.md").read_text(encoding="utf-8")
        self.assertIn("- External workflow: `custom-workflow`", handoff)
        self.assertIn("- Autonomy mode: `conservative`", handoff)
```

Delete tests that assert manifest default resolution:

- `test_run_prefers_phase_metadata_before_project_defaults`
- `test_run_uses_project_defaults_before_runner_manifest_defaults`

- [x] **Step 4: Replace archive/hook tests**

Delete bundled artifact archive and hook script tests:

- `test_complete_preserves_runner_metadata_and_snapshots_latest_runner_artifacts`
- `test_block_preserves_runner_metadata_and_snapshots_latest_runner_artifacts`
- `test_post_tool_use_capture_updates_runner_and_handoff_verification`
- `test_stop_guard_reads_wily_runner_status_and_autonomy`

Keep existing plain `complete`, `block`, and `retry` lifecycle tests.

- [x] **Step 5: Update command skill assertions**

In `tests/test_wily_command_skills.py`, replace `test_wily_run_documents_dispatch_surface_without_completion` assertions with:

```python
def test_wily_run_documents_external_workflow_handoff_without_completion(self) -> None:
    skill = (ROOT / "skills" / "wily-run" / "SKILL.md").read_text(encoding="utf-8")
    command = (ROOT / "commands" / "wily-run.md").read_text(encoding="utf-8")

    self.assertIn("$wily-run <phase-id> [--runner <external-workflow-id>]", skill)
    self.assertIn("reference-only external workflow handoff", skill)
    self.assertIn("does not execute Custom Workflow", skill)
    self.assertIn("does not require bundled runner files", skill)
    self.assertNotIn("bundled default", skill)
    self.assertNotIn("runners/custom-workflow", skill)
    self.assertIn("Run the `wily-run` skill", command)
    self.assertIn("reference-only external workflow handoff", command)
```

- [x] **Step 6: Run tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_wily_cli.ReferenceOnlyWorkflowTest \
  tests.test_wily_cli.WilyCliTest.test_run_creates_external_workflow_handoff_without_bundled_runner \
  tests.test_wily_command_skills.WilyCommandSkillsTest.test_wily_run_documents_external_workflow_handoff_without_completion
```

Expected: fail because the Custom Workflow bundle still exists, `$wily-run` still dispatches bundled artifacts, and skill docs still describe bundled dispatch.

## Task 2: Remove Bundled Assets And Refactor `wily_runner.py`

**Files:**
- Delete: `runners/custom-workflow/`
- Modify: `scripts/wily_runner.py`
- Modify: `scripts/wily.py`
- Test: `tests/test_wily_cli.py`

- [x] **Step 1: Delete bundled runner assets**

Run:

```bash
rm -rf runners/custom-workflow
```

Expected: `test_custom_workflow_bundle_is_not_part_of_live_plugin` now passes after code/docs are updated.

- [x] **Step 2: Replace `scripts/wily_runner.py` with reference-only handoff implementation**

Replace the bundled manifest/template implementation with this structure:

```python
#!/usr/bin/env python3
"""Prepare Wily phases for external workflow execution without bundling a runner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import wily
import wily_state_summary


Phase = dict[str, Any]
ALLOWED_AUTONOMY_MODES = {"conservative", "goal_scoped", "yolo"}


def parse_args(args: list[str]) -> tuple[str | None, str, str, str | None]:
    phase_id: str | None = None
    workflow = "external"
    autonomy_mode = "goal_scoped"
    error: str | None = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--runner":
            try:
                workflow = args[index + 1]
            except IndexError:
                error = "Missing value for --runner"
                break
            index += 2
            continue
        if arg == "--autonomy":
            try:
                autonomy_mode = args[index + 1]
            except IndexError:
                error = "Missing value for --autonomy"
                break
            index += 2
            continue
        if arg.startswith("--"):
            error = f"Unknown option: {arg}"
            break
        if phase_id is None:
            phase_id = arg
        else:
            error = f"Unexpected argument: {arg}"
            break
        index += 1
    return phase_id, workflow, autonomy_mode, error


def validate_autonomy(autonomy_mode: str) -> str | None:
    if autonomy_mode not in ALLOWED_AUTONOMY_MODES:
        return f"Unsupported autonomy mode: {autonomy_mode}"
    return None


def dependencies_done(phase: Phase, phases: list[Phase]) -> bool:
    return wily_state_summary.dependencies_done(phase, phases)


def phase_executable(phase: Phase, phases: list[Phase]) -> bool:
    status = str(phase.get("status") or "pending")
    if status in {"ready", "in_progress"}:
        return True
    return status == "pending" and dependencies_done(phase, phases)


def ensure_session(root: Path, phase: Phase, roadmap: dict[str, Any]) -> Path:
    session = wily.current_session_path(root, phase)
    if str(phase.get("status")) == "in_progress" and session is not None and session.exists():
        return session
    phase_id = str(phase.get("id", "unknown"))
    attempt = wily.next_attempt(root, phase_id)
    session = wily.create_session(root, phase, attempt)
    phase["status"] = "in_progress"
    phase["current_session"] = wily.relative_session_path(root, session)
    phase.pop("blocker", None)
    wily.save_roadmap(root, roadmap)
    return session


def slugify_phase(phase: Phase) -> str:
    phase_id = str(phase.get("id", "phase"))
    title = str(phase.get("title", "phase"))
    return f"{wily.phase_slug(phase_id)}-{wily.slugify_title(title)}"


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def native_goal_command(phase: Phase, workflow: str, autonomy_mode: str, handoff_path: Path, root: Path) -> str:
    phase_id = str(phase.get("id", "unknown"))
    title = str(phase.get("title", "Untitled phase"))
    handoff_ref = relative_to_root(root, handoff_path)
    return (
        f"/goal Execute Wily phase {phase_id}: {title}. "
        f"Use external workflow {workflow} with {autonomy_mode} autonomy. "
        f"Read {handoff_ref}. Do not mark the Wily phase done; "
        "record verification evidence and finish with a recommended Wily status."
    )
```

Continue the replacement with:

```python
def render_handoff(phase: Phase, workflow: str, autonomy_mode: str, session: Path, root: Path) -> str:
    phase_id = str(phase.get("id", "unknown"))
    title = str(phase.get("title", "Untitled phase"))
    phase_folder = root / ".wily" / str(phase.get("path"))
    phase_context, _planner = wily.phase_context_bundle(phase_id, title, phase_folder)
    return "\n".join(
        [
            "# Wily External Workflow Handoff",
            "",
            f"- Phase ID: `{phase_id}`",
            f"- Phase title: `{title}`",
            f"- External workflow: `{workflow}`",
            f"- Autonomy mode: `{autonomy_mode}`",
            f"- Wily session: `{relative_to_root(root, session)}`",
            f"- Git status: `{wily_state_summary.git_status(root)}`",
            "",
            "## Contract",
            "",
            "- This handoff is reference-only.",
            "- Wily does not bundle or execute the external workflow.",
            "- Do not mark the Wily phase done from the external workflow.",
            "- After verification evidence exists, complete the phase with `python3 scripts/wily.py complete <phase-id>`.",
            "- If blocked, use `python3 scripts/wily.py block <phase-id> \"<reason>\"`.",
            "",
            "## Phase Context",
            "",
            phase_context.strip(),
            "",
        ]
    )


def write_external_handoff(root: Path, phase: Phase, workflow: str, autonomy_mode: str, session: Path) -> dict[str, Path]:
    handoffs_dir = root / "agent-handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify_phase(phase)
    external_handoff = handoffs_dir / f"{slug}-external-workflow.md"
    session_handoff = session / "external-workflow-handoff.md"
    handoff_text = render_handoff(phase, workflow, autonomy_mode, session, root)
    external_handoff.write_text(handoff_text, encoding="utf-8")
    session_handoff.write_text(handoff_text, encoding="utf-8")
    return {
        "session": session,
        "external_handoff": external_handoff,
        "session_handoff": session_handoff,
    }
```

Then finish `command_run` without manifest loading:

```python
def command_run(root: Path, args: list[str]) -> int:
    phase_id, workflow, autonomy_mode, error = parse_args(args)
    if error:
        print(error, file=sys.stderr)
        return 2
    if not phase_id:
        print("Usage: wily.py run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]", file=sys.stderr)
        return 2
    autonomy_error = validate_autonomy(autonomy_mode)
    if autonomy_error:
        print(autonomy_error, file=sys.stderr)
        return 2

    roadmap = wily.load_roadmap(root)
    phases = roadmap.get("phases") or []
    phase = wily.find_phase(roadmap, phase_id)
    if phase is None:
        print(f"Phase not found: {phase_id}", file=sys.stderr)
        return 1
    if not phase_executable(phase, phases):
        print(f"Phase is not executable: {phase_id}", file=sys.stderr)
        return 1

    session = ensure_session(root, phase, roadmap)
    artifacts = write_external_handoff(root, phase, workflow, autonomy_mode, session)
    goal_command = native_goal_command(phase, workflow, autonomy_mode, artifacts["external_handoff"], root)

    print(f"Prepared phase {phase_id} for external workflow")
    print(f"Workflow: {workflow}")
    print(f"Autonomy: {autonomy_mode}")
    print(f"Session: {session}")
    print(f"Reference-only handoff: {artifacts['external_handoff']}")
    print("Native goal command:")
    print(goal_command)
    return 0
```

Do not add runner manifest code back.

- [x] **Step 3: Keep completion/block runner snapshot tolerant**

Do not remove this tolerant behavior from `scripts/wily.py`:

```python
def snapshot_runner_session(root: Path, phase: Phase, recommended_status: str) -> None:
    try:
        import wily_runner
    except ImportError:
        return
    wily_runner.snapshot_runner_artifacts(root, phase, recommended_status)
```

Instead, after replacing `scripts/wily_runner.py`, either add this no-op to the new module:

```python
def snapshot_runner_artifacts(root: Path, phase: Phase, recommended_status: str) -> None:
    return None
```

or update `scripts/wily.py` to check `hasattr(wily_runner, "snapshot_runner_artifacts")` before calling it.

Add a direct script entrypoint at the end of `scripts/wily_runner.py`:

```python
def snapshot_runner_artifacts(root: Path, phase: Phase, recommended_status: str) -> None:
    return None


def main(argv: list[str] | None = None) -> int:
    return command_run(Path.cwd(), list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run focused CLI tests**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WilyCliTest.test_run_creates_external_workflow_handoff_without_bundled_runner \
  tests.test_wily_cli.WilyCliTest.test_run_keeps_runner_and_autonomy_flags_as_external_workflow_metadata \
  tests.test_wily_cli.WilyCliTest.test_complete_marks_phase_done_and_session_verified \
  tests.test_wily_cli.WilyCliTest.test_block_marks_phase_blocked_and_records_reason
```

Expected: all pass.

## Task 3: Update Live Skills, Commands, And Manifest

**Files:**
- Modify: `skills/wily-run/SKILL.md`
- Modify: `commands/wily-run.md`
- Modify: `skills/wily-workflow/SKILL.md`
- Modify: `skills/wily-workflow/references/runner-adapter-contract.md`
- Modify: `.codex-plugin/plugin.json`
- Test: `tests/test_wily_command_skills.py`

- [x] **Step 1: Rewrite `$wily-run` skill**

Replace bundled dispatch wording in `skills/wily-run/SKILL.md` with:

```markdown
# Wily Run

Use `$wily-run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]` to prepare a selected Wily phase for an external workflow.

This is state-changing. It starts or attaches a Wily session and writes a reference-only external workflow handoff. It does not execute Custom Workflow, does not require bundled runner files, and must not mark the phase `done`.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]
```

## Boundaries

- Custom Workflow is external/reference-only.
- Wily does not bundle, install, or execute Custom Workflow.
- `--runner` is a workflow label for handoff text, not a local adapter lookup.
- The command creates `agent-handoffs/<phase>-external-workflow.md` and `.wily/sessions/<session>/external-workflow-handoff.md`.
- Final completion remains `$wily-complete <phase-id>` after verification evidence exists.
```

Keep the existing Korean response-style line.

- [x] **Step 2: Rewrite Claude command wrapper**

Update `commands/wily-run.md` to say:

```markdown
Run the `wily-run` skill to prepare a reference-only external workflow handoff.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/wily.py run <phase-id> [--runner <external-workflow-id>] [--autonomy conservative|goal_scoped|yolo]`. This does not execute Custom Workflow and does not require bundled runner files. Verified completion remains a later `/wily-complete <phase-id>` action.
```

- [x] **Step 3: Update workflow skill and reference doc**

In `skills/wily-workflow/SKILL.md`, replace bundled default runner wording with:

```markdown
External workflows such as Custom Workflow may be used by reference. Wily can prepare a phase handoff with `$wily-run`, but Wily does not bundle or execute those workflows.
```

In `skills/wily-workflow/references/runner-adapter-contract.md`, replace the contents with a short reference-only contract:

```markdown
# External Workflow Reference

Wily owns roadmap memory, phase lifecycle, and completion history.

External workflows such as Custom Workflow may execute a selected phase, but they are not bundled into Wily and are not required for core Wily behavior.

`$wily-run` creates a reference-only handoff:

- phase context
- Wily session path
- suggested native `/goal` command
- autonomy mode label
- completion/block instructions

The external workflow must not mark Wily phases done directly. After verification evidence exists, return to Wily and run `$wily-complete <phase-id>`. If blocked, run `$wily-block <phase-id> "<reason>"`.

Remote and destructive actions remain approval-first.
```

- [x] **Step 4: Update plugin default prompt**

Change `.codex-plugin/plugin.json` default prompt:

```json
"$wily-run <phase-id>: prepare a reference-only external workflow handoff"
```

- [x] **Step 5: Run command skill tests**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: pass.

## Task 4: Remove Or Downgrade Watch Runner Artifact Assumptions

**Files:**
- Read: `scripts/wily_watch_ui.py`
- Modify: `skills/wily-watch/SKILL.md`
- Read: `tests/test_wily_watch_ui.py`

- [x] **Step 1: Keep generic session progress only if wording is generic**

If keeping `_runner_status_detail`, leave the code generic because it reads `.wily/sessions/<session>/runner/` only when present. Do not mention Custom Workflow.

Update `skills/wily-watch/SKILL.md` line:

```markdown
- When a phase has external workflow progress artifacts under `.wily/sessions/<session>/runner/`, phase lines may include compact progress such as `runner in_progress` or `runner needs_review`.
```

If the implementation removes runner archives entirely, delete `_runner_status_detail` and its call sites, then update tests accordingly.

- [x] **Step 2: Prefer minimal change**

Do not remove generic watch progress in this phase unless tests or live guidance still imply bundled Custom Workflow. The important requirement is removing bundled assets and Custom Workflow-specific assumptions.

- [x] **Step 3: Run watch tests**

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui
```

Expected: pass.

## Task 5: Live Reference Scan And Cleanup

**Files:**
- Modify any live file reported by the scan: `.codex-plugin`, `README.md`, `skills`, `commands`, `scripts`, `tests`

- [x] **Step 1: Run live reference scan**

Run:

```bash
rg -n "bundled runner|runners/custom-workflow|custom-workflow|Custom Workflow" .codex-plugin README.md skills commands scripts tests
```

Expected after cleanup:

- no `runners/custom-workflow` references
- no `bundled runner` references
- `Custom Workflow` may appear only in reference-only wording
- `custom-workflow` may appear only as an example external workflow label in tests/docs

- [x] **Step 2: Update stale files found by scan**

For each stale match, change the wording to one of:

```text
external workflow
reference-only external workflow
external workflow label such as custom-workflow
```

Do not edit historical docs under `docs/superpowers/specs`, `docs/superpowers/plans`, or completed `.wily/phases/09-*` unless they are imported by live plugin guidance.

- [x] **Step 3: Re-run scan**

Run the same `rg` command again.

Expected: only reference-only matches remain.

## Task 6: Verification And Wily Session Completion

**Files:**
- Modify: `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/result.md`
- Modify: `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/changed-files.md`
- Modify: `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/verification.md`
- Modify via command: `.wily/roadmap.yaml`

- [x] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills tests.test_wily_cli tests.test_wily_watch_ui
```

Expected: pass.

- [x] **Step 2: Run full suite**

Run:

```bash
python3 -m unittest discover
```

Expected: pass.

- [x] **Step 3: Validate JSON and compile scripts**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py scripts/wily_watch_ui.py scripts/wily_runner.py
```

Expected: both commands exit `0`.

- [x] **Step 4: Record session result**

Update `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/result.md`:

```markdown
# Result

Removed bundled Custom Workflow runner integration from live Wily behavior.

Summary:

- Removed `runners/custom-workflow/`.
- Converted `$wily-run` to reference-only external workflow handoff generation.
- Removed live tests that required bundled Custom Workflow assets.
- Updated Wily skills and command wrappers to describe Custom Workflow as external/reference-only.
- Preserved historical 09-* roadmap records.
```

- [x] **Step 5: Record changed files**

Update `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/changed-files.md` with all modified/deleted paths. Include at least:

```markdown
# Changed Files

- `runners/custom-workflow/` deleted
- `scripts/wily_runner.py`
- `skills/wily-run/SKILL.md`
- `commands/wily-run.md`
- `skills/wily-workflow/SKILL.md`
- `skills/wily-workflow/references/runner-adapter-contract.md`
- `.codex-plugin/plugin.json`
- `tests/test_wily_cli.py`
- `tests/test_wily_command_skills.py`
- `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/*`
```

- [x] **Step 6: Record verification evidence**

Update `.wily/sessions/2026-05-14-224704-phase-11-1-attempt-1/verification.md` with command outputs from Steps 1-3 and the final reference scan summary.

- [x] **Step 7: Complete the Wily phase**

Run:

```bash
python3 scripts/wily.py complete 11-1
```

Expected:

```text
Completed phase 11-1
```

- [x] **Step 8: Confirm roadmap state**

Run:

```bash
python3 scripts/wily.py status
python3 scripts/wily.py next
```

Expected:

```text
25/25 - 100%
Next phase: none
```

## Self-Review Notes

- Spec coverage: the plan removes bundled assets, removes bundled dispatch assumptions, updates skills/docs/tests, preserves completed history, and verifies live reference-only wording.
- Scope: this is one cohesive reversal phase. It touches runner integration, command docs, and tests together because the bundled assumption is cross-cutting.
- Decision recorded: keep `$wily-run` as a reference-only handoff command instead of removing it. This preserves user-facing command compatibility while removing bundled Custom Workflow behavior.
