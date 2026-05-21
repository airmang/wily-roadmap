# Wily Board Agent Visibility Requirements

Date: 2026-05-20
Task: T26
Status: requirements contract

## Decision

The Wily Board UI design is fixed by:

`docs/design/wily-board-mockup.html`

Implementation must copy this visual design as the source of truth. Do not
reinterpret the IA, palette, typography, density, spacing model, component
shape, or interaction hierarchy from older Wily Board specs.

Older Board UI documents remain useful as historical context only where they do
not conflict with this mockup. When they conflict, this requirements document
and `docs/design/wily-board-mockup.html` win.

## Product Boundary

Wily Board is a read-only web supervision board for Wily v3 repositories.

It shows:

- Workspace-level supervision across child repositories.
- Repo-level task state and next work.
- Active agent work by actor, machine, task, and checkpoint.
- Checkpoint timeline and detail inspection.
- Agent freshness, stale state, and sync failure reason.

It does not:

- Claim, block, replan, or complete tasks.
- Write `.wily/` task state.
- Replace Wily CLI or Wily agent as source of truth.
- Expose raw terminal logs as a primary UI.

## Architecture Decision

Use the design-grill architecture decision:

- Server: FastAPI + SQLite + SSE.
- UI: Vite React SPA served as static assets.
- Agent: bundled `wily-agent` in `wily-roadmap`.
- Deployment: Caddy serves static React assets and reverse proxies API/SSE to
  FastAPI.

The old Jinja/htmx UI plan is superseded for the rebuild UI. Jinja may still be
used for minimal auth or fallback shells if needed, but the production Board
experience must implement the selected mockup as React components.

## Canonical UI Contract

### Shell

Copy the mockup shell:

- Sticky topbar.
- Brand block: `WILY BOARD` / `AGENT SUPERVISION`.
- Workspace switch button.
- Day/night mode toggle.
- User chip.
- Two-column desktop shell: fixed left sidebar + centered main content.
- Mobile nav burger in the topbar with `aria-label="메뉴 열기"`.
- On narrow screens, the sidebar becomes a left slide-over drawer instead of
  disappearing. It opens via the burger button, uses `#navScrim`, closes via
  `.drawer-x`, scrim click, route selection, Escape, or resize back above the
  desktop breakpoint.

Production differences:

- The mockup's bottom-left demo preview panel is not a production control.
- Login user comes from GitHub session, not the demo segmented control.
- Theme comes from login actor mapping.
- Day/night mode remains user-controlled.

### Theme

Copy the four theme variants exactly:

- `rock` + `day` for Julirsia / 록맨.
- `rock` + `night`.
- `bass` + `day` for airmang / 포르테.
- `bass` + `night`.

Keep the CSS variable names and semantic color roles when porting to React.
Implementation may place tokens in CSS modules, global CSS, or a design-token
file, but the rendered colors and component styling must match the mockup.

### Typography

Use the mockup's typography:

- Body: `IBM Plex Sans KR`.
- Mono: `IBM Plex Mono`.
- Display: `Chakra Petch`.

Production must either load these fonts from an approved web-font path or
self-host them in the built static assets. If external Google Fonts loading is
blocked in production, self-hosting is required rather than substituting a new
visual style.

### Pages And Views

Implement these views from the mockup:

- Workspace home: `감독 현황`.
- Repo detail.
- CP/task detail slide-over panel.

The workspace home must show:

- Workspace pipeline.
- Rollup strip:
  - 자식 레포
  - 진행 중 작업
  - 차단
  - 완료율
  - 활성 에이전트
- Workspace repo overview rows.
- 내 진행 중 작업.
- 다음 착수 가능:
  - 병렬 가능
  - 의존 대기

The repo detail view must show:

- Breadcrumb and repo metadata.
- Optional stale banner.
- Repo pipeline.
- Parallel-ready task segments in the pipeline must use the mockup's parallel
  segment bracket treatment: `.pl-gap`, `.pl-pgroup`, `.pl-bracket`, and
  `.pl-prow`.
- Status summary chips.
- 진행 중 작업 with checkpoint timeline.
- 그 외 작업.
- 다음 착수 가능.

The slide-over panel must show:

- 체크포인트 상세 heading.
- Standard status.
- Last update.
- Actor.
- Machine.
- Current action.
- Status board import summary.
- Verification result.
- Notes.
- Result/handoff summary.
- Original checkpoint name.

### Components

Copy the mockup component set:

