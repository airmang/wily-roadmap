# Routing Policy

## Goal

Decide how a user request maps to Wily roadmap work before editing files.

## Decision Labels

Use these labels in summaries when helpful:

- `direct_work`: no `.wily/` state is needed for a small local task.
- `init_roadmap`: create or refresh `.wily/` from the current repository baseline and user goal.
- `show_status`: summarize `.wily/roadmap.yaml`, ready Stages or legacy phases, blockers, and progress.
- `select_phase`: recommend one or more ready Stages or phases.
- `execute_phase`: run an approved Stage or phase through a new session.
- `complete_phase`: mark a reviewed Stage or phase done after verification evidence is recorded.
- `block_phase`: record a blocker and stop execution.
- `retry_phase`: create another session for an unfinished Stage or phase.
- `replan_roadmap`: preserve completed history and revise future work.
- `needs_clarification`: the safe route is ambiguous.

## Rules

- If the user says `wily init`, inspect the repository before writing `.wily/`.
- If the user provides a final goal with init, use it. If not, summarize current state and ask for the goal.
- If `.wily/` exists and the user asks what to do next, read `roadmap.yaml` and recommend ready Stages or legacy phases.
- If the user asks to implement, map the request to a Stage or Phase. If no roadmap unit exists, ask whether to create roadmap state or handle the task directly.
- If multiple ready Stages can run independently, present them as parallel candidates and include `owner` plus `write_scope` when available.
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
.wily/stages/
.wily/phases/
.wily/sessions/
.wily/revisions/
```

The first roadmap should include Stage IDs, titles, statuses, dependencies, Stage paths, and a clear next recommendation. For collaboration, include `owner` and `write_scope` so safe parallel Stage assignment is visible. Child Phase creation belongs in explicit Stage decomposition, not init.

## Script Helper

Use `scripts/wily.py` for deterministic state operations:

```bash
python3 <plugin-root>/scripts/wily.py init "Goal text"
python3 <plugin-root>/scripts/wily.py status
python3 <plugin-root>/scripts/wily.py next
python3 <plugin-root>/scripts/wily.py start 04-1
python3 <plugin-root>/scripts/wily.py decompose-stage s01-core --from-json stage-plan.json
python3 <plugin-root>/scripts/wily.py complete 04-1
python3 <plugin-root>/scripts/wily.py block 04-1 "Reason"
python3 <plugin-root>/scripts/wily.py retry 04-1
python3 <plugin-root>/scripts/wily.py replan "Reason"
python3 <plugin-root>/scripts/wily.py watch
```

The helper does not replace agent judgment. It creates and reads files; the active agent still scans the repository, designs phases, asks for approval, implements approved work, and records verification.
