# Execution Package: Stage 30 Board DAG Components Mobile

## Native Goal Command

```text
/goal Complete Stage 30 Board DAG Components Mobile according to agent-handoffs/stage-30-board-dag-components-mobile-execution-package.md.

First read the execution package. Maintain agent-handoffs/stage-30-board-dag-components-mobile-progress.md.

Keep agent-handoffs/stage-30-board-dag-components-mobile-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build; cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest when backend assumptions require it; browser smoke for desktop and 375px mobile.
```

## Source Request / Handoff

- User requested autonomous execution of Stage 30 from `docs/superpowers/plans/2026-05-18-stage-30-board-dag-components-mobile.md`.
- Roadmap stage source: `.wily/stages/s30-board-dag-components-mobile/stage.yaml`.
- Implementation repo: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`.

## Inline Requirements

Outcome: complete Stage 30 board workspace polish in the Wily Board frontend: dependency-aware DAG layout, extracted Headline and Attention components, mobile stage-list fallback plus local desk bottom sheet, and repo switcher/list ordering polish.

In scope: frontend-only changes under `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend` plus handoff evidence in this repository.

Non-goals: backend API mutations, Tremor dependency, changes to marketplace metadata, reverting unrelated dirty work, hooks/MCP/apps.

Assumptions: existing `RepoDetail`, `Stage`, `DeskPayload`, and `RepoGroups` shapes are sufficient; `@dagrejs/dagre` and `@radix-ui/react-progress` are available; active dirty files from earlier stages are user/pre-existing changes to preserve.

## Acceptance Criteria

- Stage map uses `@dagrejs/dagre` with dependency-aware LR layout while preserving Done prefix collapse, status styling, React Flow controls, minimap, background, motion, and animated in-progress edges.
- Repo workspace uses focused `RepoHeadline` and `RepoAttention` components; Headline uses local `Progress`; Attention renders only when items exist and uses shadcn Alert rows.
- Repo switcher groups Shared and Personal repos, sorts pinned first then recent then alphabetical, shows pinned stars, and remembers selected repos.
- Hub repo lists reuse the same deterministic pinned-first ordering without recent override.
- Below 600px, React Flow is hidden and a vertical mobile stage list is shown; local desk rail is hidden and available through the mobile bar bottom sheet.
- `npm run lint` and `npm run build` pass after edits; backend tests run if API assumptions change.
- Browser smoke confirms desktop and 375px mobile behavior.

## File / Ownership Boundaries

- Expected touchpoints in `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend`:
  - `components/stage-map.tsx`
  - `components/repo-workspace.tsx`
  - `components/repo-headline.tsx`
  - `components/repo-attention.tsx`
  - `components/local-desk.tsx`
  - `components/repo-switcher.tsx`
  - `components/repo-list.tsx`
  - `lib/storage.ts`
  - optional `lib/repo-ordering.ts`
  - `app/globals.css`
- Handoff touchpoints in this repo:
  - `agent-handoffs/stage-30-board-dag-components-mobile-*.md`
- Must not edit: backend API behavior, generated `frontend/lib/api-types.ts`, marketplace `.agents/plugins/marketplace.json`, plugin manifest, unrelated dirty files.
- User-owned or pre-existing changes to preserve: all pre-existing dirty files in `/Users/wilycastle/Code/projects/wily-plugin/wily-board` and `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` unless listed above.

## Execution Plan

1. CP00 Preflight: record dirty status, package availability, Tremor absence, baseline `npm run lint`, baseline `npm run build`.
2. CP01 Parallel Lane A: implement dagre layout in `stage-map.tsx`.
3. CP02 Parallel Lane B: add `RepoHeadline`, `RepoAttention`, integrate in `repo-workspace.tsx`.
4. CP03 Parallel Lane C: add recent storage/order helper, update switcher/list grouping and pin display.
5. CP04 Serial integration: add mobile stage list and local desk bottom-sheet fallback; adjust mobile CSS.
6. CP05 Final verification: lint/build, backend tests if needed, browser desktop/mobile smoke, completion review, status/progress/evidence update.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- No branch push, PR open/update, issue mutation, merge, or deployment is planned for this Stage 30 execution.
- Record externally visible actions if they become goal-scoped.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/stage-30-board-dag-components-mobile-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence: after each checkpoint, verification command, blocker, subagent lane, Superpowers auto-resolution, or final state change.
- Required visible fields: State, Objective, progress count and percentage, current action, next checkpoint, checkpoint table, verification table, recent events.

## Superpowers Skill Routing

- Available: yes.
- Required before implementation:
  - `Superpowers:test-driven-development` for behavior changes: routed; no dedicated test harness exists for these UI-only behaviors, so use baseline lint/build plus browser smoke and focused component/code review as equivalent evidence.
  - `Superpowers:systematic-debugging` for failures: use if lint/build/browser verification fails.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:using-git-worktrees`: skipped; workspace is dirty but Stage 30 target files are explicit and the user asked for current workspace completion.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development`: active for disjoint lanes A/B/C.
  - `Superpowers:requesting-code-review`: adapted through bounded completion/integration review before done.

## Superpowers Autonomy Override

- Active because native `/goal` is active and the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during this run.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/stage-30-board-dag-components-mobile-progress.md`

