---
name: wily-land
description: Use when the user types $wily-land after a task is done and asks to commit or push it.
---

# Wily Land

Collect scoped changed files, create a git commit with `Wily-Task: <id>`, and optionally push after explicit approval.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py land <id> [--dry-run|--no-push|--force|--include-ledger-closure|--include-mixed|--include <repo:path>]
```

## Behavior

- State-changing: creates a git commit.
- Without `--include-ledger-closure`, stop if out-of-scope Wily ledger files are present.
- Use `--include-ledger-closure` to include `.wily/tasks.yaml`, `.wily/tasks/<id>/result.md`, or task `progress.jsonl` closure files with the landing commit.
- Remote actions remain approval-first; do not push without explicit user approval.
- In parent-owned coordination mode, `.wily/coordination.yaml` enables
  local-only multi-repo land. `wily land --dry-run <id>` reports preflight
  before staging.
- Coordination preflight reports parent ledger changes separately, blocks parent
  task artifacts when the parent is not Git, blocks out-of-scope child changes,
  and classifies `pre_existing_dirty`, `task_candidate_changes`, and
  `mixed_files` from `claim_snapshot` fingerprints.
- Mixed files block by default. Use `--include-mixed` or
  `--include <repo:path>` only when that mixed file belongs to this task.
- In coordination mode, `--force` only bypasses the done-status gate; it does
  not include out-of-scope or mixed files.
- `--push is rejected` in coordination mode. Coordination land is local-only and
  creates one local commit per touched registered child repo with
  `Wily-Task: <id>`.
- Status-style JSON views expose `active_mode`.
- Parent-owned coordination mode is active when `.wily/coordination.yaml`
  exists. Start with `wily land --dry-run <id>`.
- Coordination land uses `claim_snapshot`, repo-qualified scope, and
  `active_mode` to preflight registered repos.
- Mixed files block unless `--include-mixed` or `--include <repo:path>` is
  explicit.
- Coordination land is local-only: it creates one child repo commit per touched
  scoped repo after preflight and `--push is rejected`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
