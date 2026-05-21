# Requirements Handoff: Board Live Local State And Checkpoint Visibility

## Source Request

The user reported that Wily Board does not show Custom Workflow Skillset checkpoint concepts, especially the phase decomposition stage, and does not reflect work data in real time. The concrete example is this repository: `wily status` reports the current Stage as `s25`, but Wily Board still shows only through `s24`.

The user asked to create this handoff first, then run a goal from it.

## Desired Outcome

Wily Board must show the same current local Wily operating state that `wily status` shows before commit/push/GitHub durable sync catches up:

- locally added or decomposed Stages such as `s25`;
- their child Phases such as `25-1` through `25-4`;
- Custom Workflow checkpoint overlay data attached to those Phases;
- live work, heartbeat, worked, stale, and awaiting-push state;
- a clear distinction between durable GitHub-synced roadmap state and local live/draft overlay state.

## In Scope

- Add or harden a Wily Roadmap CLI path that can emit or replay the current local decomposed Stage topology to Board as signed live draft data.
- Ensure local roadmap changes made by replan/manual Wily roadmap authoring are not invisible merely because they did not go through `wily decompose-stage`.
- Extend Wily Board's API and Next.js UI path to consume `live_drafts`, not only the older Jinja/HTMX routes.
- Show draft-only Stages in repo detail and repo lists/progress when durable Board DB state is behind local `.wily`.
- Merge draft Phases with live checkpoint/work overlays so a draft Phase row can show the Custom Workflow current checkpoint, progress, action, verification, and recent activity.
- Make SSE/live refresh trigger a router refresh for draft topology events as well as live item and durable sync events.
- Preserve durable `.wily` Git sync as the authority and keep local overlays clearly provisional.
- Add focused tests in both `wily-roadmap` and `wily-board`.

## Non-Goals

- Do not make Wily Board the durable roadmap source of truth.
- Do not add mutation controls, PR-writing workflows, admin panels, hooks, MCP servers, or app integrations.
- Do not make Board poll developer machines or read local repositories directly.
- Do not use production secrets in tests or commit local Board config.
- Do not deploy, restart production services, push to GitHub, or run production smoke without explicit approval.
- Do not broaden this into the Stage `s25` UI polish work; this is a data freshness and visibility fix.

## Decision Boundaries

