# Execution Package: Wily Plugin Relocation

## Native Goal Command

```text
/goal Complete moving /Users/wilycastle/Code/projects/wily-roadmap and /Users/wilycastle/Code/projects/wily-board under /Users/wilycastle/Code/projects/wily-plugin according to agent-handoffs/wily-plugin-relocation-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-plugin-relocation-progress.md.

Keep agent-handoffs/wily-plugin-relocation-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this `/goal` is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the relocation scope, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes: git status checks for both moved repos and nested worktrees; marketplace metadata check; stale executable/config path audit; launchd plist check; Wily registry check; wily agent status; wily agent run --once --offline-ok --json; targeted board tests for local_path handling; plugin Python tests or a narrowed smoke test if full tests are not available.
```

## Source Request / Handoff

User requested, in Korean, to move the two repositories into:

```text
/Users/wilycastle/Code/projects/wily-plugin/
  wily-roadmap/
  wily-board/
```

Constraints from the request:
- Do not merely move the folders; plan thoroughly to avoid breakage.
- Preserve the internal `wily-roadmap` marketplace repo structure because `.agents/plugins/marketplace.json` uses relative path `./plugins/wily-roadmap`.
- Existing absolute paths in launchd plist, agent registry, handoff docs, and local scripts must be updated after the move.
- Current daemon plist points directly at `/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`; after moving, run `wily agent install` and `wily agent start` again.
- Agent registry stores repo paths as absolute paths; re-register or update JSON after moving.

## Inline Requirements

Outcome:
- Move both repositories under `/Users/wilycastle/Code/projects/wily-plugin/`.
- Preserve the complete internal layout of each repository.
- Repair local service/configuration references so the Wily agent daemon and registry use the new path.
- Update current handoff/docs/tests/local references from old absolute paths to new absolute paths where those references are operational or current project guidance.
- Leave no old absolute paths in launchd plist, Wily agent registry, or git worktree metadata.

In scope:
- Filesystem relocation of the two repository directories.
- `wily-roadmap` git worktree metadata repair for `.claude/worktrees/*`.
- `wily-roadmap` `core.hooksPath` repair.
- Wily agent launchd stop/install/start/status.
- Wily agent registry unregister/register for moved roadmap root and its registered nested worktrees.
- Path replacement in non-vendor text files, excluding `.git`, virtualenvs, and dependency folders.
- Targeted tests and audits proving the relocated paths are active.

Non-goals:
- Changing the marketplace relative path `./plugins/wily-roadmap`.
- Adding hooks, MCP servers, or app integrations.
- Remote pushes, PRs, package publishing, or production Board changes.
- Exposing or printing secrets from Wily agent config.

Assumptions:
- `/Users/wilycastle/Code/projects/wily-plugin` does not exist and can be created.
- `wily-board` is a clean git repo on `main`.
- Existing untracked `wily-roadmap/.claude/` is user/pre-existing state and must be preserved.
- Historical archives may still mention old paths if they are intentionally archival, but operational config, registry, launchd, tests, current handoffs/docs, and git metadata must not rely on old paths.

