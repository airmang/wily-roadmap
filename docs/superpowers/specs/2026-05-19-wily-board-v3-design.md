# Wily Board v3 — Design Spec

- 작성일: 2026-05-19 (rev 3 — roadmap-bundled agent ownership)
- 작성: Wily 박사 + Claude (R-W-LAB)
- 출처 브레인스토밍: 본 세션
- 대체 대상: `docs/wily-board-plan.md`, `docs/wily-board-ui-spec.md` (v2 가정), `agent-handoffs/board-live-*`, `agent-handoffs/s21~s31 board-*`
- 구현 위치: 서버/UI는 별도 레포 `wily-board`, 공식 로컬 에이전트는 `wily-roadmap` 플러그인 번들.
- 본 레포(`wily-roadmap`)는 Board 서버/UI/DB 구현을 포함하지 않는다. 단, `.wily` 스키마와 CLI lifecycle을 가장 잘 아는 `wily-agent` 클라이언트/daemon은 `wily-roadmap` 플러그인이 소유한다.

## 0. Watch parity 원칙

**Wily Board는 `wily watch`가 표시하는 모든 정보를 같은 의미로 표시한다.** UI 시각언어는 web-native지만 정보 모델은 1:1 대응한다. 누락이 발견되면 board가 따라간다 (역방향 아님).

대응 표:

| watch 출력 | board 위치 |
|---|---|
| 진행률 바 (`done/total · %`) + 모드 라벨 | 카드 헤더(요약), 상세 페이지 상단 |
| status 그룹 (in_progress / blocked / ready / done) | 상세 페이지 status 그룹 리스트 |
| status glyph + task_id + status_label + actor_display + title | 카드 본문 + 상세 행 |
| 체크포인트 게이지 `[##-] 2/3 현재:verify` | 카드 본문 한 줄 + 상세 페이지 게이지 |
| 체크포인트 timeline (`[plan] > [design] > {verify}`) | 상세 페이지 cp timeline 영역(이벤트 단위 재생) |
| 의존 대기 텍스트 `대기 중: T01 (진행 중)` | 카드/상세 본문 |
| 차단 사유 `차단 사유: ...` | 카드/상세 본문 |
| 병렬 정보 `병렬: 레인 X · 우선순위 N · 필요 여력 N` | 카드 메타 줄 + 상세 패널 |
| 작업자 여력 `작업자 여력: wily 2/3` 또는 `여력 없음` | 카드 actor chip 보조 줄 + 상세 actor 패널 |
| scope 충돌 `충돌 가능: T02 (scope 겹침)` | 카드 경고 줄 + 상세 충돌 패널 |
| meta `[완료: …]` / `[시작: …]` / `[의존: …]` | 상세 task 펼침 영역 |
| 관찰된 commit 패널 (`git log --oneline -10`류) | 상세 페이지 활동 타임라인 |
| activity 패널 (actor 현재 task / 최근 완료) | 카드 actor chip + 상세 presence bar |

---

## 1. 제품 한 줄

로컬 우선 wily v3 프로젝트들의 진행 상황을 실시간으로 모아 보여주는 **읽기 전용 웹 보드**. R-W-LAB 두 사용자(Wily 박사, Right 박사)의 협업 가시성을 1차 목적으로 한다.

## 2. 성공 조건

- Wily 또는 Right이 자기 머신에서 `wily claim/done/replan` 등을 실행하면, 상대편 브라우저의 해당 프로젝트 카드가 15초 이내에 자동 갱신된다.
- 등록된 모든 로컬 wily v3 프로젝트는 한 번의 로그인으로 "내" 탭에서 보인다.
- `actors.yaml` 액터가 둘 이상이고 mode가 shared/collab인 프로젝트는 "협업" 탭에 자동으로 노출되며 상대의 현재 task와 활성 여부(presence)가 보인다.
- wily v3 CLI 동작은 board의 유·무와 무관하게 동일하다. Board 동기화는 `wily agent` daemon의 best-effort 경로이며, 일반 `wily claim/go/cp/done` 명령 성공 여부를 바꾸지 않는다.

## 3. Non-goals / 제약

