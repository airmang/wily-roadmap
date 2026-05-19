# S27 Wily Roadmap Stage/Phase Contract Refactor — Design Spec

- Date: 2026-05-17
- Status: ready-for-review
- Scope: Wily Roadmap plugin + Wily Board web app
- Source handoff: `agent-handoffs/s27-refactor-contract-requirements.md`
- Author flow: Wily 박사 ↔ Claude Opus 4.7 (브레인스토밍 합의)

## 1. 배경과 목표

Wily Roadmap을 누적 패치(stage-v1)에서 Stage→Phase 두 계층의 새 버전(`wily-roadmap-v2`)으로 재정의한다. Stage는 흐름/협업/집계 단위, Phase는 유일한 실행 단위로 분리하고, 외부 플러그인인 Custom Workflow Skillset을 기본 실행 흐름으로 둔다. Custom Workflow의 status board/checkpoint/progress 흐름은 Wily Phase 진행과 결합하여 `wily-watch`(CLI)와 Wily Board(웹)에서 동일한 projection 의미로 보여준다. 동시에 Wily Board의 IA를 전면 재설계하여 개인 작업(`/me`)과 협업(`/collab`)을 별도 진입점으로 분리한다.

S27의 산출물은 contract와 분해 plan이며, 본 spec은 plan-goal-runner 실행 패키지 작성 직전 단계의 합의 기록이다.

## 2. 이번 단계에서 확정된 결정

| 영역 | 결정 |
|---|---|
| Schema 이름 | `wily-roadmap-v2` |
| Phase 식별 정책 | `<stage-id>/<phase-id>` namespace 전면 도입 (내부 표현 `(stage_id, phase_id)` tuple) |
| Migration 명령 | `wily migrate-state` (top-level, 독립 명령) |
| v1 호환성 정책 | migration 직후 v2-only 강제. 미마이그레이션 repo는 명령 실패하고 `wily migrate-state` 안내 |
| Custom Workflow 테스트 정책 | 실제 plugin 설치 전제 integration test (별도 환경 표시) |
| Migration 검증 범위 | wily-roadmap repo + wily-board repo 두 곳 동시 검증 |
| Board IA | 전면 재설계 |
| Board 진입점 분리 | `/me`(개인 작업), `/collab`(협업) 별도 URL |
| Board 단일 repo 상세 | `/repos/[owner]/[name]` 단일 경로 공유, `visibility`에 따라 surface 강조점만 조정 |
| `/me` 상위 surface | 활성 Phase / next ready Phase / personal repos / blocked·needs_review |
| `/collab` 상위 surface | live activity / shared repos / blocked·review / 다음 협업 액션 |

다음 항목은 본 spec이 채택한 보조 결정이다.

- `wily migrate-state`는 dry-run, apply, prune-legacy(승인 옵션) 세 모드.
- 모든 마이그레이션은 `.wily/backups/<timestamp>-<schema>/`에 백업 생성.
- 모든 마이그레이션은 `.wily/migrations/<timestamp>-<schema>.md`(사람용)과 `.json`(머신용) 보고서 생성.
- Board는 `(repo, stage_id, phase_id)`를 canonical identity로 사용.
- Watch와 Board는 동일한 `RoadmapProjection` schema(`wily-roadmap-projection-v1`)를 소비.

## 3. 아키텍처 계약

### 3.1 Durable State Model

- `.wily/roadmap.yaml`은 `roadmap_schema: "wily-roadmap-v2"`와 `stages:` 만 포함.
- `.wily/stages/<stage-id>-<slug>/stage.yaml`은 child `phases:` 리스트 포함.
- `.wily/phases/**`는 migration 이후 legacy archive. 실행 경로는 읽지 않음.
- Phase 식별은 항상 `(stage_id, phase_id)` tuple. 단축 표기 `<stage-id>/<phase-id>` 만 허용.
- 기존 phase_id 단독 참조(세션, 핸드오프)는 migration이 namespace로 재맵핑.

`stage.yaml` 예:

