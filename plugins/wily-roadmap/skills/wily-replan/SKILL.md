---
name: wily-replan
description: Use when the user types $wily-replan to add, revise, drop, assign, or commit Wily tasks.
---

# Wily Replan

Stage task list edits in `.wily/init/draft.yaml`, validate dependencies, and commit changes to `tasks.yaml`.

## Routing Contract

- If the user gives a natural-language work request after `$wily-replan`, treat it as a request to create or revise a Roadmap Task.
- Do not implement the requested work while handling `$wily-replan`.
- Convert the requested work into a concise task title plus intent, acceptance, scope, dependencies, and assignee when enough context exists.
- Use `replan add`, `replan revise-task`, `replan assign`, and `replan commit` to update `tasks.yaml`.
- If details are missing, add the smallest clear ready task or report the missing blocker instead of editing implementation files.
- After committing the task-list change, stop after the task draft is committed and tell the user the new/updated task id and the next command to run.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py replan [add|revise-task|drop|assign|project|commit|cancel]
```

## Behavior

- State-changing: only `commit` updates durable task state.
- Done tasks cannot be dropped and non-cosmetic done-task edits are rejected.
- Natural-language work requests must produce Roadmap Task changes, not direct code or document changes.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
