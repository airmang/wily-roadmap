# Execution Package: Wily Board Sync Contract

## Native Goal Command

```text
/goal Complete the Wily Board sync contract implementation according to agent-handoffs/wily-board-sync-contract-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-board-sync-contract-progress.md.

Keep agent-handoffs/wily-board-sync-contract-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Do not stop merely because an action is externally visible if it is goal-scoped, including branch pushes, PR creation/updates, GitHub comments, issue duplicate/close actions, or PR merges after final verification. Continue through goal-scoped dependency, network, schema migration, and release steps when they are part of the objective or execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/wily-board-sync-contract-execution-package.md; python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py; python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py; python3 -m unittest discover plugins/wily-roadmap/tests.
```

## Source Request / Handoff

- User request: implement `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-board-sync-contract-requirements.md`, push `main` so plugin updates are available, and update the locally installed Wily Roadmap plugin cache so the current plugin reflects the changes.
- Requirements handoff: `agent-handoffs/wily-board-sync-contract-requirements.md`.

## Inline Requirements

Separate handoff exists; inline requirements are not needed. Summary: make Board reflection and verification a standard Wily contract for state-changing Wily commands, keep `.wily` local state authoritative, preserve Board failure recovery, document actual-site verification escalation, require Korean for Stage/Phase authoring, add deterministic checks, verify, push `main`, and update the installed plugin cache.

## Acceptance Criteria

- `wily-workflow` describes the Board reflection contract for state-changing Wily commands.
- State-changing precise skills mention Board reflection, deterministic evidence, actual-site visual escalation, and failure recovery.
- `wily-run` and runner adapter docs require Custom Workflow status/checkpoint state to sync through `checkpoint-sync` or an equivalent helper path.
- `wily-decompose-stage` explicitly requires local topology draft replay/verification after Stage decomposition.
- `wily-complete`, `wily-block`, and `wily-replan` describe Board-visible status update expectations and failure handling.
- Command docs under `plugins/wily-roadmap/commands/` stay aligned with matching skills.
- Board operations documentation exists in the plugin reference docs and describes config check, emit/replay, deterministic API/SSE/SSR evidence, conditional actual-site visual verification, and temporary auth cleanup.
- Stage and Phase authoring guidance requires Korean for human-readable titles, purpose/scope, task descriptions, prompts, verification notes, handoffs, and notes, while machine-facing fields stay English.
- CLI tests or deterministic checks cover at least one structural emit-result/resync-hint path.
- No secrets are committed or printed.
- No hooks, MCP servers, or app integrations are added.
- Final commit is pushed to `origin/main`.
- Current installed Wily Roadmap plugin cache reflects the pushed plugin implementation.

## File / Ownership Boundaries

- Expected touchpoints:
  - `agent-handoffs/wily-board-sync-contract-*.md`
  - `plugins/wily-roadmap/skills/wily-workflow/SKILL.md`
  - `plugins/wily-roadmap/skills/wily-workflow/references/*.md`
  - `plugins/wily-roadmap/skills/wily-{init,start,run,decompose-stage,complete,block,retry,replan,issues}/SKILL.md`
  - `plugins/wily-roadmap/commands/{init,start,run,decompose-stage,complete,block,retry,replan,issues}.md`
  - `plugins/wily-roadmap/tests/test_wily_command_skills.py`
  - `plugins/wily-roadmap/tests/test_wily_cli.py`
  - `plugins/wily-roadmap/scripts/wily.py`
  - installed plugin cache under `/Users/wilycastle/.codex/plugins/cache/wily-castle/wily-roadmap/0.1.0/`
- Must not edit:
  - `.agents/plugins/marketplace.json` except to preserve the existing marketplace pointer.
  - `.wily` roadmap/session/stage state except status/progress artifacts explicitly required by this execution package.
  - unrelated dirty files in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- User-owned or pre-existing changes to preserve:
  - `.wily/roadmap.yaml`
  - `.wily/status.md`
  - `.wily/revisions/2026-05-17-132403-replan-26.md`
  - `.wily/stages/s25-wily-board-ui-polish-usability/`
  - existing edits in `plugins/wily-roadmap/scripts/wily.py`
  - existing edits in `plugins/wily-roadmap/tests/test_wily_cli.py`
  - existing `agent-handoffs/board-live-local-state-*` and `agent-handoffs/p6-bridge-durable-sync-handoff.md`
  - untracked `.playwright-mcp/`