## Acceptance Criteria

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` exists and is the moved roadmap git repo.
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board` exists and is the moved board git repo.
- Original root directories `/Users/wilycastle/Code/projects/wily-roadmap` and `/Users/wilycastle/Code/projects/wily-board` no longer exist as active repo roots.
- `wily-roadmap/.agents/plugins/marketplace.json` is still present and still points to `./plugins/wily-roadmap`.
- `~/Library/LaunchAgents/com.wily.roadmap.agent.plist` points at the moved `.../wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py` path.
- `~/.config/wily/agent/registry.json` contains moved Wily repo/worktree paths and does not contain the old `wily-roadmap` path.
- `git -C <new roadmap> worktree list --porcelain` works and lists moved worktree paths.
- `git status` works for moved roadmap, moved board, and the two nested roadmap worktrees.
- Current executable/config/test references to old repo roots are updated or explicitly documented as archival.
- `wily agent status` reports installed/configured and daemon running after reinstall/start.
- `wily agent run --once --offline-ok --json` succeeds without printing secrets.
- Targeted board test for local path projection passes after expected path update.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/**`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/**`
  - `/Users/wilycastle/.config/wily/agent/registry.json`
  - `/Users/wilycastle/Library/LaunchAgents/com.wily.roadmap.agent.plist`
  - `/Users/wilycastle/Library/Logs/wily-agent/**` only for daemon output, not manual edits
- Must not edit:
  - Remote repositories or GitHub state.
  - Wily agent config secret/token values.
  - Dependency/vendor folders except path audit exclusion.
  - Marketplace relative path away from `./plugins/wily-roadmap`.
- User-owned or pre-existing changes to preserve:
  - `wily-roadmap/.claude/` is pre-existing untracked state and contains two git worktrees.
  - `wily-board` contains a private key file; do not print its contents.

## Execution Plan

1. Freeze baseline.
   - Record git status for both repos.
   - Record Wily agent status without printing config JSON.
   - Confirm target path is absent.
   - Record launchd plist path and current old script path.
2. Stop the daemon while the old plugin path still exists.
   - Run `python3 /Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent stop`.
   - Verify daemon is no longer running or record an already-stopped result.
3. Move the repos.
   - Create `/Users/wilycastle/Code/projects/wily-plugin`.
   - Move `wily-roadmap` and `wily-board` into it.
   - Switch all subsequent commands to the new paths.
4. Repair git-local absolute metadata.
   - Set `core.hooksPath` to `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/.git/hooks`.
   - Run `git worktree repair` for the two nested `.claude/worktrees` paths.
   - Verify and, only if repair misses exact files, patch `.claude/worktrees/*/.git` and `.git/worktrees/*/gitdir`.
5. Update operational path references.
   - Replace old repo roots with new roots in non-vendor text files in both repos.
   - Exclude `.git`, `node_modules`, `.venv`, caches, and binary/private key files.
   - Keep marketplace path relative.
6. Update Wily agent registry.
   - Unregister old roadmap root and old registered roadmap worktree paths using `wily agent unregister --path`.
   - Register new roadmap root and new registered roadmap worktree paths using `wily agent register --path ... --repo R-W-LAB/wily-roadmap`.
   - Register moved board only if it was already registered or if a Wily `.wily` registry entry is required for this relocation; do not invent a remote repo mapping if not present in baseline.
7. Reinstall and start launchd.
   - Run `wily agent install` from the moved plugin path.
   - Run `wily agent start`.
   - Verify plist program arguments point to the moved path.
8. Final verification and cleanup.
   - Run git status checks for moved repos/worktrees.
   - Run stale path audits on launchd plist, registry, git metadata, and active repo text files.
   - Run Wily agent status and offline one-shot daemon run.
   - Run targeted board test for local path handling.
   - Run plugin smoke tests or a focused Python test subset.
   - Update progress, verification, and status files.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- This includes moving directories, stopping/starting the local Wily launchd daemon, rewriting Wily registry entries through the Wily CLI, and running local tests.
- No remote pushes, PRs, purchases, credential exfiltration, or destructive deletes are in scope.
- Record externally visible or user-level local actions in the progress log.
- Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure.

## Live Status Board

- File: `agent-handoffs/wily-plugin-relocation-status.md`
- Intended use: keep this Markdown file open in Codex while `/goal` runs.
- Update cadence:
  - after creating the execution package
  - before starting a checkpoint
  - after completing a checkpoint
  - after each verification command
  - when a blocker, subagent lane, Superpowers auto-resolution, or final state changes
- Required visible fields:
  - State: PLANNING | RUNNING | VERIFYING | DONE | PARTIAL | BLOCKED
  - Objective
  - Progress count and percentage
  - Current checkpoint/action
  - Next checkpoint
  - Checkpoint table
  - Verification table
  - Recent events

## Superpowers Skill Routing

- Available: yes.
- Required before implementation:
  - `Superpowers:test-driven-development` for behavior changes, or reason skipped: relocation is mostly filesystem/config migration; targeted tests will be updated after move, but no application behavior change is intended.
  - `Superpowers:systematic-debugging` for failures, or reason not applicable: use only if launchd, git metadata, or tests fail unexpectedly.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans` for detailed task decomposition: used to shape this package.
  - `Superpowers:using-git-worktrees` if isolation is needed: skipped because the task is relocating the active worktrees themselves.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` if lanes are independent: used for read-only exploration, daemon registry review, parallelization review, architecture review, and plan critique.
  - `Superpowers:requesting-code-review` / `Superpowers:finishing-a-development-branch` for review, PR, merge, or cleanup: PR/merge not in scope.

## Superpowers Autonomy Override

- Active when native `/goal` is active or the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-plugin-relocation-progress.md`

Live status board:
- `agent-handoffs/wily-plugin-relocation-status.md`

Verification evidence:
- `agent-handoffs/wily-plugin-relocation-verification.md`

Baseline:
- Current git status:
  - `wily-roadmap`: `## main...origin/main`, `?? .claude/`
  - `wily-board`: `## main...origin/main`, clean
- Initial Wily agent state:
  - installed: true
  - configured: true
  - daemon running: true
  - registry: `/Users/wilycastle/.config/wily/agent/registry.json`
- Known broken tests unrelated to this task: unknown at planning time.

User / pre-existing changes:
- Pre-existing modified files: none reported by `git status --short` in either repo.
- Pre-existing untracked files: `wily-roadmap/.claude/`.
- Must not overwrite user changes:
  - Preserve `.claude/worktrees` contents and repair metadata in place.
  - Preserve Wily agent config secret/token values.
  - Preserve board private key file without reading or printing it.

Checkpoint loop:
1. Choose the next smallest checkpoint from the execution package.
2. Update the status board: mark the checkpoint RUNNING, set Current action, and refresh Last updated.
3. Make one focused change set.
4. Run targeted verification for that checkpoint.
5. Update the status board: mark verification state and checkpoint state.
6. Append progress log:
   - checkpoint name
   - files changed
   - commands run
   - result
   - evidence file updates, if any
   - status board update
   - next step
   - blockers / risks
7. Continue until `DONE`, `PARTIAL`, or `BLOCKED` unless a narrow hard-stop condition is triggered.

Checkpoint cadence:
- At the end of each execution package step.
- Before changing git metadata or launchd state.
- After any failed verification retry.
- Before final done claim.

Narrow hard-stop conditions:
- A command would delete data rather than relocate or rewrite known config.
- A command would expose secrets or private key material.
- A target path conflict appears under `/Users/wilycastle/Code/projects/wily-plugin`.
- `git worktree repair` and exact metadata patching both fail to restore worktree status.
- Wily agent cannot be restarted after two distinct evidence-producing attempts.

## Rollback / Stop Conditions

- If move fails before both repos are under the new parent, stop and report exact filesystem state.
- If launchd cannot stop from the old path, inspect status and stop condition before moving.
- If the target path unexpectedly exists, stop before any move.
- If registry commands risk removing unrelated repos, use exact old path unregister only.

## Parallelization Verdict

Verdict: SEQUENTIAL_REQUIRED

Reason:
- Actual filesystem move, git worktree repair, Wily registry mutation, and launchd reinstall/start must be ordered.
- Read-only planning/audit/review was safely delegated to subagents before implementation.
- Post-move audits can be performed by subagents, but main agent owns all writes and final synthesis.

Reviewer gates:
- plan_architect: review relocation safety before implementation.
- plan_critic: review concrete command executability before implementation.
- integration_reviewer: review final integration state after implementation.
- completion_verifier: independently inspect final evidence before done.