- `Topbar`
- `WorkspaceSwitch`
- `ModeToggle`
- `UserChip`
- `NavBurger`
- `NavDrawerScrim`
- `DrawerCloseButton`
- `Sidebar`
- `WorkspaceCard`
- `RepoNavGroup`
- `Legend`
- `WorkspacePipeline`
- `VerticalPipelineStepper`
- `ParallelSegmentBracket`
- `RollupStrip`
- `RepoOverviewList`
- `ResponsiveRepoRow`
- `TaskList`
- `NextWorkGrid`
- `RepoPipeline`
- `StatusChips`
- `ActiveTaskCard`
- `CheckpointTimeline`
- `CheckpointDetailPanel`
- `StaleBanner`

React component names may vary, but ownership boundaries should stay close to
this list so the implementation remains traceable to the mockup.

## Data Contract Required By UI

The API must provide a workspace snapshot payload that can render the mockup
without client-side inference beyond sorting, filtering, and simple progress
math.

### Workspace Snapshot

```json
{
  "title": "Wily Plugin Workspace",
  "manifest": "wily-workspace.yaml",
  "root": "~/Code/projects/wily-plugin",
  "current_user": {
    "handle": "Julirsia",
    "display": "록맨",
    "machine": "ROCK-1",
    "theme": "rock"
  },
  "repos": []
}
```

### Repo Summary

Each repo item must include:

```json
{
  "id": "wily-board",
  "group": "collab",
  "remote": "R-W-LAB/wily-board",
  "branch": "feat/agent-visibility",
  "agent": {
    "owner": "airmang",
    "online": true,
    "last_seen_label": "12분 전",
    "last_seen_at": "2026-05-20T08:45:00Z"
  },
  "stale": false,
  "sync_note": null,
  "tasks": []
}
```

Rules:

- `group` is `collab` for `R-W-LAB` org remotes, otherwise `personal` unless a
  future explicit visibility field overrides it.
- `id` is the human repo slug used in the UI.
- The database project id may remain a hash internally, but API responses must
  include the display slug.
- `sync_note` must be a Korean user-facing message when present.

### Task Summary

Each task must include:

```json
{
  "id": "T26",
  "title": "Wily Board 에이전트 가시성 요구사항과 계약 확정",
  "status": "working",
  "owner": "Julirsia",
  "deps": [],
  "parallel": true,
  "cps": []
}
```

UI statuses are normalized to:

- `waiting`
- `working`
- `verifying`
- `blocked`
- `done`
- `stale`

Mapping from Wily task state:

| Wily source | UI status |
|---|---|
| `ready` | `waiting` |
| `in_progress` with current verification CP | `verifying` |
| `in_progress` otherwise | `working` |
| `blocked` | `blocked` |
| `done` | `done` |
| missing heartbeat or old agent data | `stale` |

### Checkpoint Summary

Each checkpoint must include:

```json
{
  "id": "CP3",
  "name": "키보드 탐색·접근성 검증",
  "status": "verifying",
  "owner": "Julirsia",
  "updated": "5분 전",
  "updated_at": "2026-05-20T08:43:00Z",
  "action": "axe 접근성 점검 및 포커스 순회 검증 중",
  "verify": "진행 중 — 위반 0건 목표",
  "board": "상태판: 검증 중 · \"axe 스캔 실행\"",
  "note": "스크린리더 라벨은 한국어 우선",
  "handoff": "—"
}
```

Rules:

- `updated` is display text; `updated_at` is sortable source time.
- `board` is the status board import summary.
- `handoff` is the result/handoff summary, not the full raw file unless short.
- If a task has no checkpoints, the detail panel must show the mockup's
  unstarted checkpoint message and point to `.wily/tasks/<task-id>/progress.jsonl`.

## Agent Payload Contract

`wily-agent` must produce enough data for the UI contract above.

Snapshot payload v1 must include:

- Project identity:
  - normalized remote
  - display repo slug
  - branch
  - local path
  - workspace manifest metadata when available
- Actor identity:
  - actor id
  - display name
  - GitHub login if known
  - machine hostname
  - theme hint if configured
- Task list:
  - id, title, intent, acceptance, scope
  - depends_on
  - status
  - assignee, actor
  - claim_sha, claim_at, done_at, blocker
  - parallel metadata when present
- Checkpoint timeline:
  - ordered CP id/name
  - normalized CP status
  - current action
  - last update timestamp
  - verification text
  - status board import summary
  - note
  - result/handoff summary
- Presence:
  - current project
  - current task
  - current checkpoint when known
  - last_seen timestamp
- Recovery metadata:
  - status board discovery path
  - imported event count
  - skipped duplicate count
  - import warnings
- Sync health:
  - last successful push
  - last failed push
  - last failure reason
  - client version

Heartbeat payload must include:

```json
{
  "project_id": "<project-id-or-null>",
  "repo_slug": "wily-roadmap",
  "actor": "Julirsia",
  "machine": "ROCK-1",
  "current_task_id": "T26",
  "current_cp": "requirements-contract",
  "status": "working",
  "captured_at": "2026-05-20T08:45:00Z"
}
```

Heartbeat alone may update live presence, but snapshot remains the recovery
source for task/checkpoint data.

## Database Contract

Board SQLite stores projection/cache data only.

Required tables or equivalent persisted models:

- users
- machines
- projects
- project_machines
- task_snapshots
- tasks
- task_progress
- cp_events
- project_actors
- task_results
- observed_commits
- agent_events
- actor_presence
- oauth_sessions
- ui_preferences

Additional requirements:

- Store the latest renderable workspace/repo snapshot for fast API responses.
- Store event history for approximately 30 days.
- Store only hashed machine tokens.
- Do not store terminal logs or raw secrets.
- Keep `.wily/` parsing responsibility primarily in `wily-agent`; Board stores
  validated payloads and projections.

## Status Board Import And Recovery

`progress.jsonl` is the durable ledger.

Custom Workflow status board files are recovery/import hints:

- Discover status board files under `agent-handoffs/*-status.md` when a task is
  active or referenced by execution package metadata.
- Import only missing checkpoint state that can be tied to a Wily task.
- Use idempotency keys so repeated imports do not duplicate events.
- Ledger entries win over status board text when they conflict.
- Status board text may supply:
  - current action
  - verification state
  - note
  - result/handoff summary
- Record import warnings in agent sync health and surface them in the CP detail
  panel when relevant.

## React IA

Routes:

- `/` redirects to `/workspace`.
- `/workspace` renders the workspace home.
- `/repos/:repoSlug` renders repo detail.
- `/repos/:repoSlug/tasks/:taskId` may deep-link a task and open the detail
  panel.
- `/repos/:repoSlug/tasks/:taskId/cp/:cpId` may deep-link a checkpoint and open
  the detail panel.

State:

- Workspace snapshot query populates shell, sidebar, home, and repo views.
- SSE events invalidate or patch affected repo snapshots.
- Day/night mode persists per user.
- Theme is actor-derived, not a free user setting.

SSE events:

- `workspace_updated`
- `repo_updated`
- `presence`
- `sync_health`

Client behavior:

- Project/repo rows navigate without full page reload.
- Pipeline nodes open repo or task/CP detail.
- Task rows open the slide-over panel.
- Clicking scrim or close closes the panel.
- Mobile burger opens the sidebar drawer.
- Drawer close button, nav scrim click, route selection, Escape, and resize
  above `980px` close the sidebar drawer.
- On mobile, repo pipeline clicks still open the selected task's current CP.
- Reduced-motion preferences disable pulse/entrance animation.

Responsive behavior:

- At `max-width:1180px`, main content padding tightens.
- At `max-width:980px`, shell becomes one column, `next-grid` and detail field
  grids become single-column, nav burger is visible, and sidebar becomes a
  slide-over drawer with `.sidebar.open`.
- At `max-width:640px`, topbar compacts: workspace switch is hidden, brand
  subtitle is hidden, user metadata is hidden, and the user chip becomes avatar
  only.
- At `max-width:640px`, CP detail panel is full width.
- At `max-width:640px`, repo overview rows become stacked using the mockup's
  grid areas: `id`, `chev`, `meter`, `prog`, and `next`.
- At `max-width:640px`, task rows wrap onto multiple lines and hide the mini
  meter.
- At `max-width:640px`, horizontal pipelines become a vertical stepper. `.pl-link`
  changes from horizontal connector to vertical connector, and filled links use
  the vertical gradient.
- `html, body` must keep `overflow-x: clip` to prevent mobile horizontal scroll
  from drawer/pipeline transitions.

## Korean UI Glossary

Use these labels in the UI:

| Internal term | Korean UI |
|---|---|
| workspace | 워크스페이스 |
| manifest | 매니페스트 |
| repository | 레포 |
| personal | 개인 |
| collaboration | 협업 |
| supervision | 감독 |
| task | 작업 |
| checkpoint | 체크포인트 |
| ready/waiting | 대기 |
| in progress/working | 작업 중 |
| verifying | 검증 중 |
| blocked | 차단 |
| done | 완료 |
| stale | 오래됨 |
| next ready | 다음 착수 가능 |
| parallel ready | 병렬 가능 |
| dependency waiting | 의존 대기 |
| current action | 현재 액션 |
| status board import | 상태판 요약 |
| verification result | 검증 결과 |
| handoff/result | result / handoff 요약 |
| actor presence | 활성 에이전트 |
| sync failure | 동기화 실패 |
| last successful sync | 마지막 성공 동기화 |
| no agent | 에이전트 없음 |