Live status board:
- `agent-handoffs/stage-30-board-dag-components-mobile-status.md`

Verification evidence:
- `agent-handoffs/stage-30-board-dag-components-mobile-verification.md`

Baseline:
- Current git status: dirty in both `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` and `/Users/wilycastle/Code/projects/wily-plugin/wily-board`; preserve unrelated changes.
- Initial passing verification:
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm ls @xyflow/react framer-motion cmdk @radix-ui/react-dialog @radix-ui/react-tooltip @radix-ui/react-progress @dagrejs/dagre --depth=0`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && node -e "const p=require('./package.json'); console.log(p.dependencies['@tremor/react'] || 'absent')"`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint`
  - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build`
- Known broken tests unrelated to this task: none found in frontend baseline.

User / pre-existing changes:
- Pre-existing modified files: many Stage 28/29 files in both repos before this run; do not revert.
- Pre-existing untracked files: `.wily/stages/s25...s31`, prior handoffs, frontend shadcn/Next files, tests, fixtures.
- Must not overwrite user changes: inspect each target before editing; use narrow patches.

Checkpoint loop:
1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log with checkpoint name, files changed, commands run, result, evidence updates, status update, next step, blockers/risks.
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing component boundaries.
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
2. Record evidence in verification file.
3. Run `completion_verifier` for final acceptance coverage.
4. Run `integration_reviewer` for multi-lane frontend integration.
5. Update status to DONE, PARTIAL, or BLOCKED.
6. Produce final summary with diff, tests, risks, and remaining issues.

## Parallelization Decision

Verdict: PARALLEL_SAFE_WITH_LIMITS

Reason: lanes A, B, and C have disjoint ownership after serial dependency preflight. Lane D depends on Lane A and touches mobile/CSS integration, so it must run after the first wave.

## Lane Handoffs

### Lane A - DAG Layout

Agent: worker
Mode: implementation_disjoint
Timebox: 30 minutes
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
Must not edit:
- `repo-workspace.tsx`, `local-desk.tsx`, `repo-switcher.tsx`, `repo-list.tsx`, `storage.ts`, CSS unless explicitly coordinated.
Task: replace zigzag positioning with dagre LR layout, preserve Done prefix behavior and React Flow affordances.
Completion evidence: diff summary and `npm run lint` if feasible.
Dependencies: CP00.

### Lane B - Headline And Attention

Agent: worker
Mode: implementation_disjoint
Timebox: 30 minutes
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-headline.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-attention.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-workspace.tsx`
Must not edit:
- `stage-map.tsx`, `local-desk.tsx`, switcher/list/storage files, CSS unless explicitly coordinated.
Task: extract Headline and Attention components, use local Progress, integrate render-only attention alerts.
Completion evidence: diff summary and `npm run lint` if feasible.
Dependencies: CP00.

### Lane C - Repo Switcher And Pin Polish

Agent: worker
Mode: implementation_disjoint
Timebox: 30 minutes
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/storage.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/repo-ordering.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
Must not edit:
- `stage-map.tsx`, `repo-workspace.tsx`, `local-desk.tsx`, CSS unless explicitly coordinated.
Task: add recent repo storage, deterministic ordering helper, grouped command palette, pin star display, and Hub list ordering reuse.
Completion evidence: diff summary and `npm run lint` if feasible.
Dependencies: CP00.

### Lane D - Mobile Fallback

Agent: root
Mode: sequential_required
Timebox: 30 minutes
Allowed files:
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`
Must not edit:
- Lane B/C files unless integration requires it.
Task: render mobile stage list from final visible stage sequence, ensure React Flow hidden below 600px, hide rail, expose mobile local desk bottom sheet.
Completion evidence: lint/build and browser mobile smoke.
Dependencies: Lane A; first-wave integration.

## Sequential Gates

- CP00 must finish before lane dispatch.
- Lane D must wait for Lane A and first-wave review.
- Final browser verification waits for all lanes and build success.

## Verification Plan

- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint`
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run build`
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest` only if API/backend assumptions change.
- Browser smoke with local frontend/backend: desktop repo workspace and 375px mobile.

## Rollback / Stop Conditions

- Revert only own Stage 30 edits if needed; never clean unrelated dirty files.
- Stop for hard-stop conditions listed in the Goal Runtime Contract.
- If browser verification cannot authenticate or seed data, record limitation and use build/static evidence plus reachable routes.

## Reviewer Notes

- Architect: plan follows existing frontend boundaries and preserves read-only API assumptions.
- Critic: execution is bounded; primary risk is dirty workspace overlap, mitigated by explicit lane ownership and final integration review.
