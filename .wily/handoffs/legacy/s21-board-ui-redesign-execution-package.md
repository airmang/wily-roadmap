# Execution Package: S21 Board UI Redesign

## Native Goal Command

```text
/goal Complete Wily Roadmap Stage s21 end to end according to agent-handoffs/s21-board-ui-redesign-execution-package.md.

First read the execution package. Maintain agent-handoffs/s21-board-ui-redesign-progress.md.

Keep agent-handoffs/s21-board-ui-redesign-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: uv run pytest; npm --prefix frontend run lint; npm --prefix frontend run build; browser smoke for hub and repo workspace.
```

## Source Request / Handoff

User request: implement all of S21 and adapt whenever the design does not match the current repository code so the work can proceed without errors.

Wily state:
- Stage `s21` is decomposed into phases `21-1` through `21-7`.
- Stage `s22` is complete and provides the live activity model consumed by this work.
- Design source: `docs/superpowers/specs/2026-05-16-wily-board-ui-redesign-design.md`.

## Inline Requirements

Outcome:
- Turn the existing `R-W-LAB/wily-board` FastAPI/Jinja/htmx dashboard into a read-only multi-repo work dashboard with a Next.js frontend and FastAPI read-only JSON/SSE backend.

In scope:
- Add read-only FastAPI JSON APIs and SSE stream while preserving existing sync/live ingestion behavior.
- Add a `frontend/` Next.js app in `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend`.
- Build hub, repo workspace, local desk, pinned repos, command palette, theme, responsive behavior, and read-only cutover.
- Remove Board mutation UI/action routes only after replacement surfaces exist.
- Update Wily roadmap state in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` as phases progress.

Non-goals:
- Do not alter durable `.wily` source-of-truth semantics.
- Do not add MCP servers, hooks, app integrations, payment/purchase steps, or secret exfiltration.
- Do not push/merge unless a later explicit user instruction asks for it.

Assumptions:
- The existing `wily-board` FastAPI app remains the backend and source of auth/session policy.
- The frontend subdirectory is the right deployment unit unless implementation discovers a hard blocker.
- If a spec detail conflicts with current code, prefer a smaller compatible implementation that satisfies the user-facing acceptance criteria.

## Acceptance Criteria

- FastAPI exposes authenticated read-only JSON endpoints for user, visible repos, repo detail, phase detail, global desk, repo desk, and SSE.
- JSON payloads keep durable state distinct from live overlay state.
- Next.js app builds successfully and renders the hub and repo workspace from the backend API.
- Hub shows MY DESK first, with working, up-next, blocked, shared repos, personal repos, progress, live badges, pins, and empty states.
- Repo workspace shows stage dependency map/list, done prefix grouping where practical, phase expansion, live chips, attention, and local desk.
- Command palette, theme toggle, rail/pin persistence, Korean-ish relative times, responsive layouts, and focusable controls are implemented.
- Old Board data-mutating UI is removed from the cutover surface.
- Python and frontend verification pass or any residual issue is documented with evidence.
- Wily s21 phase state is updated only after matching checkpoint verification.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/main.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/*`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/actions/*`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/*`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/*`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/deploy/*`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.wily/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/agent-handoffs/s21-board-ui-redesign-*`
- Must not edit:
  - unrelated repositories
  - secrets such as private keys, real env files, and OAuth/App credentials
  - user-owned untracked `.playwright-mcp/` artifacts unless needed only for new screenshots
- User-owned or pre-existing changes to preserve:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/docs/superpowers/specs/2026-05-16-wily-board-ui-redesign-design.md` is pre-existing untracked design input.
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.playwright-mcp/` is pre-existing untracked output.

## Execution Plan

Checkpoint 0: Baseline and package
- Record baseline repo facts and verification.
- Keep `agent-handoffs/s21-board-ui-redesign-status.md`, progress, and verification files updated.

Checkpoint 1: Contract reconciliation
- Update s21 phase `21-1` as the active work item.
- Convert design contradictions into implementation decisions:
  - preserve GitHub App sync auth even when action routes are removed;
  - choose one SSE path;
  - keep old Jinja routes until Next.js cutover;
  - adapt shadcn/Tailwind requirements to repo-compatible local components if package scaffolding or generated code is too heavy.
- Write tests that prove JSON routes are protected by session auth.

Checkpoint 2: FastAPI JSON/SSE
- Add focused API modules and response shaping helpers.
- Add tests for `/api/me`, `/api/repos`, `/api/desk`, `/api/repos/{owner}/{name}`, `/api/repos/{owner}/{name}/desk`, phase detail, and `/api/sse/live`.
- Keep current template routes green during this checkpoint.

Checkpoint 3: Frontend scaffold/auth
- Add Next.js app under `frontend/`.
- Configure TypeScript, lint/build scripts, CSS theme tokens, API client, cookie-forwarding fetch, and rewrites.
- Implement authenticated page shells and backend URL configuration.
- Run frontend lint/build once scaffold is present.

Checkpoint 4: Hub
- Build hub page using `/api/desk` and `/api/repos`.
- Implement MY DESK, repo groups, progress, live badge, pins, empty states, and SSE-driven refresh.
- Add frontend component tests if feasible; otherwise rely on build plus browser smoke.

Checkpoint 5: Repo workspace
- Build repo workspace using `/api/repos/{owner}/{name}` and repo desk.
- Implement graph/list stage map, done grouping, phase expansion, live chips, local desk rail, and attention.
- Keep mobile fallback stable.

Checkpoint 6: Polish
- Add command palette, theme toggle, rail persistence, relative time, toasts, keyboard/focus details, responsive polishing.
- Run browser smoke at desktop and mobile widths.

Checkpoint 7: Cutover and ops
- Route `/` and `/repos/...` to Next.js frontend without breaking auth, health, sync webhook, live event ingestion, or API.
- Remove action route registration and old mutation UI from the live surface.
- Update deploy docs/Caddy/service notes for the frontend.
- Run full verification and update Wily s21 phases to done where evidence supports it.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Do not push, merge, buy services, run hard destructive commands, or expose secrets.
- Network package installation for frontend dependencies is goal-scoped and allowed.
- Record externally visible or network actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/s21-board-ui-redesign-status.md`
- Intended use: keep this Markdown file open in Codex while the goal runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, Superpowers auto-resolution, or final state changes
- Required visible fields:
  - State
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
  - `Superpowers:test-driven-development` for backend API behavior and frontend behavior where test harness exists.
  - `Superpowers:systematic-debugging` for test/build/browser failures.
- Required before done:
  - `Superpowers:verification-before-completion`
- Conditional:
  - `Superpowers:writing-plans`: folded into this execution package.
  - `Superpowers:using-git-worktrees`: skipped; both involved repos are clean enough or already have goal-owned Wily state changes.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: skipped unless the user explicitly authorizes subagents; local root runner owns this goal.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch`: use as internal review/finalization checkpoints if needed.

## Superpowers Autonomy Override

- Active because a native goal is active and the user requested autonomous implementation.
- Superpowers approval/review/continue prompts are not user gates during this goal.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/s21-board-ui-redesign-progress.md`

Live status board:
- `agent-handoffs/s21-board-ui-redesign-status.md`

Verification evidence:
- `agent-handoffs/s21-board-ui-redesign-verification.md`

Baseline:
- Current git status:
  - `wily-roadmap`: goal-owned `.wily` s21 decomposition files modified/untracked, pre-existing `.playwright-mcp/` and design spec untracked.
  - `wily-board`: clean at start.
- Initial passing verification:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board`: `uv run pytest` -> 71 passed, 26 warnings.
- Known broken tests unrelated to this task:
  - none discovered.

User / pre-existing changes:
- Pre-existing modified files:
  - none in `/Users/wilycastle/Code/projects/wily-plugin/wily-board` at baseline.
  - goal-owned Wily state changes already exist in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`.
- Pre-existing untracked files:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.playwright-mcp/`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/docs/superpowers/specs/2026-05-16-wily-board-ui-redesign-design.md`
- Preserve pre-existing untracked design spec and `.playwright-mcp/`.
- Do not overwrite unrelated user changes if they appear later; work with them or stop only if safe editing is impossible.

Checkpoint loop:
1. Choose the next smallest checkpoint from this package.
2. Update the status board.
3. Make one focused change set.
4. Run targeted verification.
5. Update status and progress evidence.
6. Continue until DONE, PARTIAL, or BLOCKED unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing component boundaries.
- Before public API/schema/migration changes.
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
2. Use browser smoke for hub and repo workspace.
3. Re-read acceptance criteria and record evidence.
4. Update status to DONE, PARTIAL, or BLOCKED.
5. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: SEQUENTIAL_RECOMMENDED
Reason: backend API shape, frontend client types, route cutover, docs, and Wily state updates are tightly coupled. Parallel read-only review is useful, but implementation should stay under one root runner unless explicit subagent authorization is given.

## Lane Handoffs

### Lane A — Root Sequential Implementation

Agent: root Codex goal runner
Mode: sequential_required
Timebox: full goal
Allowed files: all Expected touchpoints above
Must not edit: secrets, unrelated repos, unrelated user changes
Task: implement checkpoints 0-7 in order
Completion evidence: verification log and final diff summary
Dependencies: none

## Sequential Gates

- Gate 1: API tests pass before frontend depends on them.
- Gate 2: frontend build passes before route cutover.
- Gate 3: old mutation UI/action routes are removed only after Next.js surfaces render.
- Gate 4: Wily phase completion updates happen only after checkpoint verification evidence exists.

## Reviewer Gates

- Architect gate: after Checkpoint 2, review API shape against the current `wily-board` code and the s21 design; record decision in progress log.
- Critic gate: before Checkpoint 7, review cutover risk, route ownership, auth behavior, and rollback path; record decision in progress log.
- Completion gate: before final answer, run verification-before-completion discipline, re-read acceptance criteria, and record pass/fail evidence.
- `completion_verifier`: run as a local final checklist against acceptance criteria and verification evidence.
- `integration_reviewer`: run as a local multi-component review before final DONE/PARTIAL because backend, frontend, docs, and Wily state are all touched.

## Verification Plan

- Baseline: `uv run pytest`
- Backend checkpoint: `uv run pytest tests/test_api_routes.py tests/test_web_routes.py tests/test_live_events.py`
- Frontend checkpoint: `npm --prefix frontend run lint`; `npm --prefix frontend run build`
- Full backend: `uv run pytest`
- Browser smoke: start FastAPI/Next dev servers, open hub and repo workspace, capture desktop/mobile screenshots or equivalent browser evidence.
- Wily state: `python3 plugins/wily-roadmap/scripts/wily.py status --once`; `python3 plugins/wily-roadmap/scripts/wily.py next`

## Rollback / Stop Conditions

- Backend API cannot be added without breaking existing sync/live ingestion.
- Next.js scaffold cannot build under local Node/npm after two distinct remediation attempts.
- Browser smoke shows core hub or repo workspace blank after two distinct remediation attempts.
- Required production deployment would need credentials or destructive server changes.

## Reviewer Notes

- Architect: local review required before cutover; preserve sync auth code while deleting mutation boundary.
- Critic: package must stay adaptive; spec details may be trimmed if repo-compatible implementation satisfies user-facing acceptance.
