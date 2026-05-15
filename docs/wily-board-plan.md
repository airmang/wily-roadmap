# Wily Board — 공동 프로젝트 현황판 계획서

본인(`@kokyuhyun`) + 라이트, 둘이서 운영하는 여러 Wily 레포의 상태를 한 곳에서 보고 가벼운 쓰기 액션까지 할 수 있는 *별도 UI 대시보드*. 본인 보유 Azure 박스에 호스팅, 모바일 브라우저에서 즐겨찾기 한 번으로 접근.

이 문서는 Codex 등 외부 에이전트에게 그대로 던질 수 있도록 *결정·미결정·담당 분리*까지 정리한 핸드오프 계획서다.

---

## 1. 목적과 비기능 요건

- 여러 레포의 Wily Stage/Phase 상태를 *한 화면*에서 본다(소유자별·상태별 필터, 칸반/리스트).
- 모바일 브라우저에서 라이트도 접근·간단한 쓰기 액션이 가능하다.
- **토큰 비용 0에 가깝게**: LLM이 대시보드 운영 루프에 끼지 않는다. 에이전트는 *기존 Wily skill 안에서* 대시보드 API를 호출하는 정도만.
- Wily의 *단일 출처(SoT)*는 각 레포의 `.wily/` 파일. 대시보드는 *조회 캐시 + 쓰기는 PR로 위임*.
- Azure 박스는 Standard B2ats v2 (2 vCPU, **1 GiB RAM**, Ubuntu 24.04). 메모리 빠듯 → 가벼운 스택 강제.

---

## 2. 합의된 원칙

| 원칙 | 결정 |
|---|---|
| SoT | 각 레포의 `.wily/roadmap.yaml` + `.wily/stages/<id>/stage.yaml` |
| 충돌 정책 | **Wily 우선**. GitHub/대시보드에서 바뀐 게 있어도 다음 Wily push가 덮어쓴다. |
| 쓰기 모델 | 대시보드 → GitHub PR 생성. 직접 push 안 함. |
| 인증 | GitHub OAuth + 2명 화이트리스트 |
| 노출 | duckdns 호스트 + Caddy 자동 HTTPS, VPN 없음 |
| LLM 결합도 | 백엔드·동기화 어디에도 LLM 없음 |

---

## 3. 아키텍처

```
[각 Wily 레포]
  .wily/roadmap.yaml ─┐
  .wily/stages/.../    │ on push (GitHub Action)
                       ▼
              ┌────────────────────────────┐
              │ Azure VM (B2ats v2)         │
              │  Caddy (HTTPS, rate limit)  │
              │  FastAPI (uvicorn, 1 worker)│
              │  SQLite (cache + audit log) │
              │  PR-writer (GitHub App/PAT) │
              └────────────────────────────┘
                       ▲
       OAuth(GitHub) 로그인 본인/라이트 (모바일 브라우저)
                       ▲
               GitHub Webhooks (push, label change)
```

루프:
1. 본인/라이트가 어느 레포에서 `.wily/`를 푸시 → 해당 레포 GitHub Action이 *서명된* webhook을 대시보드로 보냄.
2. 대시보드는 GitHub API로 변경 파일을 가져와 파싱·SQLite 갱신.
3. 사용자는 브라우저로 대시보드 접속 → 칸반/리스트로 전체 진행 상황 확인.
4. 사용자가 "Phase 상태 토글" 같은 액션 누름 → 대시보드 백엔드가 *작은 PR* 생성.
5. PR 머지 → push webhook이 되돌아 와 SQLite 재동기화.

---

## 4. 스택 결정 (메모리 예산)

