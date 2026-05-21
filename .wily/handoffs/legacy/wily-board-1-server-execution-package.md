# Execution Package: Wily Board Plan 1 Server Foundation

## Native Goal Command

```text
/goal Complete Wily Board v3 Plan 1 server foundation and agent ingest API according to agent-handoffs/wily-board-1-server-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-board-1-server-progress.md.

Keep agent-handoffs/wily-board-1-server-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands outside the plan, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: uv run ruff check .; uv run ruff format --check .; uv run pytest -v.
```

## Source Request / Handoff

User requested:

```text
$custom-workflow-skillset:plan-goal-runner docs/superpowers/plans/2026-05-19-wily-board-1-server.md 구현해줘.
```

Primary plan: `docs/superpowers/plans/2026-05-19-wily-board-1-server.md`.
Primary spec: `docs/superpowers/specs/2026-05-19-wily-board-v3-design.md`.

## Inline Requirements

Outcome: build the `wily-board` server foundation as a Python FastAPI + SQLite service with GitHub OAuth shell and `/agent/*` ingest API.

In scope:
- Preserve the existing v2 repo history, then create or use a scoped `feat/v3-rewrite` v3 rewrite branch in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.
- Implement Plan 1 tasks 1-19: tooling, config, schema/migrations, repo helpers, parser, merge policy, sessions, OAuth, org allowlist, machine code minting, agent register/snapshot/heartbeat, web login shell, main wiring, deploy artifacts, smoke test, README/deploy docs.
- Keep the service local-first and approval-first for real remote deployment. Do not SSH or deploy unless verification reveals a local-only blocker that the plan explicitly requires remote diagnosis.

Non-goals:
- No UI cards, no SSE, no realtime browser updates.
- No wily-agent daemon.
- No remote production deployment.

Assumptions:
- Existing `/Users/wilycastle/Code/projects/wily-plugin/wily-board` is the legacy v2 repo referenced by the plan.
- Rewriting tracked files on an orphan branch is goal-scoped and preserves legacy history.
- `uv` is available locally.

## Acceptance Criteria

- `wily-board` has a FastAPI server skeleton matching the file structure and behavior in Plan 1.
- SQLite schema creates all v3 tables from spec section 6.
- `POST /agent/register` exchanges one-time machine codes for bearer tokens and stores only token hashes.
- `POST /agent/snapshot` authenticates bearer tokens, parses the contract payload, stores snapshots, applies last-write-wins rows, and idempotently appends cp/commit rows.
- `POST /agent/heartbeat` updates machine `last_seen` and `actor_presence`.
- GitHub OAuth start/callback is mockable and session-based.
- R-W-LAB org allowlist helper is implemented.
- Minimal login/web shell and machine mint endpoint exist.
- Deploy files and README/deploy runbook exist.
- Verification passes: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -v`.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-board-1-server-*.md`
- Must not edit:
  - `plugins/wily-roadmap/**`
  - existing unrelated `wily-roadmap` modified/untracked files
  - remote servers unless explicitly needed and recorded
- User-owned or pre-existing changes to preserve:
  - Existing `wily-roadmap` dirty files from initial status.
  - Existing `wily-board` v2 history by using a rewrite branch rather than erasing history.

## Execution Plan

1. Baseline and branch:
   - Record current statuses.
   - In `wily-board`, create/switch to `feat/v3-rewrite` from an empty tree when needed.
   - Remove tracked v2 files only on that branch.
2. Scaffold and dependencies:
   - Create Python 3.12 package metadata, README, gitignore, package dirs.
   - `uv sync --extra dev`.
3. Foundation modules:
   - Config, SQLite schema/migrator, repo helpers.
   - Parser and merge policy with contract fixture.
4. Auth and API modules:
   - Session middleware, GitHub OAuth, org allowlist.
   - Machine code mint, agent register, snapshot, heartbeat.
5. Web/main/deploy:
   - Jinja login shell/static CSS, main app wiring.
   - Deploy artifacts and docs.
6. Verification:
   - Run targeted tests as needed while implementing.
   - Final `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -v`.
   - Use reviewer/verifier agents for final evidence if helpful.

## Autonomous Action Policy

- Goal-scoped external engineering actions may proceed without user approval.
- This includes local branch creation and local commits if useful.
- Remote SSH, push, PR, or production changes are not required by this execution package and should not be performed unless a narrow verification blocker makes them necessary.
- Record externally visible actions in the progress log.
- Stop only for hard destructive shell commands outside this plan, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/wily-board-1-server-status.md`
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
  - `Superpowers:test-driven-development` for behavior changes: read and active; plan provides tests first, but existing v2 rewrite may use batch red/green checkpoints.
  - `Superpowers:subagent-driven-development`: read and active as a method module. Native `/goal` owns orchestration.
  - `Superpowers:systematic-debugging` for failures: load if verification fails unexpectedly.
- Required before done:
  - `Superpowers:verification-before-completion`
- Conditional:
  - `Superpowers:writing-plans`: covered by this execution package.
  - `Superpowers:using-git-worktrees`: skipped; target plan calls for a branch in the existing repo, not a separate worktree.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: use read-only/review subagents and only disjoint implementation lanes if needed.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch`: use final review evidence; no PR/merge unless requested.

