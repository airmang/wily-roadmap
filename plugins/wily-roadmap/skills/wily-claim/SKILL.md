---
name: wily-claim
description: Use when the user types $wily-claim or says they are starting a Wily task.
---

# Wily Claim

Claim a ready or blocked task and record actor, claim timestamp, claim SHA or
coordination `claim_snapshot`, and progress file.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py claim <id> [--force]
```

## Behavior

- State-changing: updates `tasks.yaml` and creates `.wily/tasks/<id>/progress.jsonl`.
- Invalid transitions return exit code 3.
- Parent-owned coordination mode is active when `.wily/coordination.yaml` exists.
  In that mode, claim records `claim_snapshot` with child repo branch, sha,
  dirty files, and fingerprints instead of requiring parent Git.
- Repo-qualified scope such as `repo:src/**` is preserved.
- In parent-owned coordination mode, `.wily/coordination.yaml` keeps the task in
  the parent `.wily/tasks.yaml` and records `claim_snapshot` instead of a fake
  parent `claim_sha`.
- The `claim_snapshot` records each registered repo's `branch`, `sha`, dirty
  files, and fingerprints for dirty or untracked files.
- Status-style JSON views expose `active_mode`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