| 컴포넌트 | 선택 | 메모리 |
|---|---|---|
| 리버스 프록시 / HTTPS | **Caddy** (자동 HTTPS, 한 줄 설정) | ~30 MB |
| 백엔드 | **FastAPI + uvicorn(1 worker)** + Python 3.12 | ~150 MB |
| 프론트엔드 | **htmx + Pico.css** (서버 렌더 HTML, 빌드 단계 0) | 0 |
| 저장 | **SQLite** | ~20 MB |
| 인증 | **GitHub OAuth** (authlib 또는 직접 구현) | — |
| 동기화 | GitHub Webhook(push) + GitHub REST API | — |
| 프로세스 관리 | **systemd** unit (Docker 안 씀) | — |
| 배포 | `git pull` + `systemctl restart` | — |

합계 idle 약 ~400 MB. 1 GiB 안에서 동시 사용자 2명 + 가벼운 폴링 트래픽 정도엔 여유.

스택을 굳이 Go로 안 가는 이유: Wily가 이미 Python이라 `.wily/` YAML 파서·상태 로직을 *재사용*할 수 있음. 메모리도 충분.

---

## 5. 레포 구조

대시보드는 **별도 레포 `wily-board`**(org 하 또는 본인 계정 하)로 가는 것을 권고. wily-roadmap은 *동기화 시범 대상*으로만 활용.

```
wily-board/
  pyproject.toml
  README.md
  app/
    main.py              # FastAPI 진입
    config.py            # 환경 변수, 시크릿
    auth/                # GitHub OAuth, 세션, 화이트리스트
    db/
      schema.sql
      migrations/
      repo.py            # SQLite 접근 계층
    sync/
      webhook.py         # /webhooks/github 엔드포인트
      pull.py            # 초기/수동 backfill
      parser.py          # .wily/ YAML 파서 (wily_state_summary.py 재사용 검토)
    actions/
      pr_writer.py       # GitHub PR 생성
      toggle_status.py   # Phase 상태 토글 핸들러
    web/
      routes.py          # HTML 렌더링 라우트
      templates/         # Jinja2 + htmx
        base.html
        board.html
        repo_detail.html
        phase_card.html  # htmx partial
      static/
        pico.min.css
        app.css
  deploy/
    Caddyfile
    wily-board.service   # systemd unit
    install.sh           # 박스 초기 부트스트랩
  tests/
    test_parser.py
    test_webhook_signature.py
    test_pr_writer.py
```

---

## 6. 데이터 모델 (SQLite)

```sql
CREATE TABLE repos (
  id          INTEGER PRIMARY KEY,
  owner       TEXT NOT NULL,         -- 'kokyuhyun' or org name
  name        TEXT NOT NULL,         -- 'digit', 'mac2win', ...
  default_branch TEXT NOT NULL DEFAULT 'main',
  webhook_secret TEXT NOT NULL,
  last_synced_at TEXT,               -- ISO8601
  UNIQUE(owner, name)
);

CREATE TABLE stages (
  id              INTEGER PRIMARY KEY,
  repo_id         INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
  stage_id        TEXT NOT NULL,     -- 's14'
  title           TEXT NOT NULL,
  status          TEXT NOT NULL,     -- pending|ready|in_progress|needs_review|done|blocked|superseded
  owner           TEXT,              -- '@codex', '@right', ...
  depends_on      TEXT,              -- JSON array of stage_ids
  execution_mode  TEXT,              -- 'direct' | 'decomposed'
  raw_path        TEXT,              -- 'stages/s14-...'
  position        INTEGER NOT NULL,  -- order from roadmap.yaml
  UNIQUE(repo_id, stage_id)
);

CREATE TABLE phases (
  id              INTEGER PRIMARY KEY,
  stage_pk        INTEGER NOT NULL REFERENCES stages(id) ON DELETE CASCADE,
  phase_id        TEXT NOT NULL,     -- '14-2'
  title           TEXT NOT NULL,
  status          TEXT NOT NULL,
  owner           TEXT,
  task            TEXT,
  depends_on      TEXT,              -- JSON array
  parallel_group  TEXT,
  current_session TEXT,
  position        INTEGER NOT NULL,
  UNIQUE(stage_pk, phase_id)
);

CREATE TABLE events (
  id          INTEGER PRIMARY KEY,
  ts          TEXT NOT NULL,
  actor       TEXT NOT NULL,         -- github login
  kind        TEXT NOT NULL,         -- 'sync', 'action', 'pr_created', ...
  repo_id     INTEGER REFERENCES repos(id),
  payload     TEXT                   -- JSON blob, 작게
);

CREATE TABLE oauth_sessions (
  sid         TEXT PRIMARY KEY,
  github_login TEXT NOT NULL,
  github_id   INTEGER NOT NULL,
  expires_at  TEXT NOT NULL
);
```

