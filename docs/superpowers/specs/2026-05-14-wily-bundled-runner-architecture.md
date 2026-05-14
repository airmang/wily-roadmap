# Wily Bundled Runner Architecture

**Date:** 2026-05-14

**Status:** design handoff for Codex implementation

**Goal:** Keep Wily Roadmap as the engine-agnostic roadmap protocol while bundling Custom Workflow as the default phase execution runner.

---

## Decision

Wily Roadmap should include Custom Workflow as a **bundled default runner**, not absorb it into Wily core.

Correct framing:

```text
Wily Roadmap = roadmap protocol, phase/session state, history, replan
Custom Workflow = default bundled execution runner
Light / Claude / Hermes / manual = future runner adapters
```

Wrong framing:

```text
Wily Roadmap becomes Custom Workflow
Custom Workflow logic is hardcoded into scripts/wily.py
```

The long-term value of Wily is that it can select and dispatch any runner while preserving the same `.wily/` project memory and execution history.

---

## Why This Direction

Wily was originally designed so execution engines can be swapped.

That means Custom Workflow should be treated as the first strong runner implementation:

- Wily decides **what phase** should run.
- Wily owns **dependencies, status, attempts, history, replan**.
- Custom Workflow decides **how to execute one selected phase** through planning, `/goal`, progress, verification, and reviewer gates.
- Runner output is archived back into the Wily session.

This keeps future upgrades clean:

```text
custom-workflow v0.3.7
custom-workflow v0.4.0
light-runner v1
claude-code-runner
hermes-runner
manual-runner
```

Only the runner adapter changes. `.wily/roadmap.yaml` and completed session history remain stable.

---

## Architecture Layers

```text
Wily Core
  - .wily/roadmap.yaml
  - .wily/phases/*
  - .wily/sessions/*
  - .wily/revisions/*
  - state transitions
  - runner selection
  - runner output archive

Runner Adapter Contract
  - reads phase context bundle
  - writes execution artifacts
  - reports result, verification, blockers, changed files
  - recommends next Wily phase status

Bundled Custom Workflow Runner
  - deep-interview
  - plan-goal-runner
  - parallel-lane-runner
  - custom agents
  - execution package
  - status board
  - progress log
  - verification evidence
  - completion/integration review
```

---

## Runner Contract

Every runner should follow the same minimum contract.

### Input

From Wily to runner:

```text
phase_id
phase title
phase path
phase.md
planner.md
prompt.md
verification.md
handoff.md
roadmap context
current git status summary
current session path
autonomy mode
```

### Output

From runner back to Wily:

```text
result summary
verification evidence
changed files
progress log
status board or equivalent
blockers
recommended phase status: needs_review | blocked | ready | done
raw runner artifacts
```

### Archive Location

Runtime files may live in runner-native paths while the run is active, but final artifacts must be archived under the Wily session:

```text
.wily/sessions/<timestamp>-phase-<id>-attempt-<n>/
  input.md
  result.md
  verification.md
  changed-files.md
  status.yaml
  runner/
    runner.yaml
    input.md
    execution-package.md
    progress.md
    verification.md
    status-board.md
    raw-output.md
```

Recommended source-of-truth split:

- Active execution source of truth: runner-native files such as `agent-handoffs/`.
- Durable Wily history source of truth: `.wily/sessions/<session>/runner/` snapshot.

---

## Bundled Runner Layout

Add a runner directory instead of mixing Custom Workflow code directly into Wily core:

```text
runners/
  custom-workflow/
    runner.yaml
    AGENTS.md                    # optional runner-local guidance
    skills/
      deep-interview/
      plan-goal-runner/
      parallel-lane-runner/
    agents/
      repo_explorer.toml
      requirements_analyst.toml
      plan_architect.toml
      plan_critic.toml
      parallel_planner.toml
      parallel_implementer.toml
      parallel_verifier.toml
      verification_runner.toml
      completion_verifier.toml
      integration_reviewer.toml
      security_reviewer.toml
      api_reviewer.toml
      performance_reviewer.toml
      test_engineer.toml
      external_researcher.toml
    scripts/
      status_board.py
      validate_execution_package.py
      watch_status.py
      pre_tool_use_safety_guard.py
      post_tool_use_verification_capture.py
      stop_goal_incomplete_guard.py
    hooks/
      hooks.json                 # optional integration, not required for core use
```