```yaml
stage_id: "s27"
schema: "wily-roadmap-v2"
phases:
  - id: "p04"
    title: "Phase-only lifecycle commands"
    status: "pending"
    depends_on: ["s27/p02"]
    owner: "codex"
    runner: "custom-workflow"
    path: "stages/s27-wily-roadmap-large-refactor/phases/p04-lifecycle"
```

### 3.2 Stage Status 집계 규칙

Stage 상태는 child Phase 상태에서 매번 재계산하며, 호환을 위해 정규화된 `status`를 stage.yaml에 기록할 수 있다.

- `superseded`: Stage-level 명시 종결.
- `done`: 모든 non-superseded child Phase가 `done`.
- `in_progress`: child Phase 중 하나라도 `in_progress`.
- `blocked`: in_progress 없음 + blocked 하나 이상.
- `needs_review`: in_progress/blocked 없음 + needs_review 하나 이상.
- `ready`: 의존성 done + 실행 가능한 child Phase 하나 이상.
- `pending`: 그 외.
- child Phase가 0인 비-superseded Stage는 실행 명령 거부 + `wily decompose-stage` 또는 `wily migrate-state` 안내.

### 3.3 Execution Contract

Phase-only 명령(모두 `<stage-id>/<phase-id>` 또는 동등한 tuple 인자):

- `wily start`, `wily run`, `wily complete`, `wily block`, `wily retry`, `wily release`
- `wily live-heartbeat`, `wily live-worked`
- `wily checkpoint-sync ... --status-board <path>`

Stage 친화 명령:

- `wily status`, `wily next`, `wily watch`
- `wily board sync-local <stage-id>`
- `wily decompose-stage <stage-id>`
- `wily migrate-state ...`

명령 규칙:

- Stage id를 Phase-only 명령에 넘기면 오류. 오류 메시지에는 가장 가까운 ready Phase의 namespace를 함께 출력.
- 단축 표기 허용: `wily run s27/p04`. 내부적으로 `(stage_id="s27", phase_id="p04")`로 정규화.
- 검증용 `--dry-run`은 runner request와 Phase resolve만 확인하고 durable state/session을 변경하지 않음.
- Phase가 없는 Stage에 실행 명령이 들어오면 `wily migrate-state` 또는 `wily decompose-stage` 안내.

### 3.4 Runner Adapter Contract

기본 adapter는 `custom-workflow`(엔진 `custom-workflow-skillset`, 기본 skill `plan-goal-runner`).

Adapter가 하는 일:

- `(stage_id, phase_id)` tuple로 Phase context 해석.
- Wily Phase 세션을 생성/연결하고 request·result 산출물 경로 결정.
- Custom Workflow의 status/progress/verification/result artifact 위치를 알고 있어야 함.
- status board checkpoint를 Wily checkpoint overlay 모양으로 파싱.

Adapter가 하지 않는 일:

- Custom Workflow plugin 파일 수정 금지.
- Custom Workflow checkpoint 만으로 Wily Phase를 `done` 처리 금지.
- Custom Workflow 내부에 Wily checkpoint id를 강제하지 않음.

### 3.5 Checkpoint Overlay Contract

Custom Workflow checkpoint는 Phase 아래 non-durable child row.

```json
{
  "source": "custom-workflow",
  "status_board": "agent-handoffs/s27-p07-status.md",
  "state": "RUNNING",
  "progress": {"done": 2, "total": 6, "percent": 33},
  "current": {"id": "CP03", "title": "...", "status": "RUNNING"},
  "next": {"id": "CP04", "title": "...", "status": "PENDING"},
  "rows": [
    {"id": "CP01", "title": "...", "status": "DONE", "owner": "root"}
  ],
  "current_action": "...",
  "blocker": "",
  "verification": {"status": "PASS", "evidence": "pytest target suite"}
}
```

projection 규칙:

- checkpoint row는 항상 owning Phase 아래에 렌더링.
- `is_durable: false`. Phase 상태에 영향을 주지 않음.
- Watch는 compact current/progress, Board는 expanded rows. 시각 상세는 p11(repo detail)에서 확정.

### 3.6 Shared Projection Contract

`wily-roadmap-projection-v1` JSON schema는 watch/status/Board emitter가 모두 소비한다.

