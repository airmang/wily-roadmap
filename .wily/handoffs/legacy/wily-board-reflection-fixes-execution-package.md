# Execution Package: Wily Board Reflection Fixes

## Native Goal Command

```text
/goal Complete the Wily Board reflection fixes according to agent-handoffs/wily-board-reflection-fixes-execution-package.md.

First read the execution package. Maintain agent-handoffs/wily-board-reflection-fixes-progress.md.

Keep agent-handoffs/wily-board-reflection-fixes-status.md updated as the live Codex status board. Update it whenever checkpoint status, verification status, blockers, or current/next action changes.

Do not treat this as a general backlog. Work only toward this single objective and its acceptance criteria.

Because this /goal is active, continue without asking for approval on goal-scoped engineering actions.

Superpowers Autonomy Override is active: convert any Superpowers approval/review/continue prompt into a recorded progress checkpoint and keep working unless a narrow hard-stop condition is reached.

Work checkpoint-by-checkpoint. After each checkpoint:
1. summarize what changed,
2. run the relevant verification command(s),
3. append progress, evidence, and remaining work to the progress log,
4. continue unless a narrow hard-stop condition is triggered.

Do not broaden scope beyond the execution package. Stop only for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, edits outside the execution package, explicit user-forbidden actions, or if the same verification failure repeats twice without new evidence.

Done only when all acceptance criteria are satisfied and final verification passes:
- python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_daemon_reloads_registry_each_tick plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent
- cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_agent_routes.py -q
- python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent status --json
- python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json
- rg -n "/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py|live-worked --from-hook" /Users/wilycastle/.codex/hooks.json /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap /Users/wilycastle/Code/projects/wily-plugin/wily-board
```

## Source Request / Handoff

User asked, in Korean, to first plan fixes for the problems found while reviewing whether Wily work state is reflected correctly on Wily Board.

Prior review found:

- `~/.codex/hooks.json` still calls the old moved-away path `/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`.
- `wily.agent.client.publish_snapshot()` and `publish_heartbeat()` overwrite failed `post_json()` results with `sent: true`.
- Wily v3 docs and CLI disagree about legacy `live-worked --from-hook`: docs imply it reflects work, CLI treats it as no-op for migration safety and removed otherwise.
- `wily-board/.venv` has old relocation shebangs pointing at `/Users/wilycastle/Code/projects/wily-board`, so local board tests are not runnable through that venv.

## Inline Requirements

Outcome:
- Make current Wily Board reflection honest and operable: durable task snapshots and heartbeats should report true send status, local Codex hook errors should stop, and docs should say exactly what v3 supports.

In scope:
- Wily Roadmap plugin agent client behavior and tests.
- Wily Roadmap plugin/README/docs wording around Board v3, legacy live hooks, and custom-workflow checkpoint sync.
- Local Codex hook configuration cleanup for the user's machine.
- Wily Board local test environment repair when needed to verify board route tests.

Non-goals:
- Do not reintroduce legacy v2 `live-worked`, `live-heartbeat`, `checkpoint-sync`, or signed `/api/live/events` as primary Wily v3 behavior.
- Do not redesign Wily Board UI.
- Do not change Board auth/token semantics except where tests require truthful reporting.
- Do not remove user-created Wily roadmap handoffs or unrelated dirty files.

Assumptions:
- Wily v3 Board reflection contract is agent-driven: `wily-agent` watches `.wily/`, sends `/agent/snapshot` and `/agent/heartbeat`, and Board projects snapshot tasks into stage/phase rows.
- Custom Workflow checkpoint progress remains a manual or explicit bridge through `wily cp start|done|import-status`.
- Legacy `live-* --from-hook` should remain non-blocking during migration, but should not be documented as a working reflection path.

## Acceptance Criteria

- No current Codex tool execution attempts to run the old `/Users/wilycastle/Code/projects/wily-roadmap/.../wily.py` path.
- `publish_snapshot()` and `publish_heartbeat()` return `sent: false` when `post_json()` fails; success cases still return `sent: true`.
- Tests cover failed snapshot and heartbeat result reporting.
- Docs clearly state Wily v3 uses `wily-agent` snapshots/heartbeats for Board reflection and that stale `live-* --from-hook` hooks are migration no-ops to remove.
- `wily agent status --json` shows the moved plugin path/registry setup without old-path failures.
- Board route tests are runnable after repairing the relocated environment, or the final report records a concrete unrepaired local environment blocker.