- Task 상태 변경, replan, 생성 등 **쓰기 동작 없음**. 모든 변경은 wily CLI로만.
- Stage/Phase/Session 데이터 모델 없음. v3는 flat Task.
- 다중 org 지원 없음 (R-W-LAB org 멤버십 allowlist 한정).
- 네이티브 모바일 앱 없음 (반응형 웹만).
- Slack/Linear/이메일 등 외부 통합 없음.
- 외부 LLM 호출 없음.

## 4. 사용자와 시나리오

**사용자**
- Wily 박사 (사용자) — 본 레포 등 자기 머신의 wily 프로젝트들을 주로 다룬다.
- Right 박사 (협업자) — 일부 프로젝트를 함께 다룬다.
- 모두 R-W-LAB GitHub org 멤버.

**핵심 시나리오**
1. *나만의 대시보드*: 브라우저로 board 접속 → "개인" 탭 → 등록된 wily 프로젝트들이 카드로 나열, 현재 진행 중 task가 한눈에. Wily가 `wily go T03`을 치면 카드의 체크포인트 게이지가 즉시 움직인다.
2. *협업 가시성*: Right이 "T07 verify" 체크포인트를 마치면 Wily의 "협업" 탭 카드가 펄스 → 새로고침 없이 새 progress 반영. Right 칩에 LIVE 점등.
3. *상세 추적*: 카드 클릭 → 프로젝트 상세 페이지 → status 그룹 task list + 활동 타임라인 + presence bar.

## 5. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Wily Board Server (Azure VM, 재사용)            │
│   Caddy ──▶ FastAPI ──┬─▶ SQLite                                     │
│                       ├─▶ SSE broker  (per-session 채널)             │
│                       └─▶ GitHub OAuth (R-W-LAB org allowlist)       │
└─────────────────────────────────────────────────────────────────────┘
        ▲ HTTPS                                       │ SSE
        │ POST /agent/snapshot · /heartbeat           ▼
┌────────────┐                                ┌────────────┐
│  Wily 머신 │                                 │  브라우저  │
│ wily-agent │  fsnotify .wily/ ───▶ HTTP push │ htmx + SSE│
└─────┬──────┘                                └────────────┘
      │  (별개 프로세스, wily CLI와 무관)
      ▼
  wily CLI ──▶ .wily/{tasks.yaml, project.md, actors.yaml, tasks/T*/...}
                                ▲
                                │ 같은 git remote = 같은 project_id
                                ▼
                       Right 머신: wily-agent daemon