- 입력: durable yaml + sessions + local live overlay + Custom Workflow status board + Board last emit cache.
- 출력: `repo`, `generated_at`, `stages[].phases[].checkpoint_overlay`, `live_overlays`, `warnings`.
- canonical identity: `(repo, stage_id, phase_id)`.
- Board는 로컬 파일시스템 접근 없이 imported `.wily` + signed live event로 동일 semantic 재구성 가능해야 함.

### 3.7 Wily Board Read-only Contract

Board가 하는 것:

- Stage list/map(aggregate progress) + child Phase list + checkpoint child row + live activity + risk/attention/next 표시.
- Multi-repo overview, `/me`(개인), `/collab`(협업) 별도 surface.

Board가 하지 않는 것:

- `.wily` 직접 쓰기 금지.
- UI에서 Phase 상태 변경 금지(S27 범위).
- Custom Workflow 수정 요구 금지.

## 4. Wily Board IA / UI 재설계

### 4.1 Route 구조

```
/                       → /me로 redirect (로그인 정책에 따름)
/me                     → 개인 작업 대시보드
/collab                 → 협업 대시보드
/repos/[owner]/[name]   → 단일 repo 상세 (Stage/Phase/checkpoint 전체)
/repos/[owner]/[name]/stages/[stage_id]              → Stage anchor
/repos/[owner]/[name]/stages/[stage_id]/phases/[phase_id]  → Phase anchor
/login (또는 동일 surface) → 인증 필요 시
```

`/repos/.../stages/<stage>/phases/<phase>`가 namespace 라우트의 정식 형태. 단일 repo 상세 페이지는 `visibility=personal|shared`에 따라 widget 강조점만 다르게 렌더(컴포넌트는 공유).

### 4.2 Surface 사양 (확정)

#### `/me` — 개인 작업 대시보드

1. **Active Phase 카드**: 현재 진행 중인 Phase의 owner=me, current checkpoint, progress%, current action, next checkpoint, blocker. 카드 클릭 → 단일 repo 상세.
2. **Next Ready Phase**: `wily next` 결과 + 짧은 이유(의존성 done, runner=ready). 1~3개 후보.
3. **Personal repos 그리드**: visibility=personal repos. 카드당 progress%, 마지막 활동 시간, 현재 Phase 요약. multi-repo 빠른 픽업용.
4. **Blocked / needs_review 알림**: 내가 owner인 막힌 Phase 또는 review 대기 Phase.

#### `/collab` — 협업 대시보드

1. **Live Activity Strip**: 현재 진행 중인 모든 shared session. owner, freshness 색, current checkpoint 표시. heartbeat가 끊긴 항목은 stale 마킹.
2. **Shared repos 그리드**: visibility=shared repos. 카드당 active Phase, owner, last heartbeat.
3. **Blocked / Review Queue**: handoff/checkpoint 단위로 막혀 있거나 리뷰 대기 중인 항목.
4. **Next 협업 Action**: 다른 owner의 픽업이 필요한 ready Phase 목록.

#### `/repos/[owner]/[name]` — 단일 repo 상세

- 헤더: repo 이름, visibility 칩, 진행률 요약, 마지막 sync 시간.
- Stage map: Stage 목록과 의존성/집계 상태.
- Stage 선택 시 child Phase 리스트.
- Phase 선택 시: Phase 상세 + checkpoint overlay rows + live session 정보 + 관련 핸드오프 링크.
- `visibility=shared`이면 owner/freshness/Live 컬럼을 더 키움. `visibility=personal`이면 진행/다음일/Next ready를 키움.

### 4.3 Chrome / 네비게이션

- 최상단: R-W-LAB 로고, repo 검색, `/me ↔ /collab` 토글.
- 사이드 nav(데스크탑): repos(personal|shared 필터), Risk view, Activity timeline.
- 우측 상단: sync 상태, login(필요 시), theme toggle.
- 모바일: 사이드 nav는 drawer.

### 4.4 인증 / 가시성

- 기본 정책: login 필요. 미로그인은 `/me`/`/collab` 대신 로그인 surface.
- personal repos: `visible_to == 본인`만 노출.
- shared repos: R-W-LAB 멤버 누구나 열람.
- 단일 repo 상세 페이지도 동일 visibility 룰을 그대로 적용.