`events`는 *감사 로그 + 디버깅 용*. 무제한 적재하지 말고 60일 retention.

---

## 7. 인증·노출 모델

- **공개 도메인**: `<duckdns 호스트>` (본인이 정해 채워넣기).
- **HTTPS**: Caddy가 Let's Encrypt 자동 발급/갱신.
- **로그인**: GitHub OAuth만. callback `https://<host>/auth/github/callback`.
- **화이트리스트**: 환경 변수 `ALLOWED_GITHUB_LOGINS="kokyuhyun,<right_login>"`. 그 외 ID는 인증 성공해도 403.
- **세션**: 서버측 SQLite `oauth_sessions` + secure HTTP-only cookie.
- **레이트 리밋**: Caddy의 `rate_limit` 모듈로 `/auth/*` 분당 10건, 그 외 분당 60건/IP.
- **OS 방어**: `ufw allow 22/80/443` 외 전부 차단. `fail2ban` 으로 SSH 보호. SSH는 key-only.
- **swap**: 1 GiB swap 추가(`/swapfile`), `vm.swappiness=10`.

라이트가 GitHub 계정이 없다면: Google OAuth 또는 email magic link로 우회. *PR 작성은 본인의 GitHub App/PAT으로* 한 명이 모아 처리하면 라이트가 GitHub에 없어도 동작. → **본인이 확인 후 결정 필요.**

---

## 8. 동기화 메커니즘

### 8.1 등록된 레포 → 대시보드 (단방향, 거의 실시간)

각 레포에 동일한 reusable GitHub Action:

```yaml
# .github/workflows/wily-board-sync.yml
on:
  push:
    paths: ['.wily/**']
  workflow_dispatch:

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Notify Wily Board
        run: |
          curl -fsS -X POST "$WILY_BOARD_URL/webhooks/github" \
            -H "X-Wily-Signature: $(echo -n "$GITHUB_SHA" | openssl dgst -sha256 -hmac "$WILY_BOARD_SECRET" | cut -d ' ' -f2)" \
            -H "Content-Type: application/json" \
            -d "{\"repo\":\"${{ github.repository }}\",\"sha\":\"${{ github.sha }}\",\"ref\":\"${{ github.ref }}\"}"
        env:
          WILY_BOARD_URL: ${{ secrets.WILY_BOARD_URL }}
          WILY_BOARD_SECRET: ${{ secrets.WILY_BOARD_SECRET }}
```

대시보드 `/webhooks/github` 핸들러:
1. HMAC 검증.
2. GitHub REST API로 해당 sha의 `.wily/roadmap.yaml`, `.wily/stages/**` 가져오기 (zipball 한 번 또는 contents API).
3. 파싱 후 `repos`/`stages`/`phases` 행 upsert.
4. `events`에 `sync` 1줄 추가.

### 8.2 초기 backfill / 수동 재동기화

`/admin/repos/<owner>/<name>/resync` 버튼 (관리자만): GitHub contents API로 현재 default branch의 `.wily/` 통째로 가져와서 SQLite 재구축.

### 8.3 GitHub Issues 연동(선택, Phase 6+)