The plugin may also expose these skills through the normal plugin `skills/` directory if Codex discovery requires it. If so, keep the runner-local copy as the canonical bundled runner source or make the top-level skills thin wrappers that route into the runner.

---

## Runner Manifest

Create:

```text
runners/custom-workflow/runner.yaml
```

Suggested schema:

```yaml
id: custom-workflow
name: Custom Workflow
version: "0.3.7"
adapter_version: 1
default: true

entrypoints:
  interview_skill: runners/custom-workflow/skills/deep-interview/SKILL.md
  plan_skill: runners/custom-workflow/skills/plan-goal-runner/SKILL.md
  parallel_skill: runners/custom-workflow/skills/parallel-lane-runner/SKILL.md

capabilities:
  - requirements_interview
  - execution_package
  - native_goal_command
  - progress_log
  - status_board
  - verification_evidence
  - bounded_subagents
  - completion_review
  - integration_review

artifacts:
  handoffs_dir: agent-handoffs
  execution_package: agent-handoffs/{slug}-execution-package.md
  status_board: agent-handoffs/{slug}-status.md
  progress: agent-handoffs/{slug}-progress.md
  verification: agent-handoffs/{slug}-verification.md

autonomy_modes:
  default: goal_scoped
  supported:
    - conservative
    - goal_scoped
    - yolo

policy:
  remote_actions_default: require_approval
  destructive_actions_default: require_approval
  archive_outputs_to_wily_session: true
```

Keep this file small and stable. It is the adapter contract, not an implementation guide.

---

## Autonomy Modes

Wily should own the autonomy policy passed to runners.

```yaml
autonomy_mode: conservative | goal_scoped | yolo
```

### `conservative`

Use for sensitive repos or shared work.

- local edits require normal agent judgment
- remote actions require explicit approval
- destructive actions require explicit approval
- push, PR, merge, GitHub comments require explicit approval

### `goal_scoped`

Recommended default.

- local implementation and verification can continue within the approved phase
- dependency installs may proceed when clearly phase-scoped and non-destructive
- remote actions still require explicit approval
- destructive actions still require explicit approval
- avoids unnecessary stopping during long local work

### `yolo`

Use only for explicit autonomous runs in safe repos.

- goal-scoped engineering actions may proceed without approval
- hard stops still apply:
  - broad destructive shell commands
  - payment/purchase
  - credential or secret exfiltration
  - actions explicitly forbidden by the user or execution package
  - repeated verification failure without new evidence

Default for bundled Custom Workflow must be:

```yaml
default_autonomy_mode: goal_scoped
```

Do not inherit Custom Workflow's original YOLO default unchanged.

---

## Phase Metadata

Wily phases may recommend a runner without depending on that runner.

Example in `.wily/roadmap.yaml`:

```yaml
- id: "09-1"
  title: "Bundle Custom Workflow runner"
  path: "phases/09-1-bundle-custom-workflow-runner"
  status: "ready"
  depends_on: ["08-1"]
  parallel_group: "09"
  runner:
    preferred: custom-workflow
    min_version: "0.3.7"
    autonomy_mode: goal_scoped
```

Alternative or complementary phase file metadata in `planner.md`:

```md
Recommended runner: custom-workflow:plan-goal-runner
Autonomy mode: goal_scoped
```

Do not require every phase to declare a runner. If absent, Wily uses the default runner from config or bundled manifest.

---

## Session Metadata

When a phase is run, record the actual runner used.

Example in `.wily/sessions/<session>/status.yaml`:

```yaml
phase_id: "09-1"
status: started
runner:
  id: custom-workflow
  version: "0.3.7"
  adapter_version: 1
  autonomy_mode: goal_scoped
  started_at: "2026-05-14T00:00:00Z"
  artifacts:
    execution_package: runner/execution-package.md
    status_board: runner/status-board.md
    progress: runner/progress.md
    verification: runner/verification.md
```

The session records reality. Even if phase metadata later changes, old sessions remain auditable.

---

## New Command: `wily-run`