### 4.5 디자인 톤

메모리상 가이드: **Wily Board(웹)는 watch(CLI)의 ASCII rail/glyph 시각언어를 옮기지 말고 웹 네이티브 반응형으로 설계**. 따라서:

- 카드 + 그리드 + chip + tag 위주의 웹 네이티브 layout.
- ASCII rail/glyph 표현은 watch 전용 시각언어로 분리.
- 반응형: 모바일에서 카드 1열, 데스크탑에서 그리드.

## 5. Migration 계약 (`wily migrate-state`)

### 5.1 모드

- `--dry-run`: 분석 + 보고서만.
- `--apply`: 실제 변환 적용(백업/보고서/검증 포함).
- `--prune-legacy`: `.wily/phases/**` 같은 legacy 디렉토리 제거. 승인 옵션.

### 5.2 단계

1. Preflight — schema 감지, top-level `phases:`, Stage-local `stage.yaml`, 세션 참조, 중복 phase_id, dirty git worktree 경고.
2. Backup — `.wily/backups/<timestamp>-wily-roadmap-v2/`에 roadmap/stage/legacy phase/세션 메타 복사. secret/local config는 복사하지 않음.
3. Transform
   - 비-superseded Stage에 Phase 0개면 직접 Stage 작업을 단일 Phase로 변환(Phase 제목은 Stage 제목 유지 + suffix policy는 p01에서 확정).
   - top-level legacy `phases:`를 해당 Stage의 `stage.yaml`로 이전.
   - phase_id 충돌 시 prefix 부여 + 매핑 기록.
   - 세션/핸드오프의 phase_id 단독 참조를 `<stage_id>/<phase_id>`로 재맵핑(원본은 backup에 남김).
   - `roadmap_schema`를 `wily-roadmap-v2`로 갱신, top-level `phases:` 제거.
4. Report — `.wily/migrations/<timestamp>-wily-roadmap-v2.md` + `.json` 생성. 변경 파일, id 매핑, 경고, 후속 명령 포함.
5. Validate — `wily status`, `wily next`, `wily watch --once --ui ascii`, 그리고 임의 Phase에 대해 `wily run --dry-run` 가능 여부 확인. 실패하면 backup으로부터 자동 rollback 안내.

### 5.3 정책

- migration 후 commands는 `.wily/phases/**`를 읽지 않음(미마이그레이션 repo는 `wily migrate-state` 안내).
- destructive removal은 `--prune-legacy`로만 옵트인.

## 6. Phase 분해 (13 Phases)

의존성: `p01 → p02 → (p03, p04) → p05 → p06 → p07 → p08 → p09 → (p10, p11) → p12 → p13`. 병렬화 가능: `p03 || p04`, `p10 || p11`.