s07 계약은 *유지*하되 *별도 동기화 채널*로 둠. Issues는 *부가적*. 대시보드에서 Phase 카드 옆에 "Discuss" 버튼 → Issue 생성/열기 정도만.

---

## 9. 쓰기 액션 (대시보드 → GitHub PR)

대시보드는 *직접 commit하지 않는다*. 모든 쓰기는 *작은 PR*을 만들어 GitHub에 던진다. 충돌·감사·라이트 협의를 GitHub UI가 무료로 해결.

### 9.1 인증 수단

옵션 A: **GitHub App** 만들어 org/레포에 설치 → installation token으로 PR 생성. 권장.
옵션 B: 본인 PAT을 환경 변수에 박기 → 빠르지만 토큰 회전 골치.

→ Phase 4에서 GitHub App 등록. 권한: `Contents: read/write`, `Pull requests: read/write`, `Metadata: read`.

### 9.2 첫 액션: Phase 상태 토글

플로우:
1. 사용자가 phase 카드의 상태 드롭다운에서 `in_progress` 선택.
2. 백엔드: 해당 repo의 default branch에서 `.wily/roadmap.yaml` (또는 `stages/<id>/stage.yaml`) 가져오기.
3. *bytes-level YAML 안전 치환*: `wily_state_summary.parse_roadmap`로 위치 찾고, *원본 라인의 status 값만* 교체(주석/공백 유지).
4. 새 브랜치 `wily-board/<repo>-<phase>-<ts>` 생성, 커밋 1개, PR 생성.
5. PR 제목: `chore(wily): set <phase-id> -> in_progress (via board)`.
6. 본문에 대시보드 링크와 actor login 표기.
7. `events`에 `pr_created` 1줄.

자동 머지 옵션은 *처음엔 OFF*. 며칠 써보고 충돌 패턴 보고 켤지 결정.

### 9.3 후속 후보 액션 (가치순)

1. Phase block / unblock (사유 코멘트 동반)
2. 새 Phase 추가 (Stage 내 decomposed인 경우)
3. Phase owner 재할당
4. Stage 단위 코멘트(=별도 Issue 생성)
5. Revision note 작성(`.wily/revisions/`)

→ 매번 *실제 자주 쓰이는지* 데이터(`events`) 보고 추가. 한꺼번에 짓지 않음.

---

## 10. UI 설계 (Claude 담당)

### 10.1 페이지

- `/` — **All board**: 모든 레포의 모든 Stage·Phase를 칸반(상태 그룹) 또는 리스트로. 좌측 사이드바에 필터(레포·소유자·상태). 모바일에선 사이드바가 위쪽 드롭다운으로 접힘.
- `/repos/<owner>/<name>` — 한 레포 상세: Stage 트리 + 자식 Phase. wily-watch와 동등한 정보 밀도.
- `/repos/<owner>/<name>/stages/<id>` — Stage 한 개 상세: phase 카드·write_scope·session 링크.
- `/auth/github/{start,callback}` — OAuth.
- `/admin` — 레포 등록·재동기화 (본인만).

### 10.2 컴포넌트

- **PhaseCard** (htmx partial): 상태 글리프·id·title·owner·task·current_session. 상태 드롭다운은 htmx `hx-post`로 `/actions/phase/{id}/status`.
- **StageHeader**: id·title·`done/total phases`·frontier phase 표기.
- **Filters**: 사이드바 form, 변경 시 `hx-get`으로 `/` 갱신.
- **Mobile compact**: 폭 < 600px이면 카드 1열·핵심 정보만(현재 watch 압축 모드와 같은 정신).

### 10.3 시각 언어

watch UI에서 정리한 두 계층(Stage = 1차 행, Phase = rail 들여쓰기) 그대로 가져온다. 다만 웹은 색·여백·아이콘이 풍부하므로:
- Stage = 박스/카드(헤더 + 자식 phase 그리드)
- Phase = 작은 카드, 상태 색 보더
- frontier phase는 강조 보더(예: 노란색)

