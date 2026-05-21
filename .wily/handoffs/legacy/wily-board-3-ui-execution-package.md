# Execution Package: Wily Board Plan 3 UI SSE Realtime

## Native Goal Command

```text
/goal Implement Wily Board v3 Plan 3 UI, SSE, and real-time behavior according to agent-handoffs/wily-board-3-ui-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-board-3-ui-progress.md.

Keep agent-handoffs/wily-board-3-ui-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not broaden scope beyond Plan 3. Work only toward the server-rendered dashboard/detail UI, SSE broker/route, snapshot and heartbeat event publishing, static client behavior, docs, and listed verification.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Done only when all Plan 3 acceptance criteria are satisfied and final verification passes: cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run pytest -v; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .
```

## Source Request / Handoff

User requested Custom Workflow goal execution for:

`/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.claude/worktrees/wily-board-plans-2-3/docs/superpowers/plans/2026-05-19-wily-board-3-ui.md`

The plan title is "Wily Board v3 - Plan 3: UI · SSE · Real-time".

## Inline Requirements

Outcome: make `/Users/wilycastle/Code/projects/wily-plugin/wily-board` visible and realtime with server-rendered Jinja pages, htmx partial refreshes, authenticated SSE, presence indicators, project cards, detail pages, activity timelines, parallel swim-lanes, and docs.

In scope:
- Add `sse-starlette`, an in-process `SseBroker`, `/sse`, and broker publish hooks in `/agent/snapshot` and `/agent/heartbeat`.
- Add personal/collab tab SQL helpers, card/detail view-models, templates, static JS/CSS, and tests.
- Preserve Plan 1 and Plan 2 behavior and their tests.
- Update README/deploy notes for Plan 3 acceptance.

Non-goals:
- No write UI for tasks.
- No external integrations, hooks, MCP servers, app integrations, deployment, SSH, push, or PR unless explicitly requested later.
- No unrelated refactors.

Assumptions:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board` is the implementation repo.
- The Plan 3 file in `.claude/worktrees/wily-board-plans-2-3` is authoritative even though it is not present in the main plan directory.
- Existing dirty files in `wily-board` are Plan 2/user-owned and must be preserved while making compatible edits.

## Acceptance Criteria

- `/web/dashboard` renders authenticated personal and collab tabs.
- Project cards show focus task, status, checkpoint gauge, blocker, parallel metadata, counts, and collab presence chips.
- `/web/projects/<id>` renders status-grouped tasks, checkpoint timeline, `result.md`, activity timeline from checkpoint events and commits, and parallel lane view.
- `/sse` rejects unauthenticated clients and streams `project_updated`, `presence`, and ping events to authenticated sessions.
- `/agent/snapshot` publishes `project_updated` only when ingest is not a noop.
- `/agent/heartbeat` publishes `presence`.
- Browser client reconnects EventSource, triggers htmx card swaps, updates connection dot, and supports dark mode toggle.
- Realtime smoke test proves agent push reaches browser SSE stream.
- Final server and agent tests plus lint pass or any residual failures are documented with evidence.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/pyproject.toml`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/uv.lock`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/agent.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sse/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_sse_*.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_agent_publishes_events.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_*.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/deploy.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/wily-board-3-ui-*.md`
- Must not edit:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/**`
  - unrelated dirty files in either repo
  - remote servers or external systems
- User-owned or pre-existing changes to preserve:
  - `wily-roadmap` dirty files and handoffs from prior tasks.
  - `wily-board` Plan 2 dirty files: README, agent package, parser/API tests and contract files.

## Execution Plan

1. Create runtime handoff/status/progress files.
2. Add SSE dependency, broker, route, main app wiring, and targeted tests.
3. Publish broker events from snapshot and heartbeat endpoints with tests.
4. Add tab classification and card view-model with tests.
5. Add dashboard templates/routes/static htmx asset and render tests.
6. Add detail view-model, templates, and detail/parallel-lane tests.
7. Add client JS/CSS behavior and realtime smoke test.
8. Update README/deploy docs.
9. Run final server tests, agent tests, server lint, and agent lint.

## Autonomous Action Policy

- Goal-scoped local edits, dependency sync via `uv`, and test/lint execution may proceed.
- Do not perform remote SSH/deploy/push/PR.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, edits outside ownership boundaries, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/wily-board-3-ui-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence: after every checkpoint status or verification state change.

## Superpowers Skill Routing

- Available: yes.
- `custom-workflow-skillset:plan-goal-runner`: outer runtime.
- `superpowers:subagent-driven-development`: used with a bounded read-only explorer; implementation remains root-owned because Plan 3 edits are tightly coupled.
- `superpowers:test-driven-development`: active for behavior changes.
- `superpowers:verification-before-completion`: required before final done.
- `superpowers:systematic-debugging`: use if verification failures repeat or are non-obvious.

## Superpowers Autonomy Override

- Active because the user explicitly requested autonomous Custom Workflow execution.
- Superpowers approval/review/continue prompts are converted into progress/evidence checkpoints.
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-board-3-ui-progress.md`

Live status board:
- `agent-handoffs/wily-board-3-ui-status.md`

Verification evidence:
- `agent-handoffs/wily-board-3-ui-verification.md`

Baseline:
- `wily-roadmap`: dirty before this goal; preserve unrelated changes.
- `wily-board`: branch `feat/v3-rewrite`; Plan 2 changes are dirty and must be preserved.

Checkpoint loop:
1. Mark next checkpoint RUNNING in status.
2. Make a focused change.
3. Run relevant verification.
4. Append progress and evidence.
5. Continue until DONE, PARTIAL, or BLOCKED.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS
Reason: read-only exploration/review lanes are safe. Implementation tasks touch overlapping web/server files, so root executor owns code changes sequentially.

## Lane Handoffs

### Lane A - Existing Repo Pattern Explorer
Agent: Huygens
Mode: read_only_evidence
Allowed files: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/**`
Must not edit: all files
Task: summarize existing patterns, mismatches with Plan 3 snippets, dirty-file risks, and verification commands.
Completion evidence: concise summary returned in thread.

## Sequential Gates

- Do not proceed to final done until full server and agent verification has fresh evidence.
- If a target file has user-owned changes unrelated to Plan 3, preserve them and continue only when safe.

## Verification Plan

- Targeted checkpoint tests from Plan 3.
- Final server suite: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest -v`
- Final agent suite: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run pytest -v`
- Server lint: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run ruff check .`
- Agent lint: `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/agent && uv run ruff check .`

## Rollback / Stop Conditions

- Same verification failure repeats twice without new evidence.
- Acceptance criteria cannot be verified locally.
- A required change needs remote deployment, secrets, hard destructive commands, or files outside the ownership boundary.

## Reviewer Notes

- Architect: Plan 3 fits the existing FastAPI/Jinja/SQLite stack and keeps UI read-only.
- Critic: SSE tests may need careful ASGI streaming handling; htmx vendoring should avoid network reliance if possible.