## File / Ownership Boundaries

- Expected touchpoints:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily/agent/client.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/v3/test_v3_core.py`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/README.md`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
  - `/Users/wilycastle/.codex/hooks.json`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board/.venv` or a regenerated replacement venv, if needed only for verification
  - `agent-handoffs/wily-board-reflection-fixes-*.md`
- Must not edit:
  - Unrelated Wily roadmap historical handoffs except this new plan/status/progress/verification set.
  - Secrets, bearer tokens, Board production env files, or private keys.
  - `.wily/archive/` historical records.
- User-owned or pre-existing changes to preserve:
  - Existing modified roadmap handoffs and docs shown by `git status`.
  - Existing modified `wily-board/tests/test_agent_routes.py`.
  - Existing untracked `.claude/` and relocation handoff files.

## Execution Plan

Parallelization verdict:
- Verdict: SEQUENTIAL_RECOMMENDED
- Limited parallelization is safe for read-only investigation and final review only.
- Implementation should run mostly serially because Checkpoint 2 changes tests/source behavior, Checkpoint 3 changes the local Codex hook that affects all subsequent tool output, and Checkpoint 4 depends on the chosen v3 contract.
- Safe side lanes during execution:
  - Docs reviewer can inspect wording after Checkpoint 4.
  - Verification reviewer can rerun command evidence after Checkpoint 6.
- Unsafe to parallelize:
  - Editing `client.py` and tests in the same file set.
  - Editing `/Users/wilycastle/.codex/hooks.json` while another lane is running tool-heavy verification.

Reviewer gates:
- completion_verifier: run after Checkpoint 6 to confirm all acceptance criteria and verification evidence are satisfied.
- integration_reviewer: run before final if both roadmap plugin and board docs/test environment changes are present.
- After Checkpoint 2, review that failed send results preserve `sent: false` and success results still report `sent: true`.
- After Checkpoint 3, review that the hook removal does not leave invalid JSON and does not re-point `live-worked` to the moved path.
- After Checkpoint 4, review docs for one clear v3 contract: Board reflection is `wily-agent` snapshot/heartbeat; legacy `live-* --from-hook` is a stale-hook no-op only.
- Before final, run the planned verification commands and inspect changed files with `git diff --check`.

Rollback/recovery note:
- Source changes can be reverted with a focused reverse patch to the files listed in this package.
- `/Users/wilycastle/.codex/hooks.json` must be backed up before editing; restore from `/Users/wilycastle/.codex/hooks.json.bak-wily-board-reflection-20260519` if Codex hook behavior needs to return to the previous state.
- If `uv sync` recreates `wily-board/.venv` and causes environment issues, remove the generated venv and rerun `uv sync` from `wily-board`; do not commit `.venv`.
- If Board production sends fail with auth/network errors after code fixes, record that as an environment/auth limitation unless local route tests fail.

## Rollback / Stop Conditions

- Roll back source edits with focused reverse patches if tests show a regression outside this objective.
- Restore `/Users/wilycastle/.codex/hooks.json` from `/Users/wilycastle/.codex/hooks.json.bak-wily-board-reflection-20260519` if removing the stale hook breaks expected local Codex behavior.
- Stop if a required fix would expose secrets, require a new Board registration code, or overwrite unrelated user changes.
- Stop if the same final verification command fails twice with no new evidence.

### Checkpoint 1: Baseline And Safety

Files:
- Read only: hook config, launchd plist, registry, target source/test files.
- Update: `agent-handoffs/wily-board-reflection-fixes-status.md`
- Update: `agent-handoffs/wily-board-reflection-fixes-progress.md`

Steps:

1. Record current status:
   - `git -C /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap status --short --branch`
   - `git -C /Users/wilycastle/Code/projects/wily-plugin/wily-board status --short --branch`
   - `sed -n '1,120p' /Users/wilycastle/.codex/hooks.json`
   - `plutil -p /Users/wilycastle/Library/LaunchAgents/com.wily.roadmap.agent.plist`
   - `sed -n '1,160p' /Users/wilycastle/.config/wily/agent/registry.json`
2. Confirm old path is only in stale local hook/config/history locations that are safe to update or document.
3. Update status/progress with exact baseline and note pre-existing dirty files.

Verification:
- Commands above complete and old-path source is identified.

### Checkpoint 2: Truthful Agent Send Results

Files:
- Modify: `plugins/wily-roadmap/scripts/wily/agent/client.py`
- Modify: `plugins/wily-roadmap/tests/v3/test_v3_core.py`

Test-first steps:

1. Add tests that monkeypatch `wily.agent.client.post_json` to return `{"sent": False, "reason": "boom"}` for both snapshot and heartbeat.
2. Verify the new tests fail because current code overwrites `sent` to `true`.
3. Change `publish_snapshot()` and `publish_heartbeat()` to preserve failed `sent: false` while adding `sent: true` only when `post_json()` does not already return `sent: false`.
4. Preserve existing success shape, including response status/body fields.

Suggested implementation shape:

```python
def _with_sent_success(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("sent") is False:
        return result
    return {"sent": True, **result}
```

Verification:
- `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_client_reports_failed_snapshot_and_heartbeat_as_not_sent`
- `python3 -m unittest plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_builds_board_v3_snapshot_payload_from_local_wily_state plugins.wily-roadmap.tests.v3.test_v3_core.CoreModelTest.test_agent_daemon_reloads_registry_each_tick`

### Checkpoint 3: Remove Stale Codex Hook Failure

Files:
- Modify: `/Users/wilycastle/.codex/hooks.json`
- Optionally modify docs to point to `wily-agent` instead of `live-worked` hook.

Steps:

1. Back up hook config:
   - `cp /Users/wilycastle/.codex/hooks.json /Users/wilycastle/.codex/hooks.json.bak-wily-board-reflection-20260519`
2. Remove the `PostToolUse` entry that invokes:
   - `/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py live-worked --from-hook --agent codex`
3. Do not replace it with a new `live-worked` path, because v3 `live-* --from-hook` is a no-op and docs say stale hooks should be removed.
4. Run a harmless command and confirm the old-path error no longer appears.

Verification:
- `python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py live-worked --from-hook --agent codex` exits 0.
- A shell command such as `true` or `pwd` no longer prints `can't open file '/Users/wilycastle/Code/projects/wily-roadmap/.../wily.py'`.
- `rg -n "/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py" /Users/wilycastle/.codex/hooks.json` returns no matches.

### Checkpoint 4: Align Documentation And CLI Contract

Files:
- Modify: `wily-board/docs/OPERATIONS.md`
- Modify: `wily-roadmap/README.md`
- Modify: `wily-roadmap/plugins/wily-roadmap/README.md`
- Optional test docs scan in `plugins/wily-roadmap/tests/v3/test_v3_surface.py` if existing style supports it.

Steps:

1. In Board operations docs, replace “Claude and Codex hooks call `wily live-worked --from-hook`” with v3 contract language:
   - `wily-agent` sends durable snapshots and heartbeat.
   - `live-* --from-hook` exists only as a migration no-op so stale hooks do not break tool calls.
   - Remove stale hooks from `~/.codex/hooks.json`.
   - Checkpoint progress requires explicit `wily cp ...` calls or `wily cp import-status`.
2. In Wily roadmap README, keep cleanup section but make it operational:
   - explain current symptom and exact stale hook pattern.
   - state not to re-point it to the moved path.
3. In plugin README, clarify Board v3 path:
   - `wily agent login/register/install/start/status`.
   - `wily cp` is the custom-workflow checkpoint bridge.
   - `live-*` is not a v3 reflection mechanism.
4. If tests exist for surface docs, add assertions for the new wording and absence of misleading `live-worked` hook guidance.

Verification:
- `rg -n "hooks call `wily live-worked|Codex hooks call `wily live-worked|codex-bridge" wily-board/docs/OPERATIONS.md wily-roadmap/README.md wily-roadmap/plugins/wily-roadmap/README.md`
- Expected: no misleading hook-as-reflection statement; any `live-worked` mentions explicitly say stale/no-op/remove.

### Checkpoint 5: Repair Board Test Execution Environment

Files:
- Prefer environment repair only, not source changes.
- Possible generated changes: `.venv/` under `wily-board`, not committed unless already intended.

Steps:

1. Try the normal route:
   - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_agent_routes.py -q`
2. If `uv` cache works now, no venv repair is needed.
3. If `.venv` shebang is still needed and points to old path, recreate local venv:
   - `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv sync`
4. Do not edit source tests just to work around a broken environment.
5. Record whether `wily-board/tests/test_agent_routes.py` has pre-existing user changes before running/fixing tests.

Verification:
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_agent_routes.py -q`

### Checkpoint 6: Integration Smoke

Files:
- No new source changes unless smoke reveals a defect in goal scope.
- Update progress/status/verification docs.

Steps:

1. Confirm installed agent paths:
   - `python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent status --json`
2. Run one foreground tick:
   - `python3 /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py agent run --once --offline-ok --json`
3. Inspect JSON:
   - registered moved repos are present.
   - failed network/auth sends, if any, report `sent: false`.
   - successful sends report `sent: true`.
4. Run old-path scan over active configs and source/docs:
   - `rg -n "/Users/wilycastle/Code/projects/wily-roadmap/plugins/wily-roadmap/scripts/wily.py|live-worked --from-hook" /Users/wilycastle/.codex/hooks.json /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap /Users/wilycastle/Code/projects/wily-plugin/wily-board`
5. Treat historical handoffs as informational unless they are active docs being edited in this goal.

Verification:
- Commands above complete.
- Any remaining matches are either removed or explicitly classified historical.

## Autonomous Action Policy

- Goal-scoped local engineering actions may proceed without user approval.
- Editing `/Users/wilycastle/.codex/hooks.json` is goal-scoped because the broken hook currently disrupts every tool execution.
- Network calls to configured Wily Board through `wily agent run --once` are goal-scoped smoke verification.
- Stop for hard destructive shell commands, payment/purchase actions, credential or secret exfiltration, explicit user-forbidden actions, or repeated verification failure without new evidence.

## Live Status Board

- File: `agent-handoffs/wily-board-reflection-fixes-status.md`
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
  - `Superpowers:test-driven-development` for Checkpoint 2 behavior change.
  - `Superpowers:systematic-debugging` for any failing verification, hook symptom recurrence, or unexpected send result.
- Required before done:
  - `Superpowers:verification-before-completion`.
- Conditional:
  - `Superpowers:writing-plans` has been used to shape this execution package.
  - `Superpowers:dispatching-parallel-agents` / `Superpowers:subagent-driven-development` may be used only for independent investigation/review lanes.
  - `Superpowers:requesting-code-review` is useful before final if source changes exceed the planned touchpoints.

## Superpowers Autonomy Override

- Active when native `/goal` is active or the user requested autonomous execution.
- Superpowers approval/review/continue prompts are not user gates during active `/goal`.
- Convert them into progress/evidence checkpoints and continue.
- Record each conversion as:
  `Auto-resolved under active /goal: <gate> -> <decision and evidence>.`
- User input is required only for narrow hard-stop conditions.

## Goal Runtime Contract

Progress log:
- `agent-handoffs/wily-board-reflection-fixes-progress.md`

Live status board:
- `agent-handoffs/wily-board-reflection-fixes-status.md`

Verification evidence:
- `agent-handoffs/wily-board-reflection-fixes-verification.md`

Baseline:
- Current git status:
  - Roadmap repo has many pre-existing modified handoffs/docs and untracked relocation handoffs.
  - Board repo has pre-existing modified `tests/test_agent_routes.py`.
- Initial verification:
  - Roadmap focused agent tests previously passed.
  - Board pytest was blocked by relocated `.venv` shebang and, earlier, `uv` cache permissions.
- Known broken tests unrelated to this task:
  - None proven; board route tests are currently environment-blocked until venv/uv is repaired.

User / pre-existing changes:
- Pre-existing modified files:
  - Roadmap repo has numerous modified historical handoff and docs files from earlier work; inspect before touching any of them.
  - Board repo has modified `tests/test_agent_routes.py`; preserve user changes and avoid editing unless required by this goal.
- Preserve all existing dirty files unless they are explicitly touched for this goal.
- If a target file has unrelated user edits, inspect first and edit around them.

Checkpoint loop:
1. Choose the next smallest checkpoint from this execution package.
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
7. Continue until DONE, PARTIAL, or BLOCKED unless a narrow hard-stop condition is triggered.

Narrow hard-stop conditions:
- A command would delete or overwrite user data outside the stated files.
- A command would expose or print secrets/tokens/private keys.
- Board production auth requires new credentials or one-time login code not available locally.
- The same verification fails twice with no new evidence.
- Editing a target file would overwrite unrelated user changes that cannot be safely separated.

## Final Report Requirements

Final response must be in Korean and include:
- Whether Board reflection is now fixed or partially fixed.
- What changed in source/docs/local config.
- Exact verification commands and outcomes.
- Any remaining limitations, especially production network/auth state if not verifiable.