## Superpowers Autonomy Override

- Active because the user requested autonomous execution through `plan-goal-runner`.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-board-1-server-progress.md`

Live status board:
- `agent-handoffs/wily-board-1-server-status.md`

Verification evidence:
- `agent-handoffs/wily-board-1-server-verification.md`

Baseline:
- Current git status:
  - `wily-roadmap`: existing modified `AGENTS.md`; multiple untracked handoffs/docs from prior work.
  - `wily-board`: clean at initial inspection.
- Initial failing/passing verification:
  - Not run before branch rewrite.
- Known broken tests unrelated to this task:
  - Unknown until final suite.

User / pre-existing changes:
- Pre-existing modified files:
  - `wily-roadmap/AGENTS.md`
- Pre-existing untracked files:
  - Existing `wily-roadmap` `.claude/`, `CLAUDE.md`, handoffs, and Plan/Spec docs.
- Must not overwrite user changes:
  - Preserve all unrelated `wily-roadmap` files.
  - Preserve `wily-board` v2 history through branch/history, not by retaining v2 files in v3 branch.

Checkpoint loop:
1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint when practical.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log with files changed, commands run, result, evidence, next step, blockers/risks.
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before public API/schema changes.
- After any failed verification retry.

Narrow hard-stop conditions:
- Acceptance criteria cannot be verified.
- Same failure repeats twice without new evidence.
- Required change touches files outside the execution package and cannot be kept in scope.
- Hard destructive shell command outside this plan is needed.
- Payment/purchase action is needed.
- Credential or secret exfiltration risk is discovered.
- Explicit user-forbidden action is needed.
- Existing behavior risk is discovered that is not covered by the plan and cannot be mitigated within scope.
- Tests fail in a way that cannot be attributed to the current change.

Finalization:
1. Run full verification commands.
2. Use completion/review evidence.
3. Update status to DONE, PARTIAL, or BLOCKED.
4. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: implementation touches one new service repo and shared API/db contracts. Sequential root implementation is safest. Read-only exploration and final review lanes are safe. Parallel implementation is only safe for disjoint file groups after branch/scaffold exists.

## Lane Handoffs

### Lane A — repo facts
Agent: explorer
Mode: read_only_evidence
Timebox: 10 minutes
Allowed files: read `wily-board`, plan, spec
Must not edit: all files
Task: confirm v2/v3 rewrite strategy, useful preservation facts, verification commands, blockers.
Completion evidence: concise repo facts report.
Dependencies: none.

### Lane B — final review
Agent: reviewer/verifier
Mode: review_verification
Timebox: 15 minutes
Allowed files: read final diff and run read-only commands
Must not edit: source files
Task: check Plan 1 acceptance and surface gaps before final.
Completion evidence: review report.
Dependencies: implementation complete.

## Sequential Gates

- Do not start rewrite until branch/history preservation is decided.
- Do not claim done until final verification commands pass or failures are documented.
- Do not use SSH unless local implementation/verification requires it.

## Reviewer Gates

- Repo explorer gate: complete read-only repo facts before branch rewrite.
- Architect/critic gate: validate that orphan v3 branch strategy fits the plan; record any deviations in the progress log.
- `completion_verifier`: run or emulate with fresh evidence after final verification commands and before reporting `DONE`.
- `integration_reviewer`: required if implementation diverges from the plan-provided module boundaries or introduces multi-component coupling beyond Plan 1.

## Verification Plan

Targeted during implementation:
- `uv run pytest tests/test_config.py -v`
- `uv run pytest tests/test_db_schema.py tests/test_db_repo.py -v`
- `uv run pytest tests/test_parsers_wily_state.py tests/test_merge_policy_tasks.py tests/test_merge_policy_append.py -v`
- `uv run pytest tests/test_auth_sessions.py tests/test_auth_github_oauth.py tests/test_auth_allowlist.py -v`
- `uv run pytest tests/test_api_machines.py tests/test_api_agent_register.py tests/test_api_agent_snapshot.py tests/test_api_agent_heartbeat.py -v`
- `uv run pytest tests/test_web_routes.py tests/test_main_app.py tests/test_smoke_end_to_end.py -v`

Final:
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -v`

## Rollback / Stop Conditions

- To rollback local v3 branch work: switch back to the original branch or previous commit; v2 history is preserved.
- Stop if orphan branch creation would overwrite uncommitted `wily-board` changes.
- Stop if verification requires secrets or remote credentials.

## Reviewer Notes

- Architect: pending.
- Critic: pending.