### 10.4 디자인 토큰

- 폰트: 시스템 sans + 모노스페이스(id 표시용).
- 배경: 라이트/다크 모두 대응(`prefers-color-scheme`).
- 라이브러리: Pico.css 시작 → 부족하면 cherry-pick 커스텀.

---

## 11. 단계별 작업 (Codex / Claude 분담)

각 Phase는 *별도 PR*로. 머지 후 다음 Phase 진입.

### Phase 1 — Azure 박스 부트스트랩 (Codex)
- Ubuntu 24.04 fresh 설정
- non-root 사용자, SSH key-only
- ufw 22/80/443, fail2ban
- swap 1 GiB
- Caddy 설치, duckdns 호스트로 자동 HTTPS 검증(임시 `respond "OK"` 사이트)
- Python 3.12 + uv 설치
- systemd unit 골격 (`wily-board.service`)

산출물: `deploy/install.sh`, `deploy/Caddyfile`, `deploy/wily-board.service`.

### Phase 2 — 백엔드 골격 (Codex)
- `wily-board` 신규 레포 생성
- FastAPI 앱·SQLite 스키마·OAuth·세션·화이트리스트
- 헬스체크 `/healthz`
- 기본 라우트 빈 껍데기 (`/`, `/repos/...`) — 200만 응답
- 테스트: webhook 서명 검증·OAuth 콜백 mock

산출물: `app/` 전체 골격, `tests/`.

### Phase 3 — 동기화 (Codex)
- `/webhooks/github` 구현 (HMAC 검증, contents API fetch, upsert)
- `.wily/` 파서 (가능하면 wily-roadmap의 `wily_state_summary.parse_roadmap`을 *그대로 import*하거나 동등 구현)
- `/admin/repos/<owner>/<name>/resync` 수동 backfill
- 이 wily-roadmap 레포로 PoC: Action 추가 → push → 대시보드 DB에 반영 확인

산출물: `app/sync/*`, `.github/workflows/wily-board-sync.yml` 템플릿.

### Phase 4 — 첫 쓰기 액션 (Codex + Claude)
- GitHub App 등록(본인) → installation_id 받음
- `app/actions/pr_writer.py`: 안전한 YAML 치환 + PR 생성
- `app/actions/toggle_status.py` 라우트
- **Claude 담당**: phase 카드 UI의 상태 드롭다운, htmx 인터랙션, 성공/실패 토스트

### Phase 5 — 다른 레포 onboarding (본인)
- org 생성
- `digit`, `mac2win`, `bounceball` 등록(`/admin`에서 레포 추가)
- 각 레포에 reusable Action 한 줄 추가
- backfill

### Phase 6 — UI 본격 구현 (Claude)
- All board 칸반/리스트
- 필터 사이드바
- 레포 상세 페이지
- Stage 상세 페이지
- 모바일 반응형
- 다크 모드
- frontier 강조·진행도 표기

### Phase 7+ — 가치순 후속 (열어둠)
- 추가 쓰기 액션 (block, owner reassign, …)
- Issues 연동
- 이벤트 타임라인 페이지
- (필요 시) Cloudflare Tunnel 전환

---

## 12. 담당 분리 요약

| 영역 | 담당 |
|---|---|
| 박스 부트스트랩 / Caddy / systemd | **Codex** |
| FastAPI 백엔드·SQLite·동기화·OAuth | **Codex** |
| GitHub Action 템플릿, GitHub App 설정 | 본인 + **Codex** |
| Pricing/도메인/시크릿 등록 | **본인** |
| HTML 템플릿·CSS·htmx 동작·반응형·다크 모드 | **Claude** |
| Phase 카드·Stage 카드·칸반 시각화 | **Claude** |
| PR 작성 로직 (YAML 안전 치환 포함) | **Codex** |
| 테스트(파서·webhook·PR) | **Codex** |
| Stage/Phase 두 계층 시각언어 결정 | **Claude** (이미 watch UI에서 정립) |

