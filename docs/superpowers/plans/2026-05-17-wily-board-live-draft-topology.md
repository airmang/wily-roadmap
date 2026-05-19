# Wily Board Live Draft Topology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make locally decomposed Wily Stages appear on Wily Board before commit and push, then reconcile those provisional rows after durable GitHub sync.

**Architecture:** Keep presence events in `live_items` and add topology drafts in a new `live_drafts` path. Wily Roadmap emits a signed `stage_decomposed_local` event from `decompose-stage`; Wily Board stores the draft child phases, renders them as provisional rows, and clears them once durable `stage.yaml` data arrives.

**Tech Stack:** Python 3, Wily Roadmap CLI, FastAPI, SQLite, Jinja templates, pytest/unittest, signed HMAC live events.

---

## File Map

- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`: emit and report live draft topology events from `decompose-stage`.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`: CLI tests for draft event emission and missing-config warning.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`: add `live_drafts`.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`: store, list, render, and clear draft topology rows.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`: validate and store `stage_decomposed_local` payloads.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/sync/parser.py` or existing sync ingest module if needed: expose durable phase presence by stage for reconciliation.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`: merge draft phases into repo detail and dashboard context.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`: show draft topology follow-up item.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/repo_detail.html` or partials used by repo detail: render provisional child phase rows.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`: document live draft setup and troubleshooting.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`: API validation and storage tests.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`: storage, listing, and clearing tests.
- Modify `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`: dashboard and repo detail rendering tests.

## Task 1: Wily CLI Draft Event Contract

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/scripts/wily.py`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/test_wily_cli.py`

- [ ] **Step 1: Write failing CLI emission test**

Add a test that applies `decompose-stage --from-json` with Board config present and patches `emit_board_live_event`.

```python
def test_decompose_stage_emits_board_live_draft_when_configured(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        self.write_stage_roadmap(project)
        fixture = project / "decomposition.json"
        fixture.write_text(json.dumps([
            {"id": "21-1", "title": "Plan", "status": "pending", "depends_on": [], "task": "write plan"}
        ]), encoding="utf-8")
        emitted = []

        def record_event(root, item, event, live_status, note=""):
            emitted.append((item, event, live_status, note))

        with patch.dict(os.environ, {
            "WILY_BOARD_URL": "https://board.example",
            "WILY_BOARD_SECRET": "secret",
            "WILY_BOARD_REPO": "R-W-LAB/wily-roadmap",
            "WILY_BOARD_ACTOR": "airmang",
            "WILY_BOARD_AGENT": "codex",
        }), patch.object(wily, "emit_board_live_event", side_effect=record_event):
            result = wily.command_decompose_stage(project, ["s21", "--from-json", str(fixture)])

        self.assertEqual(result, 0)
        self.assertEqual(emitted[0][1], "stage_decomposed_local")
        self.assertEqual(emitted[0][2], "active")
        self.assertEqual(emitted[0][0]["draft_kind"], "stage_decomposition")
        self.assertEqual(emitted[0][0]["item_type"], "stage")
        self.assertEqual(emitted[0][0]["stage_id"], "s21")
        self.assertEqual(emitted[0][0]["phases"][0]["id"], "21-1")
```

- [ ] **Step 2: Run the failing test**

Run:

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest.test_decompose_stage_emits_board_live_draft_when_configured
```

Expected: FAIL because `decompose-stage` does not emit a draft event.

- [ ] **Step 3: Implement draft payload helper**

Add a helper near the existing live helpers.

```python
def live_draft_stage_decomposition_payload(root: Path, stage: Stage, phases: list[Phase]) -> Phase:
    stage_id = str(stage.get("id", ""))
    session_id = new_live_session_id()
    normalized_phases = []
    for phase in phases:
        normalized_phases.append({
            "id": str(phase.get("id", "")),
            "title": str(phase.get("title", "")),
            "status": str(phase.get("status", "pending")),
            "depends_on": [str(value) for value in phase.get("depends_on") or []],
            "owner": str(phase.get("owner", stage.get("owner", "")) or ""),
            "task": str(phase.get("task", "") or ""),
            "path": str(phase.get("path", "") or ""),
        })
    return {
        "id": stage_id,
        "item_type": "stage",
        "item_id": stage_id,
        "stage_id": stage_id,
        "draft_kind": "stage_decomposition",
        "session_id": session_id,
        "agent": live_agent(root),
        "phases": normalized_phases,
    }
```

- [ ] **Step 4: Emit from successful `decompose-stage` apply path**

After `write_decomposed_stage_phase_files(...)` and `save_roadmap(...)`, add:

```python
draft_payload = live_draft_stage_decomposition_payload(root, stage, phases)
if board_live_enabled(root):
    emit_board_live_event(root, draft_payload, "stage_decomposed_local", "active")
    print(f"Board live draft sent for {stage_id}: {len(phases)} phases")