| Phase | Goal | 주요 write scope | 의존 |
|---|---|---|---|
| s27/p01 | Contract Freeze + Fixtures (이 spec 확정, fixture 세트) | `agent-handoffs/`, `docs/superpowers/specs/`, `plugins/wily-roadmap/skills/wily-workflow/references/` | — |
| s27/p02 | State Schema/Parser `wily-roadmap-v2` (namespace tuple, aggregate, v1 read 제거) | `plugins/wily-roadmap/scripts/wily_state_summary.py`, 신규 state 모듈, `tests/test_wily_state_summary.py` | p01 |
| s27/p03 | `wily migrate-state` (dry-run/apply/prune-legacy, namespace 재맵핑) | `scripts/wily.py`, migration helper, `tests/test_wily_cli.py` | p02 |
| s27/p04 | Phase-only Lifecycle Commands (tuple resolve, Stage id rejection) | `scripts/wily.py`, lifecycle skills, CLI 테스트 | p02 |
| s27/p05 | Runner Adapter Registry + Custom Workflow integration test | `scripts/wily_runner.py`, adapter 모듈, `skills/wily-run/SKILL.md`, runner tests | p04 |
| s27/p06 | Projection Core `wily-roadmap-projection-v1` (watch/status consumer 전환) | projection helper 모듈, `scripts/wily_watch_ui.py`, `scripts/wily.py`, watch/status tests | p02, p04, p05 |
| s27/p07 | Checkpoint Overlay + Board Event Contract (tuple payload) | `scripts/wily.py`, board reflection reference, CLI/watch tests | p05, p06 |
| s27/p08 | Wily Board Backend (api/db/live, schema namespace 수용) | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/*.sql`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/db/repo.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/live/events.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/app/api/routes.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_live_events.py`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests/test_api_routes.py` | p07 |
| s27/p09 | Wily Board IA Chrome (`/me`, `/collab` routing + 공통 chrome + 인증/visibility) | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/me/`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/collab/`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/page.tsx`, header/sidebar 컴포넌트, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/types.ts` | p08 |
| s27/p10 | Wily Board Surfaces — `/me` + `/collab` widgets | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/me/page.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/collab/page.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/active-phase-card.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-grid.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-strip.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/risk-queue.tsx` | p08, p09 |
| s27/p11 | Wily Board Repo Detail (Stage/Phase/Checkpoint UI 리팩토링) | `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/page.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`, `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/checkpoint-rows.tsx` | p08, p09 |
| s27/p12 | Skills/Commands/Docs/Cache Sync | `plugins/wily-roadmap/skills/**`, `commands/**`, `README.md`, command skill tests | p03, p05, p07 |
| s27/p13 | E2E Migration + Dashboard Verification (두 repo 동시) | tests + verification handoffs (no prod deploy) | 모든 이전 phase |

각 Phase는 plan-goal-runner에 넘길 때 verification block 포함:

- pytest 대상 모듈 명시
- `py_compile` 대상 파일 명시
- CLI 스모크 명령(`wily status`, `wily next`, `wily watch --once --ui ascii`) 명시
- Board phase는 추가로 `uv run pytest`, `npm run lint`, `npm run build`

## 7. 테스트 전략

- 모든 Phase는 진입 전 baseline 테스트(`pytest` 그린, `npm run build` 그린) 확인.
- p02·p03·p04·p06·p07: TDD 기본. fixture부터 작성.
- p05: Custom Workflow Skillset이 실제 설치된 환경에서 integration test. CI는 별도 마커로 분리(`pytest -m integration`).
- p08·p09·p10·p11: API 테스트는 TDD, 프론트는 컴포넌트 단위 + frontend snapshot 또는 screenshot.
- p13: dry-run은 wily-roadmap, wily-board 두 repo에서 수행하고, apply/run 검증은 먼저 disposable fixture copy에서 수행한다. 실제 repo apply는 별도 사용자 승인 후 결과 보고서를 archive.

## 8. 위험과 완화

| 위험 | 영향 | 완화 |
|---|---|---|
| namespace 전면 도입으로 기존 핸드오프/세션 식별자 깨짐 | 마이그레이션 후 추적 곤란 | p03 migration이 단독 phase_id 참조를 재맵핑하고 매핑 보고서 유지 |
| v2-only 강제로 미마이그레이션 repo가 즉시 실패 | 사용자 작업 일시 중단 | 오류 메시지에 `wily migrate-state --dry-run` 안내 + 한 줄 복구법 |
| 실제 Custom Workflow plugin 설치 의존성 | 테스트 환경 까다로움 | integration test는 별도 마커, mock 기반 단위 테스트 병행 |
| Board IA 전면 재설계로 UI 회귀 | 사용자 학습 비용 | p09에서 기존 라우트는 `/me`로 redirect, p13에서 시각 스모크 포함 |
| Wily Board는 별도 repo이므로 PR/배포 동시화 어려움 | 두 repo 합산 검증 시점 어긋남 | p13에서 두 repo dry-run + fixture apply를 먼저 맞추고, 실제 repo migration/release tag는 승인 후 진행 |
| migration 백업이 disk 부담 | 사용자 환경 다양 | 기본 backup은 압축 옵션, 보고서에 백업 위치/크기 명시 |

## 9. 남은 Open Question (실행 시점 결정)

- migration이 직접 Stage를 변환할 때 Phase 제목 정책(원본 Stage 제목 그대로 vs `"<Stage title> implementation"` 등 suffix). p01에서 fixture와 함께 확정.
- `/me` 메인 진입을 항상 redirect로 둘지, login 후 마지막으로 본 surface 기억할지. p09에서 결정.
- Board의 multi-repo 그리드에서 stale 임계값(예: 24h heartbeat 없음 = stale). p10에서 결정.
- `wily migrate-state`의 backup 보존 정책(영구 vs N일). p03에서 결정, 기본은 사용자 수동 삭제.

## 9.1 S27 실행 기본값

S27 CP01에서 다음 기본값을 확정한다.

- 직접 Stage를 단일 Phase로 변환할 때 Phase 제목은 원본 Stage 제목을 그대로 보존한다. suffix를 자동으로 붙이지 않는다.
- Board root(`/`)는 `/me`로 deterministic redirect한다. 마지막 surface 기억은 S27 범위 밖의 후속 개선으로 둔다.
- Board live activity stale 임계값은 heartbeat 기준 15분이다. repo card는 오래된 활동 context를 보여줄 수 있지만 live chip은 stale로 표시한다.
- migration backup은 기본적으로 영구 보존한다. 자동 삭제 정책은 두지 않고, cleanup은 별도 승인-first 절차로 처리한다.

이 결정은 `plugins/wily-roadmap/skills/wily-workflow/references/stage-phase-v2-contract.md`와 fixture 세트에 반영된다.

## 10. Out of Scope (S27 외)

- Custom Workflow Skillset 내부 변경.
- Board에 durable mutation UI 추가.
- 새 hooks, MCP server, app integration.
- 완료된 S01~S24 git history 재작성.
- production deploy, remote push, GitHub mutation(승인 없이는 불가).
- Codex 외 다른 에이전트 어댑터.

## 11. Verification Plan (S27 완료 기준)

Wily Roadmap repo:

```bash
python3 -m py_compile plugins/wily-roadmap/scripts/wily.py plugins/wily-roadmap/scripts/wily_runner.py plugins/wily-roadmap/scripts/wily_state_summary.py plugins/wily-roadmap/scripts/wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_state_summary.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_cli.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_watch_ui.py
python3 -m pytest plugins/wily-roadmap/tests/test_wily_command_skills.py
python3 -m pytest -m integration plugins/wily-roadmap/tests/   # Custom Workflow 설치 환경
./plugins/wily-roadmap/wily status
./plugins/wily-roadmap/wily next
./plugins/wily-roadmap/wily watch --once --ui ascii
./plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run

# Apply/run verification happens against a disposable fixture copy first.
tmp="$(mktemp -d)"
cp -R plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy "$tmp/project"
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --apply)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily status)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily next)
(cd "$tmp/project" && /Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily run s27/p04 --dry-run)
```

Wily Board repo:

```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
cd frontend && npm run lint && npm run build
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/wily migrate-state --to wily-roadmap-v2 --dry-run
```

수동 스모크:

- 새 합성 fixture(`v1 only`, `mixed legacy`, `already v2`)에서 migration이 의도된 변형을 함.
- `/me`와 `/collab`이 visibility에 따라 다른 surface를 그림.
- 단일 repo 상세에서 checkpoint child row가 owning Phase 아래 보임.
- Stage id를 `wily run`에 넘기면 namespace 안내와 함께 실패.
- 두 repo에서 동일하게 migration을 적용한 뒤 Wily Board가 두 repo를 동시에 정상 표시.

## 12. Self-Review (브레인스토밍 종료 시점)

- placeholder 없음: TBD/TODO 없이 모든 결정에 대안 또는 확정 표시.
- 내부 일관성: namespace 정책과 URL/명령/이벤트 payload가 같은 모델.
- 범위 점검: 13 Phase로 분해 가능. p13 이후 추가 정리는 별도 Stage.
- 모호성 제거: 남은 Open Question은 실행 시점 결정 항목으로 분리.

## 13. 다음 단계

1. 사용자(Wily 박사)가 본 spec을 검토.
2. 수정 사항이 있으면 본 문서를 갱신.
3. 승인 후 `superpowers:writing-plans` skill로 전환하여 phase-by-phase 실행 plan 작성.
4. 그 결과를 `custom-workflow-skillset:plan-goal-runner`에 넘겨 실제 실행 패키지로 변환.