---

## 13. 본인이 직접 챙길 체크리스트

- [ ] GitHub org 생성 (이름 정하기)
- [ ] duckdns 호스트 확정 → `WILY_BOARD_URL` 값으로 사용
- [ ] Azure 박스 초기화 + SSH 키 등록
- [ ] GitHub OAuth App 생성 (Phase 2 직전): client_id/client_secret
- [ ] GitHub App 생성 (Phase 4 직전): installation 권한
- [ ] 라이트의 GitHub 계정 유무 확인 → 없다면 인증 방식 재결정
- [ ] org-level secrets에 `WILY_BOARD_URL`, `WILY_BOARD_SECRET` 등록
- [ ] 동기화할 레포 4개 (`wily-roadmap`, `digit`, `mac2win`, `bounceball`)에 `.github/workflows/wily-board-sync.yml` 추가

## 14. 미결정 / 오픈 질문

1. **라이트 GitHub 계정**: 있으면 OAuth만, 없으면 Google OAuth 또는 magic link 추가.
2. **org 명**: 정하면 OAuth/Apps 등록 시 사용.
3. **wily-board 레포의 visibility**: private 권장.
4. **PR 자동 머지**: Phase 4에선 OFF, 며칠 데이터 보고 결정.
5. **다크 모드 기본**: 시스템 따라가는 게 무난(`prefers-color-scheme`).
6. **events retention**: 60일 기본 — 다르면 알려주기.

## 15. 확장 옵션 (나중에 켤 것)

- **Cloudflare Tunnel**: 봇 트래픽이 늘면 Caddy 앞에 cloudflared 두고 80/443을 ufw에서 닫는 방향.
- **Push notification**: PWA로 전환 시 Service Worker + Web Push API.
- **Multi-user**: 셋 이상 합류하면 role 칼럼 + 권한 매트릭스.
- **Self-host metrics**: Prometheus는 1 GiB 박스에 부담 → 자체 SQLite 카운터 + `/metrics`만 expose.

---

## 부록 A — 환경 변수

```
WILY_BOARD_HOST=<duckdns host>
WILY_BOARD_URL=https://<duckdns host>
WILY_BOARD_SECRET=<랜덤 hex 32바이트>
GITHUB_OAUTH_CLIENT_ID=...
GITHUB_OAUTH_CLIENT_SECRET=...
GITHUB_APP_ID=...
GITHUB_APP_PRIVATE_KEY=/etc/wily-board/app.pem
GITHUB_APP_INSTALLATION_ID=...
ALLOWED_GITHUB_LOGINS=kokyuhyun,<right>
SESSION_SECRET=<랜덤 hex 64바이트>
SQLITE_PATH=/var/lib/wily-board/board.sqlite
LOG_LEVEL=INFO
```

## 부록 B — 운영 명령

```sh
# 배포 갱신
ssh wily-board
cd /opt/wily-board && git pull
sudo systemctl restart wily-board

# 로그
journalctl -u wily-board -f

# 수동 백필 (curl)
curl -X POST https://<host>/admin/repos/kokyuhyun/digit/resync \
  -H "Cookie: <session cookie>"
```

## 부록 C — Wily 본 레포에서 분리된 이유

이 계획서는 wily-roadmap 레포 안에 *임시로* 둔다. wily-board는 별도 레포(가능하면 신규 org 아래)로 가는 게 옳음:
- wily-roadmap은 *플러그인·CLI*. wily-board는 *대시보드 웹앱*. 책임 분리.
- 배포 라이프사이클이 다름 (Wily는 git tag 릴리스, wily-board는 always-deploy).
- 향후 라이트/외부 기여자가 wily-board에만 접근하도록 권한 분리 가능.

이 문서는 wily-board 신규 레포가 생기면 거기로 이동.
