# Stage 31 Heartbeat Tail + SSE Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Stage 31 by stabilizing Wily live-event identity, Board live-event ingestion, HMAC rotation, heartbeat TTL expiry, and frontend SSE reconnect behavior.

**Architecture:** Split the work into three independent lanes. Lane A owns the Wily CLI client in this repository. Lane B owns Wily Board backend event ingestion in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`. Lane C owns Wily Board frontend SSE behavior and can run in parallel with Lane B because the backend already accepts a `repo` filter for `/api/sse/live`.

**Tech Stack:** Python 3.11, pytest, FastAPI, SQLite, Next.js 15, React 19, TanStack Query, native `EventSource`.

---

## Current State

- Stage: `s31` is ready and decomposed.
- Ready phases: `s31/31-1`, `s31/31-2`, `s31/31-3`, `s31/31-4`, `s31/31-5`.
- `s31` itself is not executable in `wily-roadmap-v2`; workers must claim phase refs such as `s31/31-1`.
- Current worktree note: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` has an unrelated untracked file `agent-handoffs/p6-bridge-durable-sync-handoff.md`.

## Parallel Execution Map

Run these lanes at the same time only if each worker gets the listed write scope.

| Lane | Phase refs | Write scope | Can run with |
| --- | --- | --- | --- |
| A. Wily CLI live-event client | `s31/31-1`, client part of `s31/31-2`, `s31/31-4` | `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py` | B, C |
| B. Board live-event backend | server part of `s31/31-1`, server part of `s31/31-2`, `s31/31-3`, Board config part of `s31/31-4` | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/signature.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/webhook.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_signature.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_webhook.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md` | A, C |
| C. Board frontend SSE | `s31/31-5` | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/api/sse/live/route.ts`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py` | A, B |
| D. Integration | all `s31` phases | both repos, no parallel edits | after A, B, C |

Do not let two workers edit the same file. In particular, Lane B and Lane C must not both edit `app/api/routes.py`; the backend SSE route already accepts `repo_filter`, so Lane C should only add a focused regression test if needed.

## Lane A: Wily CLI Live-Event Client

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`

### Task A1: Add stable `event_id` generation to every Board live payload

- [ ] Add failing tests in `test_wily_cli.py`:
  - `test_emit_board_live_event_includes_event_id`
  - `test_emit_board_live_event_preserves_supplied_event_id`
  - `test_emit_board_live_event_uses_unique_event_ids_for_distinct_events`

Expected checks:

```python
assert "event_id" in payload
assert isinstance(payload["event_id"], str)
assert payload["event_id"]
assert payload["event_id"] == "evt-fixed-1"  # when phase already contains event_id
```

- [ ] Run the failing tests:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "event_id" -q
```

Expected: new tests fail because payloads do not contain `event_id`.

- [ ] Implement `new_live_event_id()` in `wily.py` using stdlib only. Use a sortable millisecond prefix plus random hex so no new dependency is introduced:

```python
def new_live_event_id() -> str:
    millis = int(time.time() * 1000)
    return f"{millis:013x}-{uuid.uuid4().hex}"
```

Add `import uuid` near existing imports.

- [ ] In `emit_board_live_event`, include:

```python
"event_id": str(phase.get("event_id") or new_live_event_id()),
```

This keeps retries idempotent when callers reuse a supplied `event_id`, and gives normal command-boundary events unique ids.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "event_id" -q
```

Expected: PASS.

### Task A2: Emit `renamed` for active local sessions and update active registry

- [ ] Add helper-level failing tests in `test_wily_cli.py`:
  - `test_emit_renamed_live_events_updates_active_registry_item_id`
  - `test_emit_renamed_live_events_skips_sessions_without_matching_item`
  - `test_emit_renamed_live_events_keeps_workflow_local_when_board_missing`

Test fixture shape:

```json
{
  "session_id": "sid-1",
  "item_type": "stage",
  "item_id": "s21",
  "current_item_id": "s21",
  "stage_id": "s21",
  "agent": "codex",
  "actor": "airmang"
}
```

Expected emitted event:

```python
assert event == "renamed"
assert payload["session_id"] == "sid-1"
assert payload["item_id"] == "s21"
assert payload["current_item_id"] == "s22"
assert payload["old_item_id"] == "s21"
assert payload["new_item_id"] == "s22"
```

