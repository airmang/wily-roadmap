---
name: wily-done
description: Use when the user types $wily-done after a task has been verified.
---

# Wily Done

Mark an in-progress task done and write `.wily/tasks/<id>/result.md`.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py done <id> [--note <text>|--observed|--force|--add-scope|--stub-drift]
```

## Behavior

- State-changing: flips status to done and writes result metadata.
- Does not run a verification gate; the user's command is the closure signal.
- Before marking done, compares files changed since `claim_sha` against task scope.
- If scope drift exists, default behavior blocks done and asks the user to choose either `--add-scope` or `--stub-drift`.
- `--add-scope` records outside-scope files on the current task before closing it.
- `--stub-drift` creates or reuses a `drift: <summary>` helper task so the drift is tracked without duplicate stubs.
- Parent-owned coordination mode is active when `.wily/coordination.yaml`
  exists. Done uses `claim_snapshot` fingerprints and reports repo-qualified
  changed files; JSON includes `active_mode`.
- In parent-owned coordination mode, `.wily/coordination.yaml` makes `done`
  compare current child repo dirty fingerprints against `claim_snapshot`.
- Changed files are reported with repo-qualified scope such as
  `roadmap:src/app.py`, and status-style JSON views expose `active_mode`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