- Goal-scoped local engineering changes may proceed autonomously once the goal starts.
- Editing both local repositories is in scope:
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
  - `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
- Preserve all pre-existing dirty work. Do not revert user changes.
- Stop for hard destructive commands, credential/secret exposure, production live event emission, production deploy/restart, GitHub push/PR/merge, or repeated verification failure without new evidence.

## Acceptance Criteria

- `wily status` still reports this repo as version 27 with current Stage `s25`.
- Wily CLI has a local-first way to replay the current local decomposed Stage topology to Board without requiring GitHub sync.
- The replay payload includes enough Stage metadata for Board to render a Stage missing from durable DB state: id, title, status, owner, depends_on, execution mode, raw path, position when available, and normalized child Phases.
- Board API `/api/repos/{owner}/{name}` includes draft-only Stages and draft child Phases when durable data is behind.
- Board API repo progress can show local draft stage totals, so `R-W-LAB/wily-roadmap` can represent `24/25` instead of appearing complete at `24/24`.
- Draft Phase rows can show live checkpoint overlays from `live_items`/`live_sessions`.
- Board Hub/MY DESK has at least one visible follow-up or active item for local draft topology awaiting push.
- SSE refresh covers draft/live events so the Next.js UI refreshes after local draft or checkpoint events.
- Existing durable sync reconciliation remains: once durable GitHub sync imports matching child Phases, draft rows are hidden/cleared.
- Tests prove the regression: a durable DB ending at `s24` plus a live draft for `s25` renders `s25` and `25-1` through the API/Next-facing payload.

## Constraints

- Keep plugin behavior local-first and approval-first for remote actions.
- Keep `.agents/plugins/marketplace.json` and `plugins/wily-roadmap/.codex-plugin/plugin.json` untouched unless strictly required; they are not expected touchpoints.
- Do not add hooks, MCP servers, or app integrations.
- Board remains read-only for roadmap state.
- Avoid schema changes unless existing `live_drafts`/payload storage cannot support the requirement. Current evidence suggests schema changes are unnecessary.

## Repo Facts

- `python3 plugins/wily-roadmap/scripts/wily.py status` reports:
  - roadmap version 27;
  - `24/25`, 96%;
  - current/next Stage `s25`;
  - next Phase `25-1`.
- Current local Wily tree has modified `.wily/roadmap.yaml` and `.wily/status.md`, plus untracked `.wily/stages/s25-wily-board-ui-polish-usability/`.
- `wily board check --probe` reports live Board config, signature, Codex hook, and endpoint are OK, with secrets redacted.
- No `.wily/local/live` or `.wily/local/board-last-emit.json` files are currently present, so the current `s25` topology has not been replayed as local live data.
- Stage 23 already implemented a `stage_decomposed_local` live draft topology path, stored in Board `live_drafts`.
- Existing Board Jinja/HTMX route `app/web/routes.py` reads `list_live_drafts_by_stage()` and can render draft phases when a durable Stage has no phases.
- Current Next/API route `app/api/routes.py` does not read `live_drafts` in `_repo_detail_payload`, `_desk_payload`, repo progress, or SSE event visibility.
- Current Next `PhaseList` can render checkpoint rows for durable phases with live items, but it has no draft phase concept.
- Current Board DB helpers can store and list `live_drafts`; they need API-facing projection for draft-only Stages and draft Phases.
- Wily CLI emits draft topology only from `decompose-stage`; local Stage additions from replan/manual roadmap authoring can remain invisible unless a replay/sync command exists.

## Assumptions

- The immediate product expectation is that local Wily state should be visible on Board before commit/push, but visibly marked as local/provisional.
- A new Wily CLI subcommand under `wily board`, such as `wily board sync-local [stage-id]`, is acceptable because it is local-first and does not add hooks or integrations.
- The production Board can accept signed live events, but production smoke remains approval-gated.
- Existing dirty Board changes in `app/live/events.py` and `tests/test_live_events.py` are pre-existing S24 checkpoint validation work and must be preserved.

## Decision Log

- Repo facts answered the key ambiguity, so no user question was asked before writing this handoff.
- Scope is a freshness/data-surface fix, not the broader `s25` UI polish Stage.
- Use Custom Workflow Skillset `deep-interview` for this handoff and `plan-goal-runner` for the execution package.
- Superpowers `brainstorming` was read because behavior/UI changes are involved; its user-review gates will be recorded as Custom Workflow progress checkpoints once the explicit goal starts.

## Superpowers Routing

- `Superpowers:brainstorming`: read for requirements/design discipline; written handoff replaces a separate design doc for this focused bugfix because the user explicitly requested a Custom Workflow handoff first.
- `Superpowers:test-driven-development`: required before implementation because this changes CLI/API/UI behavior.
- `Superpowers:systematic-debugging`: use for failing tests or unexpected live/SSE behavior.
- `Superpowers:verification-before-completion`: required before claiming done.

## Open Questions

- None blocking. Production smoke/deploy/push requires later explicit approval.

## Likely Touchpoints

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`

## Verification Ideas

- `python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest`
- targeted Wily CLI tests for local board draft replay.
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest tests/test_api_routes.py tests/test_live_events.py tests/test_web_routes.py`
- `cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend && npm run lint && npm run build`
- Local smoke with temporary Board DB:
  - durable repo data through `s24`;
  - signed local draft event for `s25`;
  - signed checkpoint event for `25-1`;
  - API repo detail shows `s25`, draft phases, and checkpoint;
  - SSE emits a refresh-causing event after draft/checkpoint updates.
