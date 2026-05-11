# Routing Policy

## Goal

Decide how a user request maps to Wily roadmap work before editing files.

## Decision Labels

Use these labels in summaries when helpful:

- `direct_work`: no `.wily/` state is needed for a small local task.
- `init_roadmap`: create or refresh `.wily/` from the current repository baseline and user goal.
- `show_status`: summarize `.wily/roadmap.yaml`, ready phases, blockers, and progress.
- `select_phase`: recommend one or more ready phases.
- `execute_phase`: run an approved phase through a new session.
- `complete_phase`: mark a reviewed phase done after verification evidence is recorded.
- `block_phase`: record a blocker and stop execution.
- `retry_phase`: create another session for an unfinished phase.
- `replan_roadmap`: preserve completed history and revise future work.
- `needs_clarification`: the safe route is ambiguous.

## Rules

- If the user says `wily init`, inspect the repository before writing `.wily/`.
- If the user provides a final goal with init, use it. If not, summarize current state and ask for the goal.
- If `.wily/` exists and the user asks what to do next, read `roadmap.yaml` and recommend ready phases.
- If the user asks to implement, map the request to a phase. If no phase exists, ask whether to create roadmap state or handle the task directly.
- If multiple ready phases can run independently, present them as parallel candidates and recommend one.
- If the user changes the target after progress exists, use `replan_roadmap`, not a fresh phase-1 reset.
- If remote or destructive work is implied, stop and ask for explicit approval.
- Keep command routing fast. Do not invoke external planner adapters or run project verification while handling roadmap state commands.
- Use planner adapters only after the user explicitly continues into phase implementation and the phase needs a detailed implementation plan.
- Run verification only for implementation completion, and prefer the phase's focused verification over broad test suites.

## Init Output

`wily init` should create or update:

```text
.wily/project.md
.wily/roadmap.yaml
.wily/status.md
.wily/decisions.md
.wily/phases/
.wily/sessions/
.wily/revisions/
```

The first roadmap should include phase IDs, titles, statuses, dependencies, parallel groups, phase paths, and a clear next recommendation.

## Script Helper

Use `scripts/wily.py` for deterministic state operations:

```bash
python3 <plugin-root>/scripts/wily.py init "Goal text"
python3 <plugin-root>/scripts/wily.py status
python3 <plugin-root>/scripts/wily.py next
python3 <plugin-root>/scripts/wily.py start 04-1
python3 <plugin-root>/scripts/wily.py complete 04-1
python3 <plugin-root>/scripts/wily.py block 04-1 "Reason"
python3 <plugin-root>/scripts/wily.py retry 04-1
python3 <plugin-root>/scripts/wily.py replan "Reason"
python3 <plugin-root>/scripts/wily.py watch
```

The helper does not replace Codex judgment. It creates and reads files; Codex still scans the repository, designs phases, asks for approval, implements approved work, and records verification.