- [ ] Run the failing tests:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "renamed_live" -q
```

- [ ] Implement a narrow helper in `wily.py`:

```python
def emit_renamed_live_events(root: Path, old_item_id: str, new_item_id: str) -> list[BoardLiveEventResult]:
    results: list[BoardLiveEventResult] = []
    for path in active_live_registry_files(root):
        payload = read_live_registry(path)
        if str(payload.get("current_item_id") or payload.get("item_id") or "") != old_item_id:
            continue
        updated = {**payload, "item_id": old_item_id, "current_item_id": new_item_id, "old_item_id": old_item_id, "new_item_id": new_item_id}
        path.write_text(json.dumps({**payload, "item_id": new_item_id, "current_item_id": new_item_id}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(emit_board_live_event(root, updated, "renamed", "active"))
    return results
```

Keep failure best-effort like existing Board live emits.

- [ ] Wire the helper into the roadmap mutation path that changes item ids. Start with the replan path where old and new ids are known. If the current implementation changes only title/path slugs without changing `id`, do not emit `renamed`; this event is only for item id changes.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "renamed_live or replan" -q
```

Expected: PASS.

### Task A3: Add heartbeat TTL env default and self-suicide regression

- [ ] Add failing tests in `test_wily_cli.py`:
  - `test_live_heartbeat_uses_env_ttl_when_ttl_arg_missing`
  - `test_live_heartbeat_ttl_arg_overrides_env`
  - `test_live_heartbeat_ttl_expiry_releases_and_exits`

Use `patch.object(wily.time, "monotonic", side_effect=[0.0, 3.0])` and `patch.object(wily.time, "sleep", return_value=None)` so the TTL test does not wait in real time.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "heartbeat and ttl" -q
```

- [ ] Implement:

```python
DEFAULT_HEARTBEAT_TTL_SECONDS = 14400.0

def heartbeat_ttl_from_env() -> float:
    raw = os.environ.get("WILY_BOARD_HEARTBEAT_TTL_SECONDS", "").strip()
    if not raw:
        return DEFAULT_HEARTBEAT_TTL_SECONDS
    try:
        ttl = float(raw)
    except ValueError:
        return DEFAULT_HEARTBEAT_TTL_SECONDS
    return ttl if ttl >= 0 else DEFAULT_HEARTBEAT_TTL_SECONDS
```

Initialize `ttl = heartbeat_ttl_from_env()` and keep explicit `--ttl` parsing as the override.

- [ ] Preserve existing behavior for `--ttl 0`: zero disables TTL expiry for that command.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py -k "live_heartbeat or board_live_event or renamed_live" -q
```

Expected: PASS.

## Lane B: Board Live-Event Backend

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/config.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/signature.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/webhook.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_config.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_signature.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_webhook.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`

### Task B1: Support `WILY_BOARD_SECRETS` dual HMAC rotation

- [ ] Add failing tests:
  - `tests/test_config.py::test_settings_builds_wily_board_secrets_from_rotation_env`
  - `tests/test_signature.py::test_verify_signature_any_accepts_current_or_previous_secret`
  - `tests/test_live_events.py::test_live_event_accepts_previous_rotation_secret`
  - `tests/test_webhook.py::test_webhook_accepts_previous_rotation_secret`

Expected config behavior:

```python
monkeypatch.setenv("WILY_BOARD_SECRETS", "new-secret, old-secret")
monkeypatch.setenv("WILY_BOARD_SECRET", "legacy-secret")
settings = Settings.from_env()
assert settings.wily_board_secrets == ("new-secret", "old-secret", "legacy-secret")
assert settings.wily_board_secret == "new-secret"
```

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_config.py tests/test_signature.py tests/test_live_events.py -k "secret or signature" -q
```

- [ ] Implement `wily_board_secrets: tuple[str, ...]` in `Settings`. Build it from `_split_csv(os.environ.get("WILY_BOARD_SECRETS", "")) + (WILY_BOARD_SECRET,)`, dedupe while preserving order, and set `wily_board_secret` to the first secret for backwards compatibility.

- [ ] Add `verify_signature_any(secrets: Iterable[str], body: bytes, signature: str) -> bool` in `app/sync/signature.py`.

- [ ] Update live event, live claims, and GitHub webhook routes to use `verify_signature_any(settings.wily_board_secrets, ...)`.

- [ ] Keep `settings.wily_board_secret` as the first/current secret for signing examples and backwards-compatible callers, but use `wily_board_secrets` for verification.

- [ ] Run the same pytest command. Expected: PASS.

### Task B2: Add `(session_id, event_id)` five-minute dedup

- [ ] Add failing tests in `tests/test_live_events.py`:
  - `test_live_event_dedups_same_session_and_event_id`
  - `test_live_event_dedup_is_scoped_by_session_id`
  - `test_live_event_dedup_expires_after_five_minutes`

Expected HTTP behavior:

```python
assert first.status_code == 200
assert first.json() == {"stored": True}
assert second.status_code == 200
assert second.json() == {"stored": True, "dedup": True}
```

Expected DB behavior: duplicate request does not create a second `live_event` audit row and does not call `upsert_live_item` a second time.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_live_events.py -k "dedup" -q
```

- [ ] Implement a process-local lazy-expiry cache in `app/live/events.py`:

```python
DEDUP_WINDOW_SECONDS = 300.0
DEDUP_MAX_KEYS = 10000
_dedup_seen: dict[tuple[str, str], float] = {}
```

Use server monotonic time. On every live event, prune expired keys and trim oldest keys over the cap.

- [ ] Apply dedup after JSON validation and before DB writes. Only dedup when both `session_id` and `event_id` are non-empty. Events missing either field continue through the existing path for backwards compatibility.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_live_events.py -q
```

Expected: PASS.

### Task B3: Handle `renamed` events

- [ ] Add failing test:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_live_events.py -k "renamed" -q
```

Required scenario: send an initial `claimed` event with `session_id="sid-rename"` and `item_id="s21"`, then send `renamed` with `old_item_id="s21"`, `new_item_id="s22"`, `current_item_id="s22"`. Assert the visible live item has `current_item_id == "s22"` and keeps `session_id == "sid-rename"`.

- [ ] Implement by normalizing `renamed` payloads before `upsert_live_item`:

```python
if payload.get("event") == "renamed":
    payload = {**payload, "current_item_id": payload.get("new_item_id") or payload.get("current_item_id") or payload.get("item_id")}
```

Reject malformed renamed events with a 400 when `session_id`, `old_item_id`, or `new_item_id` is missing.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_live_events.py tests/test_db.py -k "renamed or live_item" -q
```

Expected: PASS.

### Task B4: Document secret rotation

- [ ] Add an operations section to `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md` named `HMAC Secret Rotation`.

Include this exact operational flow:

```text
1. Generate a new value with `openssl rand -hex 32`.
2. Set `WILY_BOARD_SECRETS=new,old` on Board and deploy.
3. Update user or repo Wily live config to sign with `new`.
4. Keep `old` for seven days.
5. After seven days, remove `old` so `WILY_BOARD_SECRETS=new`.
6. If compromise is suspected, deploy `new` immediately and remove the compromised value after all active clients are updated.
```

- [ ] Update `tests/test_operations_doc.py` if it asserts required operational keywords.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_operations_doc.py -q
```

Expected: PASS.

### Task B5: Expose Board heartbeat TTL setting

- [ ] Add failing config test:

```python
def test_settings_reads_live_heartbeat_ttl_seconds(monkeypatch):
    monkeypatch.setenv("WILY_BOARD_HEARTBEAT_TTL_SECONDS", "42")
    settings = Settings.from_env()
    assert settings.live_heartbeat_ttl_seconds == 42
```

- [ ] Implement `live_heartbeat_ttl_seconds: int` in `Settings`, defaulting to `14400`.

- [ ] Document `WILY_BOARD_HEARTBEAT_TTL_SECONDS` in `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md` as the client/sidecar TTL default used by Wily live heartbeat clients.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_config.py tests/test_operations_doc.py -q
```

Expected: PASS.

## Lane C: Board Frontend SSE

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
- Verify or minimally modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/api/sse/live/route.ts`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py` only for backend `repo_filter` regression coverage.

### Task C1: Scope repo workspace SSE with `?repo=owner/name`

- [ ] Confirm backend route already accepts `repo: str | None` and passes `repo_filter=repo` into `_live_sse_events`.

- [ ] Add or keep a backend regression test in `tests/test_api_routes.py`:
  - `test_api_sse_live_repo_filter_limits_snapshot_to_requested_repo`

Expected: two visible repos have live items, request stream with `repo_filter="R-W-LAB/wily-roadmap"`, and assert only `R-W-LAB/wily-roadmap` appears.

- [ ] In `live-refresh.tsx`, import `usePathname` from `next/navigation`.

- [ ] Add a parser:

```ts
function repoFilterFromPath(pathname: string): string | null {
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] !== "repos" || !parts[1] || !parts[2]) {
    return null;
  }
  return `${decodeURIComponent(parts[1])}/${decodeURIComponent(parts[2])}`;
}
```

- [ ] Build the EventSource URL:

```ts
const repoFilter = repoFilterFromPath(pathname);
const url = repoFilter ? `/api/sse/live?repo=${encodeURIComponent(repoFilter)}` : "/api/sse/live";
```

Hub pages such as `/me` and `/collab` keep the unfiltered stream.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_api_routes.py -k "sse_live" -q
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
```

Expected: PASS.

### Task C2: Add manual backoff and tab visibility handling

- [ ] Refactor `LiveRefresh` effect to own:

```ts
const retryDelays = [1000, 2000, 5000, 15000];
let retryIndex = 0;
let retryTimer: ReturnType<typeof setTimeout> | null = null;
let source: EventSource | null = null;
let failureCount = 0;
```

- [ ] Implement `connect()` so `open` resets `retryIndex` and dismisses the toast.

- [ ] On `error`, close the source, increment failure count, schedule `connect()` using the backoff sequence, and after the fifth failure show:

```ts
toast("Connection lost - refresh page", { id: "live-disconnected" });
```

Keep automatic retries running after the toast.

- [ ] Add visibility handling:

```ts
function handleVisibilityChange() {
  if (document.hidden) {
    closeSource();
    return;
  }
  invalidateAllLiveQueriesOnce();
  connect();
}
```

`invalidateAllLiveQueriesOnce()` must invalidate `desk`, `repos`, and `repoRoot`; if a repo filter exists, also invalidate `repo(owner, name)` and `repoDesk(owner, name)`.

- [ ] Cleanup must remove the visibility listener, clear pending retry timers, and close the active EventSource.

- [ ] Run:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: PASS.

## Lane D: Integration and Verification

Run after Lanes A, B, and C are complete.

- [ ] Verify Wily CLI tests:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py plugins/wily-roadmap/tests/test_wily_watch_ui.py -q
```

- [ ] Verify Board backend tests:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest tests/test_live_events.py tests/test_config.py tests/test_signature.py tests/test_api_routes.py tests/test_db.py tests/test_operations_doc.py -q
uv run pytest tests/test_webhook.py -q
```

- [ ] Verify Board frontend:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

- [ ] Manual local smoke:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run dev
```

Open `http://127.0.0.1:3000/repos/R-W-LAB/wily-roadmap` and confirm the browser requests `/api/sse/live?repo=R-W-LAB%2Fwily-roadmap`.

- [ ] Manual event smoke with dual secrets:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
WILY_BOARD_SECRET=old WILY_BOARD_SECRETS=new,old uv run pytest tests/test_live_events.py -k "previous_rotation_secret or dedup or renamed" -q
```

- [ ] Manual Wily heartbeat TTL smoke:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap
WILY_BOARD_HEARTBEAT_TTL_SECONDS=2 python3 plugins/wily-roadmap/scripts/wily.py live-heartbeat s31/31-1 --interval 1 --foreground
```

Expected: exits after TTL expiry and emits a final `released` event when Board live config is present. Without Board live config, use the pytest TTL regression as the deterministic proof.

## Completion Sequence

1. Start and complete executable phase refs, not the Stage id:
   - `$wily-start s31/31-1`
   - `$wily-start s31/31-2`
   - `$wily-start s31/31-3`
   - `$wily-start s31/31-4`
   - `$wily-start s31/31-5`
2. If running lanes in parallel, claim each phase from a fresh session and keep worker write scopes disjoint.
3. After verification, mark each phase complete with its own evidence.
4. Commit Wily roadmap state together with the code changes only after the user explicitly asks to commit or land.

## Self-Review

- Coverage: all five Stage 31 phase docs map to at least one lane.
- Parallel safety: no lane shares write scope except final integration.
- Risk: `s31/31-1` touches both client and server semantics, so Lane A and Lane B must agree on `renamed` payload fields: `session_id`, `old_item_id`, `new_item_id`, `current_item_id`.
- Risk: `s31/31-2` dedup is process-local. That matches the Stage request for a memory LRU, but it will not dedup across multiple Board worker processes.
- Risk: frontend manual SSE retry behavior can be hard to unit test because there is no frontend test runner. Treat lint, build, backend SSE tests, and browser Network smoke as the verification floor.
