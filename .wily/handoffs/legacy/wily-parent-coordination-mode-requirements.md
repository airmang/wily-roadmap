# Requirements Handoff: Wily Parent-Owned Coordination Mode

## Source Request

User asked to run `deep-interview` on `agent-handoffs/wily-coordination-project-design-grill.md` and create an execution package.

Source design:
- `agent-handoffs/wily-coordination-project-design-grill.md`

## Desired Outcome

Implement Wily Roadmap support for parent-owned coordination projects, where a non-repo parent directory can own `.wily/tasks.yaml` and `.wily/coordination.yaml`, while child Git repositories are treated as task work targets.

The implementation must preserve existing single-repo Wily behavior and existing manifest-only `wily workspace` behavior.

## In Scope

- Add parent-owned coordination mode using `.wily/coordination.yaml`.
- Add a shared project context resolver for lifecycle/view commands, including active mode, parent root, coordination config, repo registry, actor policy, and observation policy.
- Keep manifest-only workspace mode using `wily-workspace.yaml` / `.wily-workspace.yaml` as read-only aggregate behavior.
- Make `.wily/coordination.yaml` take precedence when both coordination and workspace manifests exist.
- Support repo-qualified task scope entries:
  - `parent:path`
  - `<repo_id>:path`
  - structured `{repo, path}`
  - legacy plain string paths for single-repo compatibility.
- Add normalized scope parsing/matching for coordination mode.
- Use typed scope helpers internally; persist task scope in a backward-compatible YAML form that round-trips strings and structured entries.
- Make `claim`, `done`, `cp`, `status`, `next`, and `watch` operate against parent tasks in coordination mode, including non-Git parent directories.
- Record coordination `claim_snapshot` maps while preserving legacy `claim_sha`; dirty/untracked claim-time files must include per-file fingerprints, not only path names.
- Implement `land` preflight and local multi-commit behavior:
  - classify changes by registered repo,
  - report parent Wily ledger changes separately from parent task artifacts,
  - block ambiguous or out-of-scope changes,
  - block mixed files unless explicitly included,
  - create one local commit per task-scoped touched Git repo,
  - require parent Git only when parent-scoped changes need a commit.
- Update CLI output/JSON/docs/skills to show the active mode clearly.
- Add focused tests for parent non-Git lifecycle, scope parsing, dirty baseline classification, parent-Git land blocking, child-only land, multi-repo land, and manifest-only compatibility.

## Non-Goals

- Do not remove or replace manifest-only workspace mode.
- Do not create parent `.wily/` for manifest-only workspace commands.
- Do not push, open PRs, deploy, or publish remote state.
- Do not auto-run `git init`.
- Do not implement a future `wily publish` command.
- Do not rebuild `wily-board` as part of this package.
- Do not rewrite unrelated Wily v3 commands or docs outside the coordination-mode surface.

## Decision Boundaries

- Goal-scoped local engineering actions may proceed during `/goal`.
- Local commits may be created only by `wily land` behavior under tests/smoke fixtures or during explicit final workflow verification if the execution package calls for it.
- Remote actions remain approval-first under repository instructions; this package must not push or open PRs.
- Hard destructive commands, credential/secret handling, payment/purchase actions, and edits outside the execution package are hard stops.

## Acceptance Criteria

- In a directory with parent `.wily/tasks.yaml` and `.wily/coordination.yaml`, `wily claim <id>` succeeds even when the parent is not a Git repo.
- Coordination `claim` records `claim_snapshot` containing parent and registered child repo entries, including branch, sha when available, dirty state, changed files, and per-file fingerprints for dirty/untracked files.
- Legacy single-repo `claim_sha` remains accepted and serialized for existing tasks.
- `wily done <id>` works in coordination mode and reports changed files using `claim_snapshot` rather than requiring parent Git.
- `wily cp import-status`, `wily status`, `wily next`, and `wily watch` work against parent-owned tasks in coordination mode.
- Active mode is explicit in text and JSON output where user-facing command output summarizes the project.
- Parent-owned `land` blocks clearly when parent-scoped changes exist but the parent is not Git.
- Coordination `land --dry-run` and `land` block before staging when out-of-scope repo changes are present.
- Child-only `land` can commit child repo changes when parent is not Git; parent Wily ledger changes are reported separately and do not require parent Git by themselves.
- Multi-repo `land` creates one local commit per touched task-scoped repo and includes `Wily-Task: <id>`.
- Dirty-at-claim files are classified as `pre_existing_dirty`, new post-claim changes as `task_candidate_changes`, and changed-again baseline files as `mixed_files`.
- Claim snapshots contain enough per-file fingerprint information to distinguish unchanged claim-time dirty files from claim-time dirty files modified again after claim.
- Mixed files block unless an explicit inclusion mechanism is used.
- `--push` is rejected in coordination mode; existing `--push` behavior is preserved only for legacy single-repo mode unless separately deprecated.
- Existing manifest-only `wily workspace status/next/watch/init` tests still pass and still do not create parent `.wily/`.
- Existing single-repo `wily claim/go/done/cp/status/next/watch/land` behavior remains compatible.

## Constraints

- The parent workspace `/Users/wilycastle/Code/projects/wily-plugin` is a coordination workspace, not a monorepo.
- Changes should stay scoped to `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`.
- `wily-board/` should not be treated as an editable repo for this package.
- Coordination v1 commands are run from the parent coordination root or a non-child descendant that resolves to the parent `.wily/`; commands run inside a registered child repo with its own `.wily/` use that child-local Wily project.
- The current worktree is dirty with unrelated Wily Board and task progress changes; preserve them.
- Keep plugin behavior local-first and approval-first for remote actions.
- Runtime handoffs must live under `agent-handoffs/`, not `.codex/` or `.agents/`.