Do not expose implementation terms such as `snapshot`, `heartbeat`, `SSE`,
`payload`, `projection`, or `SQLite` in primary UI copy unless the user opens a
technical detail view.

## Deployment Requirements

Azure deployment target:

- Caddy terminates HTTPS.
- Caddy serves the React build output.
- Caddy reverse proxies `/api/*`, `/auth/*`, and `/sse` to FastAPI.
- FastAPI runs under systemd.
- SQLite is on persistent disk and backed up daily.
- Machine token registration is browser-authenticated and one-time-code based.
- `/agent/*` accepts only bearer machine tokens.
- Browser auth uses GitHub OAuth allowlist.
- Production deploy, server mutation, SSH, and secret handling remain
  approval-first.

## Implementation Notes For Copying The Mockup

The implementation should copy:

- CSS variables and theme tokens.
- Layout breakpoints.
- Component radii and borders.
- Mobile nav drawer classes and behavior: `.nav-burger`, `.drawer-x`,
  `#navScrim`, and `.sidebar.open`.
- Pipeline and checkpoint timeline visual language.
- The pipeline parallel segment bracket classes and behavior:
  `.pl-gap`, `.pl-pgroup`, `.pl-bracket`, and `.pl-prow`.
- Mobile stacked repo rows and vertical pipeline stepper behavior.
- Slide-over detail panel.
- Korean visible copy.
- Dense operational information hierarchy.

The implementation should replace:

- Static `WS` sample data with API data.
- Static `ACTORS` with actor/session config.
- Demo preview panel with real session behavior.
- Inline script rendering with React components.

The implementation should not replace:

- The visual direction.
- The home/repo/detail IA.
- The status color model.
- The actor theme mapping concept.
- The CP timeline-first supervision model.

## Open Questions

No implementation-blocking open questions remain for T26.

Non-blocking follow-up decisions:

- Font delivery: production may load the selected fonts from Google Fonts or
  self-host them, but it must not substitute a different visual system.
- Theme mapping source: initial implementation may hard-code the Julirsia/rock
  and airmang/bass mapping in server config or actor metadata; later Wily config
  can make this user-editable.
- Deep links: `/repos/:repoSlug/tasks/:taskId` and
  `/repos/:repoSlug/tasks/:taskId/cp/:cpId` are required by the IA contract, but
  the first implementation may open the correct panel after loading the normal
  repo snapshot rather than adding separate API endpoints.
- Event retention: keep approximately 30 days unless production disk pressure
  proves a smaller retention window is needed.
- Exact stale thresholds: UI must support stale display and sync failure text;
  the first server/agent implementation may choose conservative thresholds and
  tune them after smoke testing.

These are not blockers because they do not change the source of truth, API/DB
shape, agent payload shape, or final UI direction.

## Implementation Handoff

Use this document plus `docs/design/wily-board-mockup.html` as the handoff for
the next implementation tasks.

For T28 (`wily-agent snapshot heartbeat와 상태판 import recovery 구현`):

- Build snapshot and heartbeat payloads that satisfy `Agent Payload Contract`.
- Include enough checkpoint/status-board/result metadata for the slide-over
  detail panel.
- Preserve the rule that `progress.jsonl` is durable and status board import is
  recovery/hint data.
- Include sync health fields needed by stale banners and Korean failure copy.
- Do not implement Board server/UI code in `wily-roadmap`.

For the sibling `wily-board` rebuild:

- Create the fresh `wily-board` repository as a separate sibling repo.
- Implement FastAPI/SQLite/SSE as the projection/cache layer.
- Serve a Vite React SPA that copies `docs/design/wily-board-mockup.html`.
- Treat older Jinja/htmx UI plans as historical where they conflict with the
  React mockup contract.
- Implement mobile drawer, stacked rows, full-width mobile CP panel, vertical
  pipeline stepper, and parallel segment bracket behavior from the mockup.
- Keep the Board read-only for Wily task state.

T26 completion evidence:

- UI source of truth is fixed.
- API-facing render data is specified.
- Agent payload and heartbeat requirements are specified.
- DB/projection responsibilities are specified.
- Status board import/recovery rules are specified.
- Korean UI glossary is specified.
- Azure deployment boundary is specified.
- No implementation files are changed by this task.

## Follow-up Task Boundaries

T28 (`wily-agent snapshot heartbeat와 상태판 import recovery 구현`) must implement
the agent-side payload and import behavior required above.

The sibling `wily-board` rebuild must implement:

- Server/API/DB projection.
- Vite React UI copied from the mockup.
- SSE live updates.
- Azure deployment assets.

No implementation files are changed by T26.