```

### 구성 요소

| 요소 | 책임 |
|---|---|
| **wily-agent (daemon)** | `wily-roadmap` 플러그인에 번들된 로컬 daemon. 등록된 `.wily` 레포의 task/actor/progress/result/project/git snapshot을 만들어 `/agent/snapshot`으로 POST하고, presence는 `/agent/heartbeat`로 보낸다. macOS 설치는 플러그인의 launchd 경로를 우선 사용한다. 파일 watch/debounce와 fallback push는 agent 내부 책임이며, Board 서버는 수신 계약만 책임진다. |
| **FastAPI 서버** | `/agent/*` 수집 API, `/sse` 브라우저 스트림, `/web/*` 페이지·파셜, `/auth/github/*` OAuth. SQLite가 단일 진실 원천. |
| **SSE 브로커** | 로그인 세션마다 채널. 사용자가 보는 프로젝트의 update·presence 이벤트만 전송. |
| **htmx 프론트** | 빌드 단계 없음. SSE 수신 시 영향받은 카드 파셜만 out-of-band swap. |

## 6. 데이터 모델 (SQLite)

```sql
CREATE TABLE users (
  github_id      INTEGER PRIMARY KEY,
  login          TEXT NOT NULL,
  display        TEXT,
  avatar_url     TEXT,
  allowlist_role TEXT NOT NULL,   -- 'wily' | 'right'
  created_at     TEXT NOT NULL
);

CREATE TABLE machines (
  id           TEXT PRIMARY KEY,    -- uuid
  user_id      INTEGER NOT NULL REFERENCES users(github_id),
  hostname     TEXT NOT NULL,
  token_hash   TEXT NOT NULL UNIQUE,
  created_at   TEXT NOT NULL,
  last_seen    TEXT
);

CREATE TABLE projects (
  id              TEXT PRIMARY KEY,   -- sha1(normalized remote_url)
  remote_url      TEXT NOT NULL,
  title           TEXT,
  mode_hint       TEXT,               -- 'solo' | 'shared' | 'collab'
  first_seen_at   TEXT NOT NULL,
  last_update_at  TEXT NOT NULL
);

CREATE TABLE project_machines (
  project_id    TEXT NOT NULL REFERENCES projects(id),
  machine_id    TEXT NOT NULL REFERENCES machines(id),
  local_path    TEXT NOT NULL,
  registered_at TEXT NOT NULL,
  PRIMARY KEY (project_id, machine_id)
);

CREATE TABLE task_snapshots (
  project_id    TEXT NOT NULL,
  machine_id    TEXT NOT NULL,
  snapshot_sha  TEXT NOT NULL,
  tasks_json    TEXT NOT NULL,
  project_md    TEXT,
  actors_json   TEXT,
  updated_at    TEXT NOT NULL,
  PRIMARY KEY (project_id, machine_id)
);

CREATE TABLE tasks (
  project_id              TEXT NOT NULL,
  task_id                 TEXT NOT NULL,
  title                   TEXT NOT NULL,
  intent                  TEXT,
  acceptance              TEXT,
  scope_json              TEXT,
  depends_on_json         TEXT,
  status                  TEXT NOT NULL,    -- ready|in_progress|blocked|done
  assignee                TEXT,
  actor                   TEXT,
  claim_sha               TEXT,
  claim_at                TEXT,
  done_at                 TEXT,
  blocker                 TEXT,
  parallel_lane           TEXT,             -- 병렬 메타 (T04)
  priority                INTEGER,          -- 병렬 메타 (T04)
  capacity_hint           INTEGER,          -- 병렬 메타 (T04)
  last_updated_by_machine TEXT NOT NULL,
  last_updated_at         TEXT NOT NULL,
  PRIMARY KEY (project_id, task_id)
);

CREATE TABLE task_progress (
  project_id    TEXT NOT NULL,
  task_id       TEXT NOT NULL,
  cp_done       INTEGER NOT NULL DEFAULT 0,
  cp_total      INTEGER NOT NULL DEFAULT 0,
  current_cp    TEXT,
  cp_names_json TEXT,                       -- 순서 보존된 cp 이름 리스트
  updated_at    TEXT NOT NULL,
  PRIMARY KEY (project_id, task_id)
);

-- 개별 cp 이벤트 (timeline 재생용 · custom-workflow `wily cp`가 만든 모든 start/done/note)
CREATE TABLE cp_events (
  project_id     TEXT NOT NULL,
  task_id        TEXT NOT NULL,
  ts             TEXT NOT NULL,
  actor          TEXT NOT NULL,
  cp             TEXT NOT NULL,
  event          TEXT NOT NULL,             -- 'start' | 'done' | 'note'
  note           TEXT,
  ingest_machine TEXT NOT NULL,
  PRIMARY KEY (project_id, task_id, ts, cp, event, actor)
);

-- 액터 메타 (capacity 포함). actors.yaml 동기 보관.
CREATE TABLE project_actors (
  project_id      TEXT NOT NULL,
  actor_id        TEXT NOT NULL,
  display         TEXT,
  capacity        INTEGER NOT NULL DEFAULT 1,
  git_emails_json TEXT,
  git_names_json  TEXT,
  PRIMARY KEY (project_id, actor_id)
);

-- 태스크 마무리 노트 (.wily/tasks/T*/result.md)
CREATE TABLE task_results (
  project_id  TEXT NOT NULL,
  task_id     TEXT NOT NULL,
  body        TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (project_id, task_id)
);

-- 관찰된 git commits (watch의 commit 패널과 동일 의미)
CREATE TABLE observed_commits (
  project_id  TEXT NOT NULL,
  sha         TEXT NOT NULL,
  author      TEXT,
  committed_at TEXT,
  subject     TEXT,
  guessed_task_id TEXT,                     -- guess_task_id 결과
  PRIMARY KEY (project_id, sha)
);

CREATE TABLE agent_events (
  id          INTEGER PRIMARY KEY,
  machine_id  TEXT NOT NULL,
  project_id  TEXT,
  type        TEXT NOT NULL,   -- 'snapshot' | 'heartbeat' | 'registered'
  payload     TEXT,
  created_at  TEXT NOT NULL
);

CREATE TABLE actor_presence (
  user_id            INTEGER NOT NULL,
  machine_id         TEXT NOT NULL,
  current_project_id TEXT,
  current_task_id    TEXT,
  last_seen          TEXT NOT NULL,
  PRIMARY KEY (user_id, machine_id)
);