Add a new command/skill pair:

```text
$wily-run <phase-id> [--runner <id>] [--autonomy conservative|goal_scoped|yolo]
/wily-run <phase-id> [--runner <id>] [--autonomy conservative|goal_scoped|yolo]
```

### Purpose

Dispatch a selected Wily phase to a runner.

### Default Behavior

```text
$wily-run 09-1
```

means:

```text
runner = custom-workflow
autonomy_mode = goal_scoped
```

unless phase metadata or project config overrides it.

### Responsibilities

`wily-run` should:

1. Read applicable `AGENTS.md`.
2. Read `.wily/roadmap.yaml`.
3. Validate phase exists and is executable.
4. Resolve runner:
   - CLI flag
   - phase metadata
   - project default
   - bundled default
5. Resolve autonomy mode:
   - CLI flag
   - phase metadata
   - project default
   - runner default
6. Start or attach Wily session:
   - use existing `wily.py start <phase-id>` behavior where possible
7. Build phase context bundle.
8. Create runner input under session archive and runner-native handoff path.
9. For Custom Workflow:
   - create `agent-handoffs/<slug>-execution-package.md`
   - create `agent-handoffs/<slug>-status.md`
   - create `agent-handoffs/<slug>-progress.md`
   - create `agent-handoffs/<slug>-verification.md`
   - include exact `/goal` command when the current environment cannot set it directly
10. Stop after dispatch unless the runtime can safely continue inside an active goal.
11. Never mark the phase `done` directly from dispatch.

### Status Flow

Recommended phase state flow:

```text
ready
  -> wily-run / wily-start
  -> in_progress
  -> runner executes
  -> needs_review | blocked
  -> completion_verifier / integration_reviewer
  -> wily-complete
  -> done
```

`wily-run` may move `ready` to `in_progress`, but final `done` requires verification evidence and completion handling.

---

## Custom Workflow Execution Package Additions

When Custom Workflow is used as the runner, include Wily metadata in the execution package.

Add this section:

```md
## Wily Phase Metadata

- Phase ID: `<id>`
- Phase title: `<title>`
- Wily phase path: `.wily/phases/<phase-dir>`
- Wily session: `.wily/sessions/<session-dir>`
- Runner: `custom-workflow`
- Runner version: `0.3.7`
- Autonomy mode: `goal_scoped`
- Completion command: `python3 scripts/wily.py complete <phase-id>`
- Block command: `python3 scripts/wily.py block <phase-id> "<reason>"`
```

Add Wily-specific finalization rules:

```md
## Wily Finalization Rules

- Do not mark the Wily phase `done` until verification evidence is recorded.
- If implementation succeeds, update runner progress and recommend `needs_review` or completion.
- If blocked, record blocker text suitable for `wily.py block`.
- Archive runner artifacts into the Wily session before final summary.
- Preserve completed phase history. Do not rewrite earlier Wily sessions.
```

---

## Hook Strategy

Hooks should be optional for v1 of the bundled runner.

Reason: Wily currently avoids hooks, MCP servers, and app integrations unless explicitly requested. The bundled runner can include hook files, but core Wily behavior should work without installing them.

Recommended phases:

### v1

- Bundle Custom Workflow skills, agents, scripts.
- Add `wily-run` dispatch.
- Generate execution packages/status boards.
- Archive runner artifacts to Wily session.
- No automatic hook installation.

### v2

- Make hooks opt-in.
- Teach hooks to read Wily phase metadata.
- PostToolUse evidence capture can append to both `agent-handoffs/*-verification.md` and session runner archive.
- Stop continuation guard can recognize Wily phase status and autonomy mode.

Hook policy must respect Wily autonomy mode:

```text
conservative -> strict approval gates
 goal_scoped -> continue local phase-scoped work, gate remote/destructive
        yolo -> Custom Workflow original behavior with hard stops
```

---

## Plugin Discovery Notes

Preserve current compatibility requirements:

- Keep `.codex-plugin/plugin.json` and `skills/` compatible with Codex plugin discovery.
- Keep `.claude-plugin/plugin.json` and `commands/` compatible with Claude Code slash command discovery.
- If runner-local skills are not discoverable directly, provide top-level wrapper skills:

```text
skills/wily-run/SKILL.md
skills/custom-workflow-plan-goal-runner/SKILL.md  # optional wrapper
```

The top-level Wily commands should remain the primary user interface. Custom Workflow internals should be exposed only when useful for direct expert use.

---

## Suggested Implementation Phases

### Phase A: Document and contract only

Files:

- Create `runners/custom-workflow/runner.yaml`.
- Create `skills/wily-workflow/references/runner-adapter-contract.md`.
- Update `skills/wily-workflow/SKILL.md` references.
- Add tests for manifest readability if a parser is introduced.

Verification:

```bash
python3 -m pytest tests/test_wily_command_skills.py -q
```

### Phase B: Bundle Custom Workflow files

Files:

- Add `runners/custom-workflow/skills/*`.
- Add `runners/custom-workflow/agents/*.toml`.
- Add `runners/custom-workflow/scripts/status_board.py`.
- Add `runners/custom-workflow/scripts/validate_execution_package.py`.
- Add `runners/custom-workflow/scripts/watch_status.py`.
- Add optional `runners/custom-workflow/hooks/hooks.json`.

Verification:

```bash
python3 -m compileall -q runners/custom-workflow
python3 runners/custom-workflow/scripts/validate_execution_package.py \
  runners/custom-workflow/skills/plan-goal-runner/templates/execution-package.md
```

### Phase C: Add `wily-run` command and skill

Files:

- Create `commands/wily-run.md`.
- Create `skills/wily-run/SKILL.md`.
- Update `.codex-plugin/plugin.json` default prompts if useful.
- Update `.claude-plugin/plugin.json` if command listing is needed.
- Add command skill test coverage.

Verification:

```bash
python3 -m pytest tests/test_wily_command_skills.py -q
```

### Phase D: Add runner dispatch helper

Files:

- Modify `scripts/wily.py` to add a `run` command or add a small dedicated helper such as `scripts/wily_runner.py`.
- Prefer keeping `scripts/wily.py` focused on state transitions. If dispatch grows beyond simple filesystem operations, use `scripts/wily_runner.py`.
- Add tests for runner resolution and session artifact creation.

Verification:

```bash
python3 -m pytest tests/test_wily_cli.py -q
```

### Phase E: Artifact archive and review handoff

Files:

- Add tests ensuring runner artifacts are copied or linked under `.wily/sessions/<session>/runner/`.
- Ensure `status.yaml` records runner metadata.
- Ensure `wily-run` does not mark phases done.

Verification:

```bash
python3 -m pytest -q
```

---

## Non-Goals for First Implementation

Do not do these in the first pass:

- Do not auto-install hooks globally.
- Do not make Custom Workflow the only possible runner.
- Do not change existing Wily phase/session history format incompatibly.
- Do not make `yolo` the default.
- Do not implement Light runner yet.
- Do not push, open PRs, or perform remote writes as part of the implementation unless explicitly requested.

---

## Open Questions for Codex Implementation

1. Should runner-local skills be canonical, or should top-level `skills/` hold canonical files with runner wrappers?
2. Should active Custom Workflow handoffs be copied into `.wily/sessions/.../runner/` immediately, or only snapshotted at completion/block?
3. Should `wily-run` be purely a dispatch/document-generation command, or may it invoke Codex-native `/goal` directly when available?
4. Where should project-level runner defaults live?
   - `.wily/config.yaml`
   - `.wily/project.md`
   - top-level plugin default only
5. Should `wily-watch` eventually show runner progress from `agent-handoffs/*-status.md` inside the phase node?

Recommended defaults:

- Canonical runner files under `runners/custom-workflow/`.
- Snapshot runner artifacts at dispatch and finalization; update during execution only when cheap.
- `wily-run` generates exact `/goal` command first; direct native invocation can come later.
- Put project defaults in `.wily/config.yaml` once config support exists.
- Add runner progress to `wily-watch` in a later phase, not first pass.

---

## Final Principle

Wily should stay the durable memory and orchestration protocol.

Custom Workflow should be the default muscle, not the skeleton.

```text
Wily = roadmap memory and phase lifecycle
Custom Workflow = bundled default execution runner
Runner contract = replaceable seam
```
