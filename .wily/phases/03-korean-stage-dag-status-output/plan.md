# Korean Stage-Based DAG Status Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `wily-status` print Korean user-facing status text and replace the flat English phase list with a compact stage-based DAG summary.

**Architecture:** Keep `.wily/roadmap.yaml` machine values in English and translate only rendered status output. Add small formatting helpers in `scripts/wily_state_summary.py`: Korean status labels, dependency/parallel labels, stage ranking for DAG display, and phase flow rendering. Preserve the existing executable-phase logic from Phase 02.

**Tech Stack:** Python standard library, `unittest`, local Wily helper scripts.

---

### Task 1: Add Failing Tests for Korean Summary Labels

**Files:**
- Modify: `tests/test_wily_state_summary.py`

- [ ] **Step 1: Update `test_summarizes_ready_and_blocked_phases` expected output**

Replace English output assertions with Korean user-facing labels while keeping roadmap markers in the fixture English:

```python
self.assertIn("상태 디렉터리: .wily", output)
self.assertIn("로드맵 버전: 1", output)
self.assertIn("진행: 완료 1, 실행 가능 1, 진행 중 0, 차단 1, 대체됨 0", output)
self.assertIn("다음 단계: 02 - Core engine", output)
self.assertIn("Phase 흐름:", output)
self.assertIn("Stage 1:", output)
self.assertIn("  - 01 [완료] Audit current implementation", output)
self.assertIn("Stage 2:", output)
self.assertIn("  - 02 [실행 가능] Core engine", output)
self.assertIn("Stage 3:", output)
self.assertIn("  - 03 [차단] Packaging", output)
self.assertIn("실행 가능 단계:", output)
self.assertIn("  - 02 Core engine", output)
self.assertIn("차단된 단계:", output)
self.assertIn("  - 03 Packaging (의존: 02)", output)
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run:

```bash
python3 -m unittest tests.test_wily_state_summary.WilyStateSummaryTest.test_summarizes_ready_and_blocked_phases
```

Expected: FAIL because the current renderer still prints English labels and `All phases:`.

### Task 2: Add Failing Tests for Stage Grouping and Multi-Dependency Annotation

**Files:**
- Modify: `tests/test_wily_state_summary.py`

- [ ] **Step 1: Add `test_groups_parallel_phases_by_dependency_stage`**

Use a roadmap where phases `04-1` and `04-2` both depend on `03`, share `parallel_group: "04"`, and render under the same stage:

```python
self.assertIn("Stage 4:", output)
self.assertIn("  - 04-1 [대기] Improve init roadmap authoring (의존: 03, 병렬: 04)", output)
self.assertIn("  - 04-2 [대기] Harden lifecycle status CLI (의존: 03, 병렬: 04)", output)
```

- [ ] **Step 2: Add `test_shows_multi_dependency_without_tree_edge`**

Use a roadmap where phase `05` depends on `04-1` and `04-2`, then assert it renders with an explicit dependency annotation:

```python
self.assertIn("Stage 5:", output)
self.assertIn("  - 05 [대기] Plugin discovery and release polish (의존: 04-1, 04-2, 병렬: 없음)", output)
```

- [ ] **Step 3: Run both new tests and confirm they fail**

Run:

```bash
python3 -m unittest tests.test_wily_state_summary.WilyStateSummaryTest.test_groups_parallel_phases_by_dependency_stage tests.test_wily_state_summary.WilyStateSummaryTest.test_shows_multi_dependency_without_tree_edge
```

Expected: FAIL because stage rendering and Korean dependency labels do not exist yet.

### Task 3: Implement Korean Stage-Based Rendering

**Files:**
- Modify: `scripts/wily_state_summary.py`

- [ ] **Step 1: Add Korean label helpers**

Add a status map and update dependency/parallel labels:

```python
STATUS_LABELS = {
    "pending": "대기",
    "ready": "준비됨",
    "in_progress": "진행 중",
    "needs_review": "검토 필요",
    "done": "완료",
    "blocked": "차단",
    "superseded": "대체됨",
}
```

Use `"실행 가능"` for phases included in the computed `ready` list so pending phases whose dependencies are done are rendered as executable in user-facing output.

- [ ] **Step 2: Add deterministic stage ranking**

Implement a helper that assigns each phase to `1 + max(dependency stage)` and falls back to stage 1 when a dependency is missing from the current roadmap. Keep ordering stable by preserving roadmap order inside each stage.

- [ ] **Step 3: Replace `All phases:` rendering**

Render:

```text
Phase 흐름:
Stage 1:
  - 01 [완료] ...
Stage 2:
  - 02 [실행 가능] ...
```

Each phase line should include `(의존: ..., 병렬: ...)`; dependencies with more than one item must remain explicit on the same line rather than pretending there is a single tree parent.

- [ ] **Step 4: Translate remaining user-facing sections**

Translate summary labels:

```text
저장소:
상태 디렉터리:
Git:
로드맵 버전:
목표:
진행:
다음 단계:
실행 가능 단계:
차단된 단계:
대체:
대체된 단계:
로드맵: 없음
```

Do not translate stored status values in `.wily/roadmap.yaml`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_wily_state_summary
```

Expected: PASS.

### Task 4: Update Skill Documentation

**Files:**
- Modify: `skills/wily-status/SKILL.md`
- Modify: `skills/wily-workflow/SKILL.md`
- Modify: `skills/wily-workflow/references/planning-style.md`

- [ ] **Step 1: Update status report wording**

State that `$wily-status` renders Korean user-facing output, uses a stage-based `Phase 흐름:` section, and keeps roadmap status markers English in files.

- [ ] **Step 2: Update workflow/planning references**

Mention that status summaries group phases by dependency stage and use explicit `의존:` annotations for multi-dependency phases.

### Task 5: Verify Phase Completion

**Files:**
- Modify: `.wily/sessions/2026-05-11-125059-phase-03-attempt-1/verification.md`
- Modify: `.wily/sessions/2026-05-11-125059-phase-03-attempt-1/changed-files.md`
- Modify: `.wily/sessions/2026-05-11-125059-phase-03-attempt-1/result.md`

- [ ] **Step 1: Run required verification**

Run:

```bash
python3 -m unittest tests.test_wily_state_summary
python3 -m unittest discover
python3 -m py_compile scripts/wily.py scripts/wily_state_summary.py
python3 scripts/wily.py status
```

Expected: all tests and compile checks pass; manual status output uses Korean headings and stage-based DAG layout.

- [ ] **Step 2: Record session evidence**

Update the session files with verification commands, changed files, and a concise result summary. Do not mark the phase complete; `$wily-complete` is a separate explicit command after review.