else:
    print(
        "Board live draft not sent: missing WILY_BOARD_URL, WILY_BOARD_SECRET, WILY_BOARD_REPO, or WILY_BOARD_ACTOR.",
        file=sys.stderr,
    )
```

Apply this to both successful apply branches in `command_decompose_stage`.

- [ ] **Step 5: Add missing-config warning test**

```python
def test_decompose_stage_warns_when_board_live_config_missing(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        self.write_stage_roadmap(project)
        fixture = project / "decomposition.json"
        fixture.write_text(json.dumps([
            {"id": "21-1", "title": "Plan", "status": "pending"}
        ]), encoding="utf-8")

        with patch.dict(os.environ, {}, clear=True):
            result = self.run_wily(project, "decompose-stage", "s21", "--from-json", str(fixture))

        self.assertEqual(result.returncode, 0)
        self.assertIn("Board live draft not sent", result.stderr)
```

- [ ] **Step 6: Verify Wily CLI tests**

Run:

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest
```

Expected: `OK`.

## Task 2: Board Draft Storage

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/schema.sql`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] **Step 1: Write storage test**

```python
def test_upsert_live_draft_stage_decomposition(tmp_path):
    db = connect_db(tmp_path / "board.db")
    repo_id = upsert_repo(db, "R-W-LAB", "wily-roadmap", "main", "secret")
    payload = {
        "repo": "R-W-LAB/wily-roadmap",
        "draft_kind": "stage_decomposition",
        "item_type": "stage",
        "item_id": "s21",
        "stage_id": "s21",
        "actor": "airmang",
        "agent": "codex",
        "session_id": "draft-1",
        "phases": [{"id": "21-1", "title": "Plan", "status": "pending", "depends_on": []}],
    }

    upsert_live_draft(db, repo_id, payload)

    drafts = list_live_drafts(db, repo_id=repo_id, stage_id="s21")
    assert len(drafts) == 1
    assert drafts[0]["phases"][0]["id"] == "21-1"
```

- [ ] **Step 2: Add schema table**

Add:

```sql
CREATE TABLE IF NOT EXISTS live_drafts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
  draft_kind TEXT NOT NULL,
  item_type TEXT NOT NULL,
  item_id TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  actor TEXT NOT NULL,
  agent TEXT NOT NULL,
  session_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  cleared_at TEXT,
  UNIQUE(repo_id, draft_kind, stage_id, actor, session_id)
);
```

- [ ] **Step 3: Add repo helpers**

Implement `normalize_live_draft_payload`, `upsert_live_draft`, `list_live_drafts`, and `clear_live_drafts_for_stage`.

```python
def normalize_live_draft_payload(payload: dict[str, Any]) -> dict[str, Any]:
    phases = []
    for phase in payload.get("phases") or []:
        phases.append({
            "id": str(phase.get("id", "")),
            "title": str(phase.get("title", "")),
            "status": str(phase.get("status", "pending")),
            "depends_on": [str(value) for value in phase.get("depends_on") or []],
            "owner": str(phase.get("owner", "") or ""),
            "task": str(phase.get("task", "") or ""),
            "path": str(phase.get("path", "") or ""),
        })
    normalized = dict(payload)
    normalized["phases"] = phases
    return normalized
```

- [ ] **Step 4: Verify DB tests**

Run:

```sh
uv run pytest tests/test_db.py -q
```

Expected: all tests pass.

## Task 3: Board Live Event API

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`

- [ ] **Step 1: Write API accept/reject tests**

Add one test for valid `stage_decomposed_local`, one for empty `phases`, and one for phase missing `id`.

```python
def test_live_event_accepts_stage_decomposition_draft(client):
    payload = signed_payload({
        "repo": "R-W-LAB/wily-roadmap",
        "item_type": "stage",
        "item_id": "s21",
        "stage_id": "s21",
        "actor": "airmang",
        "agent": "codex",
        "event": "stage_decomposed_local",
        "live_status": "active",
        "draft_kind": "stage_decomposition",
        "session_id": "draft-1",
        "phases": [{"id": "21-1", "title": "Plan"}],
    })
    response = client.post("/api/live/events", content=payload.body, headers=payload.headers)
    assert response.status_code == 200
```

- [ ] **Step 2: Add draft validation**

Extend `validate_payload`:

```python
if payload.get("draft_kind") == "stage_decomposition":
    if payload.get("event") != "stage_decomposed_local":
        return "stage_decomposition requires stage_decomposed_local event"
    if payload.get("item_type") != "stage":
        return "stage_decomposition requires item_type stage"
    if payload.get("item_id") != payload.get("stage_id"):
        return "stage_decomposition item_id must match stage_id"
    phases = payload.get("phases")
    if not isinstance(phases, list) or not phases:
        return "stage_decomposition requires phases"
    for phase in phases:
        if not isinstance(phase, dict) or not phase.get("id") or not phase.get("title"):
            return "stage_decomposition phases require id and title"
```

