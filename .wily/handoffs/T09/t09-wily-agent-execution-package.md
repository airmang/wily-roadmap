# Execution Package: T09 wily-agent daemon packaging

## Native Goal Command

```text
/goal Complete Wily Task T09 according to agent-handoffs/t09-wily-agent-execution-package.md.

First read the execution package. Maintain agent-handoffs/t09-wily-agent-progress.md.

Keep agent-handoffs/t09-wily-agent-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py; python3 plugins/wily-roadmap/scripts/wily.py agent check --offline; python3 plugins/wily-roadmap/scripts/wily.py agent status --json.
```

## Source Request / Handoff

User asked to process all ready Wily tasks with `custom-workflow-skillset`. Per Wily sequencing, this package covers the first claimed task, T09.

## Inline Requirements

Outcome: package `wily-agent` as part of the Wily Roadmap plugin and expose `wily agent` management commands.

In scope: CLI dispatch, agent package code, local registry/config/launchd helpers, best-effort signed Board heartbeat/live event publishing, docs, skill, manifest/default prompt, and focused tests.

Non-goals: production Board deployment, remote registration side effects during tests, shell startup mutation, real launchd install outside explicit user command, and completing T08 before T09 is verified.

Assumptions: Board accepts signed `POST /api/live/events` payloads using `X-Wily-Signature: sha256=<hmac>` and supports phase/item identity compatible with Wily v3 task ids.

## Acceptance Criteria

- Plugin contains installable `wily-agent` source or launcher.
- `wily agent install/configure/start/stop/status/check` commands exist, with foreground/dev and register support for smoke and T08.
- macOS launchd start/stop and foreground/dev paths are documented.
- Agent watches registered `.wily` repos and best-effort sends signed heartbeat/live events.
- Board outage, missing secret, and agent absence do not fail existing Wily commands.
- Onboarding docs and smoke tests verify the post-upgrade install flow.

## File / Ownership Boundaries

- Expected touchpoints:
  - `plugins/wily-roadmap/scripts/wily/cli/agent.py`
  - `plugins/wily-roadmap/scripts/wily/cli/__main__.py`
  - `plugins/wily-roadmap/scripts/wily/agent/**`
  - `plugins/wily-roadmap/commands/agent.md`
  - `plugins/wily-roadmap/skills/wily-agent/SKILL.md`
  - `plugins/wily-roadmap/.codex-plugin/plugin.json`
  - `plugins/wily-roadmap/README.md`
  - `plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Must not edit:
  - Board server repo files.
  - Remote configuration, secrets, shell startup, or real launchd state during tests.
- User-owned or pre-existing changes to preserve:
  - Current dirty tree includes T06/T07 implementation, `.wily/tasks.yaml`, root `AGENTS.md`, `CLAUDE.md`, agent handoffs, and hooks. Do not revert or normalize unrelated changes.

## Execution Plan

1. RED tests: add failing core and surface tests for `wily agent` dispatch, offline check/status, config/register, launchd plist generation, docs/skill/manifest exposure, and best-effort publisher behavior.
2. Implementation: add `wily.agent` package with config, registry, signing/publishing, launchd plist generation, daemon loop, and CLI wrapper. Keep network and launchctl calls opt-in and best-effort.
3. Docs and surface: add command docs, skill instructions, README onboarding, and manifest prompt entries.
4. Verification: run targeted T09 tests, full v3 unittest suite, offline smoke commands, and scope drift check.
5. Wily closeout: record checkpoints in `.wily/tasks/T09/progress.jsonl`; run `wily done T09` only after verification.

Verdict: PARALLEL_SAFE_WITH_LIMITS. Read-only explorer/reviewer lanes are safe. Implementation is sequential because `test_v3_core.py`, `test_v3_surface.py`, and CLI dispatch are shared. Implementation subagents must not edit shared files unless the package is revised with disjoint ownership.

Reviewer gates:
- Repo explorer: CLI dispatch conventions, command module shape, and T09-scope dirty changes.
- Agent explorer: reusable Board/heartbeat/daemon contracts.
- Test reviewer: RED test placement and verification commands.
- completion_verifier: run after final tests and before `wily done T09`.
- integration_reviewer: run before closeout if implementation touches more than the expected T09 files.

## Rollback / Stop Conditions

Rollback/recovery note:
- Do not revert user changes. If T09 changes must be backed out, remove only files added for T09 and reverse only hunks clearly introduced for T09.
- If launchd command execution is accidentally attempted, stop, report the exact command and result, and do not retry without explicit user approval.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Do not run real `launchctl bootstrap/bootout`, production Board calls, remote pushes, PRs, or destructive cleanup under this package.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, edits outside the package, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/t09-wily-agent-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, subagent lane, Superpowers auto-resolution, or final state changes
- Required visible fields:
  - State: PLANNING | RUNNING | VERIFYING | DONE | PARTIAL | BLOCKED
  - Objective
  - Progress count and percentage
  - Current checkpoint/action
  - Next checkpoint
  - Checkpoint table
  - Verification table
  - Recent events

## Superpowers Skill Routing

- Available: yes
- Required before implementation:
  - `Superpowers:test-driven-development` for behavior changes.
  - `Superpowers:systematic-debugging` for failures.
- Required before done:
  - `Superpowers:verification-before-completion`
- Conditional:
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` for bounded read-only review lanes only.

## Superpowers Autonomy Override

- Active because a native goal is active and the user requested Custom Workflow execution.
- Superpowers approval/review/continue prompts are progress checkpoints, not user gates.
- User input is required only for narrow hard-stop conditions.

Active goal auto-resolution log:
- Auto-resolved under active /goal: Superpowers TDD approval gate -> apply RED/GREEN locally because T09 has explicit acceptance criteria and a scoped execution package.
- Auto-resolved under active /goal: Custom Workflow plan review gate -> use bounded read-only subagents and validator evidence, then continue without waiting for a human review checkpoint.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/t09-wily-agent-progress.md`

Live status board:
- `agent-handoffs/t09-wily-agent-status.md`

Verification evidence:
- `agent-handoffs/t09-wily-agent-verification.md`

Baseline:
- Current git status: dirty before T09; preserve pre-existing changes.
- Initial failing/passing verification: to be recorded during RED tests.
- Known broken tests unrelated to this task: unknown until verification.

User / pre-existing changes:
- Pre-existing modified files include `.wily/tasks.yaml`, CLI modules, docs, skills, and tests from T06/T07.
- Pre-existing untracked files include `.claude/`, `CLAUDE.md`, `plugins/wily-roadmap/scripts/wily/hooks/`, several `agent-handoffs/`, and `.wily/tasks/T06/T07`.
- Must not overwrite user changes.
- If a target file has user changes unrelated to T09, preserve them and continue when possible.

Checkpoint loop:
1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log:
   - checkpoint name
   - files changed
   - commands run
   - result
   - evidence file updates, if any
   - status board update
   - next step
   - blockers / risks
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED`.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing CLI dispatch or package boundaries.
- After any failed verification retry.

Narrow hard-stop conditions:
- Hard destructive shell command.
- Payment/purchase action.
- Credential or secret exfiltration.
- Explicit user-forbidden action.
- Edits outside the execution package.
- Same verification failure repeated twice without new evidence.

Final verification:
- `python3 -m unittest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `python3 plugins/wily-roadmap/scripts/wily.py agent check --offline`
- `python3 plugins/wily-roadmap/scripts/wily.py agent status --json`
