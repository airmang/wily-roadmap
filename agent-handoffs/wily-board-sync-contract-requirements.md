# Requirements Handoff: Wily Board Sync Contract For Wily Skills

## Source Request

The user asked whether Wily Roadmap plugin skills should be revised so their behavior includes the procedure for reflecting Wily state changes on Wily Board.

Context from the preceding production fix:

- Local Wily state had advanced to Stage `s25`, but production Wily Board still showed only through `s24`.
- The root cause was not just missing code; the Wily skill/operation contract did not consistently require Board reflection and actual-site verification after Wily state changes.
- The user wants this contract made explicit across Wily plugin skills and operations.

## Desired Outcome

Make Wily Roadmap skills and related docs define a standard contract:

1. Wily state-changing actions update local `.wily` state first.
2. The related Wily Board live/provisional projection is emitted or replayed when Board live config is available.
3. Board reflection is verified with deterministic evidence such as emit result, API, SSR HTML, or SSE.
4. The actual production Board site is visually verified in a browser when automatic verification fails, reports a mismatch, the user explicitly asks for visual confirmation, or the implementation changes Board UI/rendering behavior.
5. If Board reflection fails, durable `.wily` state is preserved and the user gets a clear warning plus recovery steps.

## In Scope

- Update Wily plugin skill documentation so Board reflection is part of the normal procedure for all state-changing Wily commands.
- Update command docs and runner adapter contract so Custom Workflow checkpoint/status boards are reflected on Board.
- Update Board operations documentation so the live reflection and actual-site verification procedure is explicit.
- Add or adjust CLI-level behavior/tests where needed so Board emit results and resync hints are structurally recorded and easy for skills to surface.
- Require browser visual verification of `https://rnwlab.duckdns.org` for Board reflection failures, suspected mismatches, explicit user requests, and Board UI/rendering behavior changes.
- Add Wily authoring guidance that new or revised Stage and Phase natural-language content must be written in Korean.

State-changing Wily commands include at least:

- `$wily-init`
- `$wily-start`
- `$wily-run`
- `$wily-decompose-stage`
- `$wily-complete`
- `$wily-block`
- `$wily-retry`
- `$wily-replan`
- `$wily-issues --add-to-roadmap` when approved
- any future Wily command that mutates `.wily` roadmap, Stage, Phase, session, revision, or live projection state.

## Non-Goals

- Do not make Wily Board the durable source of truth. `.wily` Git-backed state remains authoritative.
- Do not add hooks, MCP servers, app integrations, or new remote integrations as part of this contract.
- Do not make Board outages roll back local Wily state.
- Do not require every read-only command such as `$wily-status`, `$wily-next`, or `$wily-watch` to emit Board updates.
- Do not require production deploy work unless implementation changes actually need deployment.

## Decision Boundaries

- Board reflection failure must not undo or block the underlying Wily state change.
- When Board reflection fails, the command/skill should surface:
  - what Wily state changed;
  - which Board event/projection failed;
  - the recovery command, such as `wily board check --probe` or `wily board sync-local <stage-id>`;
  - whether actual-site verification remains incomplete.
- Browser visual verification is not mandatory for every successful state-changing Wily command.
- Browser visual verification is mandatory when:
  - Board emit/API/SSE/HTML verification fails;
  - Board evidence reports a mismatch with `.wily` state;
  - the user explicitly asks to check the real site visually;
  - the implementation changes Board UI/rendering behavior rather than only Wily skill/CLI procedure.
- Authentication policy for browser verification:
  - First use the user's Chrome logged-in session.
  - If Chrome/browser automation is unavailable, stop and request explicit user approval before creating a short-lived server-side verification session.
  - Any temporary verification session must be deleted after use.
- User-facing responses should be situation-aware:
  - routine success can be concise;
  - important transitions such as `$wily-run`, `$wily-complete`, `$wily-block`, and `$wily-replan` should include compact Board verification evidence;
  - failures should include detailed recovery steps.

## Acceptance Criteria

- `wily-workflow` describes the Board reflection contract for state-changing Wily commands.
- Precise command skills for state-changing commands mention the required Board reflection and actual-site verification behavior.
- `wily-run` and runner adapter docs require Custom Workflow status/checkpoint state to be synchronized to Board through `checkpoint-sync` or the equivalent helper path.
- `wily-decompose-stage` explicitly requires local topology draft replay/verification after Stage decomposition.
- `wily-complete`, `wily-block`, and `wily-replan` describe Board-visible status update expectations and failure handling.
- Command docs under `plugins/wily-roadmap/commands/` stay aligned with matching skills.
- Board operations docs describe the end-to-end procedure:
  - check live config;
  - emit or replay;
  - verify API/SSE/SSR HTML as normal evidence;
  - visually verify the actual site only when deterministic verification fails, reports a mismatch, UI/rendering changed, or the user explicitly asks;
  - clean up any temporary verification auth.
- Stage and Phase authoring guidance requires Korean for human-readable content such as titles, purpose/scope, task descriptions, prompts, verification notes, handoffs, and notes.
- CLI tests or deterministic checks cover at least one structural emit-result/resync-hint path so future regressions are visible.
- No secret values are committed or printed.
- No new hooks, MCP servers, or app integrations are added.