## Execution Plan

1. Create and validate this execution package, status board, progress log, and verification log.
2. Locally perform the `repo_explorer`, `parallel_planner`, `plan_architect`, and `plan_critic` checks because subagent spawning is not allowed without explicit user delegation in this interface.
3. Add failing contract tests in `plugins/wily-roadmap/tests/test_wily_command_skills.py` for Board reflection docs, command doc alignment, Board operations reference, runner adapter sync guidance, and Korean authoring guidance.
4. Run the focused command-skill tests and confirm the new tests fail for missing contract text.
5. Implement concise skill and command doc changes. Put detailed Board reflection policy in `skills/wily-workflow/references/board-reflection-contract.md`.
6. Add or adjust CLI/test support only where required, preserving the pre-existing `wily.py` and `test_wily_cli.py` changes.
7. Run focused tests after each checkpoint, then full plugin test discovery.
8. Review diff for secret leakage, scope drift, marketplace metadata preservation, and installed plugin compatibility.
9. Commit on `main`, push `origin/main`, and copy the updated plugin implementation into the currently installed plugin cache.

## Autonomous Action Policy

- Goal-scoped external engineering actions may proceed without user approval.
- This includes committing and pushing `main` because the user explicitly requested it.
- This does not include pushing unrelated `/Users/wilycastle/Code/projects/wily-plugin/wily-board` dirty work.
- Record externally visible actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/wily-board-sync-contract-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, Superpowers auto-resolution, or final state changes
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

- Available: yes.
- Required before implementation:
  - `Superpowers:test-driven-development` for behavior and deterministic documentation-test changes.
  - `Superpowers:systematic-debugging` for any failing or unexpected verification.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans` used; folded into this execution package rather than a separate `docs/superpowers` plan because `plan-goal-runner` requires `agent-handoffs/` runtime files.
  - `Superpowers:using-git-worktrees` skipped; user requested direct `main` push and repo already has relevant dirty work to preserve.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` skipped; no explicit user delegation permission in this tool environment.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch` adapted into local diff review and final push evidence because user explicitly requested push to `main`.

## Superpowers Autonomy Override

- Active when native `/goal` is active or the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-board-sync-contract-progress.md`

Live status board:
- `agent-handoffs/wily-board-sync-contract-status.md`

Verification evidence:
- `agent-handoffs/wily-board-sync-contract-verification.md`

Baseline:
- Current git status: `main...origin/main`; modified `.wily/roadmap.yaml`, `.wily/status.md`, `plugins/wily-roadmap/scripts/wily.py`, `plugins/wily-roadmap/tests/test_wily_cli.py`; untracked `.playwright-mcp/`, `.wily/revisions/2026-05-17-132403-replan-26.md`, `.wily/stages/s25-wily-board-ui-polish-usability/`, several existing `agent-handoffs/*` files, and the source requirements handoff.
- Initial failing/passing verification: to be recorded in `agent-handoffs/wily-board-sync-contract-verification.md`.
- Known broken tests unrelated to this task: unknown at start.

User / pre-existing changes:
- Pre-existing modified files: `.wily/roadmap.yaml`, `.wily/status.md`, `plugins/wily-roadmap/scripts/wily.py`, `plugins/wily-roadmap/tests/test_wily_cli.py`.
- Pre-existing untracked files: `.playwright-mcp/`, `.wily/revisions/2026-05-17-132403-replan-26.md`, `.wily/stages/s25-wily-board-ui-polish-usability/`, `agent-handoffs/board-live-local-state-*`, `agent-handoffs/p6-bridge-durable-sync-handoff.md`, `agent-handoffs/wily-board-sync-contract-requirements.md`.
- Must not overwrite user changes: preserve all pre-existing dirty state and only layer required edits.
- If a target file has user changes unrelated to this task, preserve them and continue when possible; stop only if safe editing is impossible.

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
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing component boundaries.
- Before public command/CLI contract changes.
- After any failed verification retry.

