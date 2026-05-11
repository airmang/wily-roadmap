# Phase Execution Policy

## Execution Loop

1. Read `.wily/roadmap.yaml`.
2. Select a `ready` phase or the phase explicitly named by the user.
3. Show the phase purpose, dependencies, likely touched files, planner adapter, prompt, handoff, and verification.
4. Ask for approval before implementation.
5. Create a new session under `.wily/sessions/`.
   - Helper command: `python3 <plugin-root>/scripts/wily.py start <phase-id>`
6. Mark the phase `in_progress`.
7. If no detailed implementation plan exists and one is needed for implementation, use the recommended external planner before changing project files.
8. Implement only the approved phase.
9. Run focused phase verification.
10. Record result, changed files, verification output, planner used, and blockers in the session.
11. Mark the phase `needs_review`, `blocked`, or `done` based on the result and user approval.
    - Helper command for verified completion: `python3 <plugin-root>/scripts/wily.py complete <phase-id>`
    - Helper command for blockers: `python3 <plugin-root>/scripts/wily.py block <phase-id> "<reason>"`

## Session Status

Use these session statuses:

```text
started
needs_work
verified
blocked
abandoned
```

A session is an execution attempt. Do not overwrite older sessions when retrying a phase.

If the phase has `planner.md`, record its recommended planner in `status.yaml`. `plan.md` is optional and may be absent when the session starts.
Recording a planner is metadata only; starting or inspecting a phase must not invoke that planner by itself.

## Completion Criteria

A phase is ready for `done` only when:

- implementation matches the phase scope,
- verification ran or the reason it could not run is recorded,
- changed files are summarized,
- unrelated user changes were preserved,
- no hidden remote or destructive action occurred,
- the user has approved completion when review is needed.

## Retry Rule

If a phase fails or is interrupted, keep the existing session and create a new attempt:

```text
.wily/sessions/2026-05-11-phase-04-1-attempt-2/
```

Helper command:

```bash
python3 <plugin-root>/scripts/wily.py retry <phase-id>
```

The phase remains `blocked`, `needs_review`, or `ready` depending on the next safe action.

## Stop Conditions

Stop and report `needs_work` or `blocked` when:

- tests fail for a reason that is not understood,
- required credentials or permissions are missing,
- the requested scope conflicts with roadmap state,
- the implementation would cross into another phase,
- dirty worktree state would risk user changes,
- remote or destructive work is required but not approved.