## Constraints

- Preserve local-first and approval-first behavior.
- Preserve all existing dirty `.wily` roadmap state and untracked Stage `s25` files.
- Do not revert existing Wily Board or Wily Roadmap changes.
- Keep skill bodies concise; put detailed policy in `skills/wily-workflow/references/` when practical.
- Keep machine-facing IDs, status values, field names, file paths, and commands in English.
- Write new or revised Stage and Phase human-readable content in Korean, including `stage.md`, `phase.md`, `prompt.md`, `verification.md`, `handoff.md`, `notes.md`, and title/task text where those fields are user-facing.
- User-facing prose should be Korean when the user is speaking Korean.

## Repo Facts

- Wily Board live config is read from user config, repo-local `.wily/board.json`, repo-local `.wily/local/board.json`, and `WILY_BOARD_*` environment variables.
- `wily.py` already has live event helpers:
  - `emit_board_live_event`
  - `_record_board_emit_result`
  - `read_board_last_emit`
  - `command_board_sync_local`
  - `command_checkpoint_sync`
  - `command_live_heartbeat`
  - `command_live_worked`
- `wily.py start` emits Board `start` events when live config is present.
- `wily.py complete` and `wily.py block` close live sessions with Board-visible statuses.
- `wily.py decompose-stage` and `wily.py board sync-local` can emit `stage_decomposed_local` draft topology events.
- `wily-workflow/references/runner-adapter-contract.md` already documents checkpoint sync, but the high-level skill contract does not yet make actual Board/site verification mandatory after state-changing Wily operations.
- Production Board visual verification previously required special handling because browser automation may not have the user's authenticated Chrome session.

## Assumptions

- Board reflection is a live/provisional projection, not durable roadmap truth.
- The actual site URL for verification is `https://rnwlab.duckdns.org` unless config says otherwise.
- API/HTML/SSE checks are the normal verification path for successful Board-visible Wily state changes.
- Browser visual verification is the escalation path for failures, mismatches, explicit user requests, and UI/rendering changes.
- Temporary verification sessions are acceptable only after explicit user approval and must be cleaned up.

## Decision Log

- Q1: selected C = full operations contract across skills, command docs, runner adapter contract, and Board operations docs.
- Q2: corrected after follow-up = actual-site browser visual verification is required for failures, mismatches, explicit user requests, and UI/rendering changes, not for every routine successful Wily state change.
- Q3: selected A = all state-changing Wily commands must include Board reflection/verification procedure.
- Q4: selected A = Board failure preserves Wily state and surfaces warning/recovery, rather than rolling back or failing the Wily state change.
- Q5: selected C = use user Chrome session first; if unavailable, ask explicit approval before temporary verification session.
- Q6: selected C = mixed responsibility: CLI records emit results/resync hints; skills enforce actual-site verification and recovery behavior.
- Q7: selected C = concise by default, detailed evidence for important transitions and failures.
- Q8: added by direct user instruction = Stage and Phase authoring must use Korean for human-readable content while machine-facing values remain English.

## Superpowers Routing

- `Custom Workflow Skillset:deep-interview` used to clarify scope and write this requirements handoff.
- `Superpowers:brainstorming` was read because this is a behavior/design change, but the user explicitly requested deep-interview style requirements clarification rather than immediate implementation.
- Implementation should later route through `Superpowers:test-driven-development` for CLI/test changes and `Superpowers:verification-before-completion` before claiming completion.

## Open Questions

- None blocking. Implementation may choose the exact reference-doc split, as long as the acceptance criteria stay covered.

## Likely Touchpoints

In `wily-roadmap`:

- `plugins/wily-roadmap/skills/wily-workflow/SKILL.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/runner-adapter-contract.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/routing-policy.md`
- `plugins/wily-roadmap/skills/wily-workflow/references/planning-style.md`
- `plugins/wily-roadmap/skills/wily-start/SKILL.md`
- `plugins/wily-roadmap/skills/wily-run/SKILL.md`
- `plugins/wily-roadmap/skills/wily-decompose-stage/SKILL.md`
- `plugins/wily-roadmap/skills/wily-complete/SKILL.md`
- `plugins/wily-roadmap/skills/wily-block/SKILL.md`
- `plugins/wily-roadmap/skills/wily-retry/SKILL.md`
- `plugins/wily-roadmap/skills/wily-replan/SKILL.md`
- `plugins/wily-roadmap/skills/wily-init/SKILL.md`
- `plugins/wily-roadmap/commands/*.md`
- `plugins/wily-roadmap/scripts/wily.py`
- `plugins/wily-roadmap/tests/test_wily_cli.py`

In `wily-board`, if operations docs are updated there:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`

## Verification Ideas

- Run focused Wily CLI tests for Board live config diagnostics, emit result recording, and `board sync-local`.
- Run command skill tests that assert state-changing skill docs mention Board reflection/actual-site verification.
- Run `python3 -m unittest discover plugins/wily-roadmap/tests`.
- Run `python3 plugins/wily-roadmap/scripts/wily.py board check --probe`.
- For an implementation smoke, use a safe local or approved production scenario:
  - perform or replay a Board-visible state change;
  - verify emit result;
  - verify actual Board site visually in browser;
  - verify failure path if live config is missing.