Narrow hard-stop conditions:
- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside the execution package and cannot be kept in scope.
- Hard destructive shell command is needed.
- Payment/purchase action is needed.
- Credential or secret exfiltration risk is discovered.
- Explicit user-forbidden action is needed.
- Existing behavior risk is discovered that is not covered by the plan and cannot be mitigated within scope.
- Tests fail in a way that cannot be attributed to the current change.

Finalization:
1. Run full verification commands.
2. Use command output as verification_runner evidence in `agent-handoffs/wily-board-sync-contract-verification.md`.
3. Run completion_verifier locally by checking acceptance criteria one by one against files and test output.
4. Run integration_reviewer locally by inspecting skill/docs/CLI consistency and installed cache state.
5. Update `agent-handoffs/wily-board-sync-contract-status.md` to DONE, PARTIAL, or BLOCKED.
6. Produce final summary with diff, tests, push/cache evidence, risks, and remaining issues.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED

Reason: docs, tests, and existing dirty CLI changes overlap. Parallel read-only review would be safe, but this interface forbids subagent dispatch without explicit delegation and the implementation is cohesive enough to keep local.

## Lane Handoffs

### Lane A - Local repo exploration and plan review

Agent: root Codex
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: all expected touchpoints
Must not edit: `.wily` roadmap state, unrelated `wily-board` dirty files
Task: collect repo facts, verify touchpoints, validate plan architecture and critic concerns locally
Completion evidence: progress log entries and execution package validator output
Dependencies: none

### Lane B - Sequential implementation

Agent: root Codex
Mode: sequential_required
Timebox: 45-90 minutes
Allowed files: expected touchpoints
Must not edit: unrelated dirty files
Task: add tests, implement contract docs/CLI support, verify, commit, push, update cache
Completion evidence: test outputs, git push output, cache diff/check output
Dependencies: Lane A

## Sequential Gates

- Gate 1: execution package validates before implementation.
- Gate 2: focused documentation tests fail before docs implementation.
- Gate 3: focused documentation tests pass after docs implementation.
- Gate 4: CLI tests and full plugin tests pass before commit.
- Gate 5: secret scan and diff review pass before push/cache update.
- Gate 6: installed plugin cache matches committed plugin files after push.

## Verification Plan

- `python3 /Users/wilycastle/.codex/plugins/cache/custom-workflow-skillset/custom-workflow-skillset/0.3.8/skills/plan-goal-runner/scripts/validate_execution_package.py agent-handoffs/wily-board-sync-contract-execution-package.md`
- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_command_skills.py`
- `python3 -m unittest plugins/wily-roadmap/tests/test_wily_cli.py`
- `python3 -m unittest discover plugins/wily-roadmap/tests`
- `git diff --check`
- Secret-oriented scan over changed files for obvious secret literals.
- Post-push: `git status --short --branch` and `git log -1 --oneline`.
- Cache check: compare updated plugin cache files against `plugins/wily-roadmap/` for touched plugin paths.

## Rollback / Stop Conditions

- If docs-only contract tests cannot be made stable without broad brittle assertions, reduce assertions to durable policy phrases and record the reason.
- If pre-existing `wily.py` / `test_wily_cli.py` edits conflict with required CLI changes, preserve existing edits and stop only if the target behavior cannot be added safely.
- If full tests expose unrelated failures, record the failing command and decide whether targeted acceptance is enough; do not hide failures.
- If push fails due auth or non-fast-forward, fetch/read status and stop before force-push.
- If installed cache update risks deleting user-local plugin files outside the Wily plugin root, stop.

## Reviewer Notes

- Architect: keep detailed policy in `wily-workflow/references/board-reflection-contract.md`; keep command skills concise with a shared contract pointer; use tests to pin durable phrases rather than every paragraph.
- Critic: high risk is stale/incomplete docs across skills and commands. Tests must cover both skill and command docs plus runner adapter and operations reference. Existing CLI changes appear to already add `board sync-local` and emit-result recording; preserve and cover rather than rewrite.