- [ ] **Step 3: Store drafts in live endpoint**

Import `upsert_live_draft`. In `live_event`, after repo lookup:

```python
if payload.get("draft_kind") == "stage_decomposition":
    upsert_live_draft(request.app.state.db, repo_id, payload)
else:
    upsert_live_item(request.app.state.db, repo_id, payload)
```

Keep `upsert_live_session` only for payloads with `phase_id`.

- [ ] **Step 4: Verify live API tests**

Run:

```sh
uv run pytest tests/test_live_events.py -q
```

Expected: all tests pass.

## Task 4: Draft Rendering And Dashboard Follow-Up

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/routes.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/board.html`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/web/templates/repo_detail.html`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_web_routes.py`

- [ ] **Step 1: Write repo detail rendering test**

Create a repo with durable Stage `s21` and no durable child phases, store a live draft with `21-1`, then assert the repo detail page includes `21-1`, `local draft`, and `awaiting push`.

- [ ] **Step 2: Write durable-wins rendering test**

Create durable Stage `s21` with durable `21-1`, store a matching draft, then assert only durable row controls/status render and draft badge is omitted.

- [ ] **Step 3: Add route context merge**

In repo detail route:

```python
drafts_by_stage = list_live_drafts_by_stage(request.app.state.db, repo_id=repo_id)
for stage in stages:
    durable_phases = stage.get("phases") or []
    if durable_phases:
        stage["draft_phases"] = []
        continue
    draft = drafts_by_stage.get(stage["stage_id"])
    stage["draft_phases"] = draft["phases"] if draft else []
    stage["draft_actor"] = draft.get("actor") if draft else ""
    stage["draft_agent"] = draft.get("agent") if draft else ""
```

- [ ] **Step 4: Render provisional rows**

Add a visually distinct row for each `stage.draft_phases`:

```html
<div class="wb-phase-row is-draft">
  <span class="wb-phase-id">{{ phase.id }}</span>
  <span class="wb-phase-title">{{ phase.title }}</span>
  <span class="wb-chip">local draft</span>
  <span class="wb-chip">awaiting push</span>
  <p class="wb-phase-task">{{ phase.task }}</p>
</div>
```

- [ ] **Step 5: Add dashboard follow-up**

Expose draft follow-up rows from `routes.py` and render:

```text
S-21 decomposed locally - 7 draft phases awaiting push
```

- [ ] **Step 6: Verify web route tests**

Run:

```sh
uv run pytest tests/test_web_routes.py -q
```

Expected: all tests pass.

## Task 5: Durable Sync Reconciliation And Docs

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/docs/OPERATIONS.md`
- Test: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_db.py`

- [ ] **Step 1: Write draft clear test**

Store a draft for `s21`, then run the same replacement path used by GitHub sync with durable phases for `s21`. Assert `list_live_drafts(..., stage_id="s21")` returns no active drafts.

- [ ] **Step 2: Clear drafts during replace**

In the durable repository replace/import function, after inserting phases for a stage:

```python
if stage_phases:
    clear_live_drafts_for_stage(conn, repo_id, stage_id)
```

- [ ] **Step 3: Document troubleshooting**

Add to operations:

```md
If a local Stage decomposition does not appear on Board:

1. Run `python3 plugins/wily-roadmap/scripts/wily.py status` and confirm the child phases exist locally.
2. Confirm `.wily/local/board.json` or `~/.wily/board.json` contains `url`, `secret`, `repo`, and `actor`.
3. Re-run `decompose-stage` and look for `Board live draft sent`.
4. If durable sync has already run, the draft may have been cleared and replaced by durable rows.
```

- [ ] **Step 4: Full verification**

Run:

```sh
python3 -m unittest plugins.wily-roadmap.tests.test_wily_cli.WilyCliTest
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board && uv run pytest
```

Expected: Wily CLI tests pass and Board pytest suite passes.

## Commit Sequence

- [ ] Commit Wily CLI event contract: `feat(wily): emit live draft topology events`
- [ ] Commit Board storage/API: `feat(live): store topology draft events`
- [ ] Commit Board rendering/reconciliation: `feat(board): render live draft phase topology`
- [ ] Commit docs/tests polish: `docs(board): document live draft topology flow`

## Review Checklist

- [ ] `decompose-stage` still succeeds without Board config.
- [ ] Missing Board config is visible in CLI output.
- [ ] Draft rows are visually distinct from durable rows.
- [ ] Durable phases win over draft phases.
- [ ] GitHub sync clears matching drafts.
- [ ] No new remote write path is introduced.