## Repo Facts

- `plugins/wily-roadmap/scripts/wily/coordination.py` does not exist yet.
- `plugins/wily-roadmap/scripts/wily/scope.py` does not exist yet.
- `Task` currently serializes `scope: list[str]` and `claim_sha`; there is no `claim_snapshot` field.
- `claim` currently calls Git helpers at the Wily root and fails in a non-Git parent.
- `done` catches Git failures but only understands single-root `claim_sha` diffs.
- `land` is fully single-repo and commits at the Wily root.
- Manifest-only workspace support is isolated in `wily/workspace.py` and `wily/cli/workspace.py`.
- Existing workspace tests assert that manifest-only commands do not create parent `.wily/`.

## Assumptions

- The initial implementation should include both `--include-mixed` and explicit `--include <repo:path>` for `land`, with preflight defaulting to block mixed files.
- `done` should preserve `claim_sha` for legacy/single-repo tasks; in coordination mode it should prefer `claim_snapshot` and need not synthesize a fake parent `claim_sha`.
- Parent coordination repo outside the current parent path is deferred; v1 treats `parent.path` as `.` in `.wily/coordination.yaml`.
- `wily land --dry-run` should be introduced as the canonical preflight report surface because preflight is a first-class safety requirement.
- Existing plain scope strings remain supported; in coordination mode they should warn or be treated as parent/plain legacy depending on context, but they must not silently match the wrong child repo.
- Parent Wily ledger changes are not the same as parent task artifact changes. Ledger changes under `.wily/tasks.yaml`, `.wily/tasks/<id>/progress.jsonl`, and `.wily/tasks/<id>/result.md` should be reported in coordination land preflight; they do not force parent Git for child-only work. Explicit `parent:` scope entries outside ledger files do force parent Git when touched.
- Commands run inside a registered child repo with its own `.wily/` use the child-local Wily project, not the parent coordination project.

## Decision Log

- Q1: Accepted source design decisions from `wily-coordination-project-design-grill.md` as the interview baseline.
- Q2: Resolved `claim_snapshot` migration by preserving `claim_sha` and adding `claim_snapshot` as an optional field.
- Q3: Resolved mixed-file CLI by planning both `--include-mixed` and explicit `--include <repo:path>`.
- Q4: Deferred external parent coordination repo support.
- Q5: Included `wily land --dry-run` as the preflight report surface.
- Q6: Adopted a shared `resolve_project_context(start)` contract before command rewrites.
- Q7: Required per-file claim fingerprints for mixed-file detection instead of path-only dirty snapshots.
- Q8: Defined parent Wily ledger changes as report-only for child-only land when parent is non-Git.
- Q9: Rejected `--push` in coordination mode while preserving legacy single-repo behavior.
- Q10: Made out-of-scope land blocking and child-repo invocation precedence explicit acceptance criteria.

## Superpowers Routing

- `Superpowers:brainstorming` was consulted because this is behavior/design work. Its approval gates were treated as already satisfied by the provided design grill and the user's explicit request to create an execution package.
- `Superpowers:test-driven-development` should be used during implementation because this changes command behavior.
- `Superpowers:systematic-debugging` should be used for unexpected test/build failures.
- `Superpowers:verification-before-completion` is required before final completion claims.

## Open Questions

- Exact JSON field names for every land preflight classification can be finalized while writing red tests.
- Exact wording of active-mode text output can be tuned against existing command style.

## Likely Touchpoints

- `plugins/wily-roadmap/scripts/wily/coordination.py`
- `plugins/wily-roadmap/scripts/wily/scope.py`
- `plugins/wily-roadmap/scripts/wily/models.py`
- `plugins/wily-roadmap/scripts/wily/config.py`
- `plugins/wily-roadmap/scripts/wily/observation.py`
- `plugins/wily-roadmap/scripts/wily/transitions.py`
- `plugins/wily-roadmap/scripts/wily/cli/claim.py`
- `plugins/wily-roadmap/scripts/wily/cli/done.py`
- `plugins/wily-roadmap/scripts/wily/cli/cp.py`
- `plugins/wily-roadmap/scripts/wily/cli/land.py`
- `plugins/wily-roadmap/scripts/wily/cli/status.py`
- `plugins/wily-roadmap/scripts/wily/cli/next.py`
- `plugins/wily-roadmap/scripts/wily/cli/watch.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_activity.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_layout.py`
- `plugins/wily-roadmap/scripts/wily/ui/watch_render.py`
- `plugins/wily-roadmap/tests/v3/test_v3_core.py`
- `plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- `plugins/wily-roadmap/commands/*.md`
- `plugins/wily-roadmap/skills/wily-*/SKILL.md`
- `plugins/wily-roadmap/README.md`

## Verification Ideas

- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py -k 'coordination or workspace or claim or done or cp or land or status or next or watch'`
- `python3 -m pytest plugins/wily-roadmap/tests/v3/test_v3_core.py plugins/wily-roadmap/tests/v3/test_v3_surface.py`
- Manual fixture smoke for parent-owned non-Git lifecycle.
- Manual fixture smoke for child-only and multi-repo `wily land --dry-run`.
- Manual fixture smoke for out-of-scope land blocking and child-local invocation precedence.