CREATE TABLE oauth_sessions (
  sid        TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL,
  expires_at TEXT NOT NULL
);
```

### 머지 정책

- `task_snapshots`는 각 머신이 본 그대로 보관.
- `tasks` / `task_progress` / `task_results` / `project_actors`는 *마지막 push가 이긴다* (per-row `last_updated_at`/`updated_at` 기준). 같은 프로젝트를 양쪽이 push해도 git 동기화 이후 다음 push로 자연 수렴한다.
- `cp_events`와 `observed_commits`는 **append-only**. PRIMARY KEY가 자연 idempotency를 보장하므로 같은 이벤트는 중복 삽입되지 않는다 (UPSERT IGNORE).
- 충돌은 board가 해결하지 않는다. git이 해결한다.

## 7. 이벤트 흐름

```
1. agent  ──POST /agent/snapshot {project_id, sha, payload}──▶  server
2. server  diff against latest task_snapshots(project_id, machine_id)
           if sha equal → 200 noop
           else         → upsert + insert agent_event(snapshot) + broadcast SSE
3. server  ──SSE  {"type":"project_updated", "project_id":...}──▶  browser
4. browser ──htmx GET /web/projects/{id}/card  (oob swap)──▶  server
5. agent  ──POST /agent/heartbeat {project_id?, current_task_id?}──▶ server (5s)
6. server  upsert actor_presence; if status change → SSE {"type":"presence", ...}
```

### 탭 분류 규칙

| 탭 | 표시 대상 |
|---|---|
| 개인 | 현재 사용자의 `machines`가 등록한 모든 `projects` |
| 협업 | 위 중 `actors.yaml`의 액터 ≥ 2 AND `mode_hint ∈ {shared, collab}` |

### 프레전스 신호

- agent가 5초 주기로 `/agent/heartbeat` POST. 페이로드는 `{project_id?, current_task_id?}` (`current_task_id`는 그 시점의 in_progress task; 없으면 null).
- 서버는 `last_seen < 15s`인 actor를 "활성"으로 점등. UI는 카드의 actor chip에 펄스.
- presence 상태 변화도 SSE 이벤트(`type: "presence"`).

## 8. API

```
POST  /agent/register        (one-time code → machine token)
POST  /agent/snapshot        (token, project_id, snapshot_sha, payload)
POST  /agent/heartbeat       (token, project_id?, current_task_id?)
GET   /sse                   (인증 세션, 본인 채널)
GET   /web/                  (대시보드 셸)
GET   /web/projects/:id/card (htmx 파셜)
GET   /web/projects/:id      (상세 페이지)
GET   /auth/github/start
GET   /auth/github/callback
```

- 모든 `/agent/*`는 `Authorization: Bearer <machine-token>`. 토큰은 SHA-256 해시 비교, 머신 1개당 1 토큰.
- 모든 `/web/*`는 `oauth_sessions` 쿠키 기반 세션. allowlist 미충족이면 403.
- `/sse`는 EventSource 호환 형식. 인증 실패 시 401, 재연결 시 클라이언트 백오프 2/4/8초.

### 에이전트 페이로드 (계약)

```json
{
  "project_id": "<sha1(remote)>",
  "snapshot_sha": "<sha256 of canonical payload>",
  "remote_url": "git@github.com:R-W-LAB/wily-roadmap.git",
  "title": "wily-roadmap v3: ...",
  "mode_hint": "solo|shared|collab",
  "tasks": [
    {
      "id": "T04",
      "title": "...",
      "intent": "...",
      "acceptance": "...",
      "scope": ["..."],
      "depends_on": [],
      "status": "done",
      "assignee": "wily",
      "actor": "wily",
      "claim_sha": null,
      "claim_at": null,
      "done_at": "2026-05-18T14:55:08Z",
      "blocker": null,
      "parallel_lane": "ui",
      "priority": 1,
      "capacity_hint": 2
    }
  ],
  "actors": {
    "wily": {
      "display": "Wily 박사",
      "git_author_emails": ["..."],
      "git_author_names": [],
      "capacity": 2
    }
  },
  "task_progress": {
    "T03": {"done": 2, "total": 3, "current_cp": "verify", "cp_names": ["plan", "design", "verify"]}
  },
  "cp_events": {
    "T05": [
      {"ts": "2026-05-18T15:02:48Z", "actor": "wily", "cp": "execution-package", "event": "start"},
      {"ts": "2026-05-18T15:02:48Z", "actor": "wily", "cp": "execution-package", "event": "done"},
      {"ts": "2026-05-18T15:05:00Z", "actor": "wily", "cp": "red-tests", "event": "start"}
    ]
  },
  "task_results": {
    "T04": "# T04: ... — done\n\n- actor: wily\n- ..."
  },
  "observed_commits": [
    {"sha": "9151dc0", "author": "kokyuhyun", "committed_at": "2026-05-19T00:15:42+09:00",
     "subject": "T05: sync custom workflow checkpoints", "guessed_task_id": "T05"}
  ],
  "project_md": "raw markdown text",
  "client_version": "wily-agent/0.1.0",
  "captured_at": "2026-05-19T03:14:15Z"
}
```

`snapshot_sha`는 위 객체에서 `snapshot_sha`·`captured_at`을 제외한 canonical JSON의 SHA-256.

`mode_hint`는 에이전트가 `actors.yaml`로부터 계산한다 — 액터 1명이면 `solo`, 2명 이상이면 `shared`. 명시적 모드 필드를 향후 wily v3에 추가하면 그 값을 우선한다.

## 9. UI

### 페이지 셸

```
┌────────────────────────────────────────────────────────────────────────┐
│  Wily Board     [● connected]                Wily 박사 ▾   🌙 / ☀     │
├────────────────────────────────────────────────────────────────────────┤
│  [🧑 개인 6]   [🤝 협업 2 •]                                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [프로젝트 카드 그리드 — 1024+ 2열, 그 외 1열]                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- 상단바 좌측에 SSE 연결 상태 점, 우측에 사용자 메뉴와 다크모드 토글.
- 탭에 미확인 활동 점(•). 탭 진입 시 일괄 클리어.

### 프로젝트 카드 (개인 탭)

```
┌──────────────────────────────────────────────────────────┐
│ ●  wily-roadmap                            12분 전 활동  │
│ 진행 중 · T03 wily-replan 자연어 라우팅                  │
│ 시작 14:29 · 체크포인트 ▕██░▏ 2/3  현재 verify          │
│ 다음 대기: T04 · 차단 0                                  │
└──────────────────────────────────────────────────────────┘
```

상태별 변이:
- idle (`모두 완료` 또는 ready 무): 단일 줄, 옅은 톤
- ready만: `▶ 대기 T05 · 의존 충족`
- blocked: `✗ T02 차단 사유: 외부 API 응답 대기`

병렬·여력·충돌 메타가 있으면 카드 메타 줄에 압축 표기:

```
┌──────────────────────────────────────────────────────────┐
│ ●  wily-roadmap                            12분 전 활동  │
│ 진행 중 · T04 병렬 watch · 레인 ui · 우선순위 1           │
│ 체크포인트 ▕███▏ 5/5  완료 직전                          │
│ 작업자 여력 wily 2/2 (여력 없음)                          │
│ ⚠ 충돌 가능: T07 (scope 겹침)                            │
└──────────────────────────────────────────────────────────┘
```

— 카드는 4줄을 넘기지 않는다. 상세는 상세 페이지에서.

### 프로젝트 카드 (협업 탭)

```
┌──────────────────────────────────────────────────────────┐
│ ●  r-w-shared                  [Right ● LIVE]  8s 전     │
│ 진행 중 · T07 (Right 박사) 데이터 파이프 정리             │
│ 체크포인트 ▕█░░▏ 1/3 현재 design                         │
│ ─                                                         │
│ ◐ Wily는 1시간 전 T05 완료                               │
└──────────────────────────────────────────────────────────┘
```

- actor chip: LIVE면 초록 펄스, stale은 회색 + 마지막 본 시각
- 카드 하단에 *상대 액터의 최근 활동 한 줄* 항상 노출

### 프로젝트 상세

- **상단**: 프로젝트 메타 + presence bar + 진행률 바(`done/total · %`) + 모드 라벨(`단독/공유/협업`)
- **본문 좌(≥1024) / 위(small)**: status 그룹별 task list (`진행 중 → 차단 → 대기 → 완료`). 항목 펼치면:
  - intent / acceptance / scope / depends_on
  - 체크포인트 게이지 + cp_names 가로 timeline (완료=`[name]`, 현재=`{name}`, 대기=`name`)
  - 병렬 메타 (`레인 / 우선순위 / 필요 여력`)
  - 작업자 여력 + 충돌 경고
  - meta 줄 (`[완료: …]` / `[시작: …]` / `[의존: …]`)
  - `task_results.body` (result.md) 미리보기
- **우측(≥1024) / 아래(small)**: 활동 타임라인 — `cp_events` + `observed_commits` 시간순 머지. 항목 예:
  - `15:05 · wily · T05 · cp "red-tests" 시작`
  - `15:10 · wily · T05 · cp "implementation" 완료`
  - `00:15 · kokyuhyun · 9151dc0 · "T05: sync custom workflow checkpoints"`

### 병렬 lane 시각화 (옵션 토글)

상세 페이지 상단에 "병렬 lane 뷰" 토글 → 같은 `parallel_lane` 값의 task들을 가로 swim-lane으로 묶어 의존·충돌 관계를 화살표로 표시. 의존이 충돌하거나 작업자 여력이 부족한 lane은 빨간 테두리. lane이 정의되지 않으면 토글이 비활성. ASCII rail 시각언어는 사용하지 않고 HTML grid + 점/선으로 그린다.

### 시각 톤

- Pico.css 위에 얇은 사용자 레이어 (변수 기반)
- 상태색은 **dot 8px + 카드 좌측 2px 보더**에만. 배경은 사용하지 않는다.
- 라이트/다크 두 팔레트, `prefers-color-scheme` 자동 + 토글 localStorage 저장
- 모노스페이스는 task id (`T03`)와 sha (`fc95e4b`)만. 나머지는 시스템 sans.
- CLI watch의 ASCII rail/glyph는 시각언어로 가져오지 않는다 (web-native 반응형).

### 반응형

| 너비 | 동작 |
|---|---|
| ≥1024 | 카드 2열 그리드, 상세 2열 (task list / timeline) |
| 600–1024 | 카드 1열, 상세 1열, timeline 접힘 드로어 |
| <600 | 헤더 컴팩트, 카드 메타 압축 |

### 실시간 UX

- SSE 이벤트 수신 → 영향 카드 보더 0.6초 펄스 → htmx로 카드 파셜 swap
- 연결 끊김 → 상단바 점이 회색 + "재연결 중" 마이크로 텍스트, 2/4/8초 백오프
- 탭 비활성 동안 누적 변경은 페이지 타이틀에 `(N)` 카운트

### 빈/오류 상태

- 프로젝트 0개: "wily-agent register `<path>` 로 첫 프로젝트를 등록하세요" + 토큰 발급 버튼
- 에이전트 stale (last_seen > 30분): 카드 ⚠ + "에이전트 응답 없음"

## 10. 레포 구조

```
wily-board/
  pyproject.toml
  README.md
  app/
    main.py · config.py
    db/   schema.sql · migrations/ · repo.py
    auth/ github_oauth.py · sessions.py · allowlist.py
    api/  agent.py · sse.py
    web/  routes.py
          templates/  base.html · dashboard.html · project_card.html
                      project_detail.html · presence_chip.html
          static/     pico.min.css · app.css · app.js
    parsers/
      wily_state.py
  deploy/
    Caddyfile · wily-board.service · install.sh · backup.sh
  tests/
    test_parser.py · test_agent_routes.py · test_sse_broker.py
    test_auth_allowlist.py · test_merge_policy.py · test_card_render.py
  docs/
    deploy.md · agent-setup.md · data-model.md
```

- `wily-board`는 서버/API/cache/UI만 포함한다. 별도 `wily-board/agent` 패키지는 만들지 않는다.
- 공식 agent 구현은 `wily-roadmap/plugins/wily-roadmap/scripts/wily/agent/`에 둔다.
- `wily-roadmap` agent는 Board API 계약에 맞는 payload를 생성한다. Board는 payload를 검증/저장/렌더링하지만 `.wily` 파일 포맷 세부 지식을 agent보다 더 많이 갖지 않는다.

## 11. 배포

- 서버: 기존 Azure VM 그대로. `git pull && systemctl restart wily-board`. 첫 설치는 `deploy/install.sh`.
- 에이전트:
  - Codex plugin marketplace에서 `wily-roadmap` 플러그인을 설치/업데이트한다.
  - 웹에서 "Add machine" → 일회용 코드 → 머신에서 `wily agent login <code> --url <board-url> --actor <actor>`를 실행한다.
  - 등록할 프로젝트마다 해당 레포에서 `wily agent register --repo OWNER/REPO`를 실행한다.
  - macOS에서는 `wily agent install && wily agent start`가 launchd daemon을 설치/시작한다.
- 백업: SQLite 파일 매일 새벽 archive (v2 정책 유지).

## 12. v2에서 가져오는 것 / 버리는 것

| 분류 | v2에서 재사용 | v3에서 신규/변경 |
|---|---|---|
| HTTPS / 리버스프록시 | `deploy/Caddyfile` 거의 그대로 | rate-limit 영역 갱신 |
| 인증 | GitHub OAuth + `oauth_sessions` + Caddy rate-limit | allowlist를 R-W-LAB org 멤버십으로 |
| 스택 | FastAPI · Pico.css · htmx · Jinja2 · systemd · SQLite | SSE broker, agent 통신 |
| DB 스키마 | 폐기 (Stage/Phase 전부) | 본 문서 §6 스키마 신규 |
| 쓰기 모듈 | PR-writer · toggle 라우트 **삭제** | 없음 (읽기 전용) |
| Sync | GitHub webhook 핸들러는 호환 경로로 유지 가능 | 공식 신규 경로는 `wily-roadmap` 번들 agent → `/agent/*` |
| UI | base 템플릿, 다크모드 토글 | 본 문서 §9 카드/탭 신규 |

## 13. 테스트 전략

- 단위: parsers, snapshot diff, merge policy, auth allowlist, SSE broker fan-out
- 통합: in-memory SQLite + fake agent client → snapshot POST → SSE round-trip 어서션
- 컨트랙트: `tests/contracts/agent_v1.json`에 에이전트 페이로드 스키마 고정, 양쪽이 import
- 수동 verification: `docs/deploy.md`에 절차 체크리스트 (첫 등록부터 presence 확인까지)

## 14. 보안 노트

- 머신 토큰은 평문 미보관(SHA-256 해시), 한 번에 한 토큰
- OAuth state/nonce 검증, secure HTTP-only SameSite=Lax 세션 쿠키
- Caddy rate_limit: `/auth/*` 분당 10, `/agent/*` 분당 600, `/web/*` 분당 60 (IP 기준)
- SSE 채널은 인증된 사용자가 접근 권한 있는 프로젝트의 이벤트만 받도록 서버 측 필터링
- 에이전트가 보내는 file 본문(`project_md`)은 길이 상한(64KB) 적용

## 15. 마이그레이션 / 롤아웃

1. `wily-board` 레포의 v2 브랜치를 `legacy/v2`로 보존하고 main을 새로 비운다(이력 보존).
2. 서버 Azure VM에서 v2 service 정지 + DB 백업 + 새 서비스 배포.
3. 두 사용자가 각자 머신에서 `wily-agent` 설치·로그인·등록.
4. 7일간 양쪽이 daily 사용하며 verification 체크리스트 통과.
5. 통과 시 v3 정식 운영, `legacy/v2` 브랜치는 archive 라벨로 잠금.

## 16. Open questions (구현 단계에서 결정)

- *snapshot 크기 임계*: `project_md` 외 본문이 커질 때 페이로드 압축 여부 (gzip transfer-encoding 권장)
- *오프라인 에이전트의 백로그*: heartbeat 누락 동안의 snapshot은 단순 큐(local disk)에 보관 후 연결 복구 시 일괄 push
- *멀티 머신 사용자*: 한 사용자가 2대 머신에서 같은 프로젝트를 등록한 경우의 표시 — 일단 머신 단위로 합산, 충돌은 last-write-wins로 둔다
- *알림*: 초기 버전은 시각 펄스만. 푸시·이메일은 의도된 누락
- *cp_events 누적량*: 한 task가 수십 개 cp를 누적할 수 있으니 상세 timeline은 가상화 또는 페이지네이션 필요할 수 있음
- *observed_commits 수집*: 에이전트가 `git log --since=...`로 최근 7일 정도만 push. 그 이상은 board가 보관만 하고 UI는 최근 N개만 표시
