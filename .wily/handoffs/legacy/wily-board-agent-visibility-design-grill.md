# Design Grill Handoff: Wily Board Agent Visibility System

## Source Request

사용자는 `wily-roadmap` plugin 기반으로 다음 목적의 시스템 설계를 요청했다.

- 개인 작업 현황을 레포별/단계별로 한눈에 보고, 다음 작업/남은 작업/병렬 가능성/종속성을 확인한다.
- 협업 레포에서 상대방이 어떤 작업을 진행 중인지 실시간으로 확인한다.
- 개인 Azure 서버에 올려 어디서나 접근한다.
- 핵심 목적은 에이전트에게 작업을 위임했을 때 Task와 CP가 어떻게 나뉘었고, 현재 어떤 범위에서 어느 정도 진행 중인지 감독하는 것이다.

## Design Under Review

`wily-roadmap` plugin이 생산하는 repo-local `.wily/` 상태와 bundled `wily-agent`를 기반으로, 별도 sibling repo인 `wily-board`에 웹 감독 보드를 구축한다.

기존 문서/구현에서 확인한 사실:

- `wily-roadmap`은 local-first Project + flat Task manager이고 durable 상태는 `.wily/` 아래에 있다.
- `wily-board`는 fresh rebuild 대상 sibling repo이며, 서버/UI/DB 구현은 `wily-roadmap`에 넣지 않는다.
- 공식 로컬 sync daemon은 `wily-roadmap` plugin의 `wily-agent`가 소유한다.
- 기존 v3 spec은 읽기 전용 Board, `wily-agent` snapshot/heartbeat push, FastAPI/SQLite/SSE 기반을 전제로 한다.

## Desired Outcome

사용자가 브라우저에서 다음을 빠르게 감독할 수 있어야 한다.

- 지금 내 에이전트가 어떤 레포/Task/CP를 잡고 있는지
- Task가 어떤 CP로 분해되었는지
- CP가 어디까지 진행되었고 마지막 업데이트가 언제인지
- 다음에 착수 가능한 작업이 무엇인지
- 협업 레포에서 상대가 어떤 Task를 잡고 있는지
- 특정 레포의 전체 작업 구조와 큰 로드맵이 어떻게 생겼는지

보드는 `.wily`를 직접 수정하지 않는다. 실제 작업 상태 변경은 계속 Wily CLI와 에이전트 실행 흐름에서 발생한다.

## Decision Tree

1. Board 권한 모델
   - 선택: 읽기 전용 projection
   - 이유: 충돌/보안/운영 복잡도를 낮추고 Wily local-first 원칙을 유지한다.

2. 상태 수집 모델
   - 선택: `wily-agent` 실시간 push 중심
   - 이유: GitHub push만으로는 "지금 작업 중" presence와 CP 진행을 볼 수 없다.

3. 인증/노출
   - 선택: GitHub OAuth allowlist + machine bearer token
   - 이유: 브라우저 사용자와 로컬 머신 권한을 분리한다.

4. 작업 대기열과 레포별 큰그림
   - 선택: 전역 작업 대기열 + 레포별 로드맵 + 사용자/머신별 진행 프로젝트 화면
   - 이유: "다음 작업"과 "레포 전체 구조"가 둘 다 1차 목적이다.

5. 협업 레포 분류
   - 선택: Git remote owner/org가 `R-W-LAB`이면 협업 레포
   - 이유: 조직 레포가 협업 경계로 가장 명확하다.

6. 실시간 작업 표시 깊이
   - 선택: 누가 어떤 Task/CP를 잡고 있는지 중심
   - 이유: 충돌 판단은 에이전트/CLI가 수행하고, 보드는 감독 가시성에 집중한다.

7. 에이전트 작업 흔적 소스
   - 선택: `.wily/tasks/<id>/progress.jsonl` ledger가 공식 기록, Custom Workflow status board는 import/recovery 소스
   - 이유: 실시간 감독에는 status board가 유용하지만 장기 신뢰성은 `.wily` ledger가 가져야 한다.

8. UI 표시 단위
   - 선택: CP 타임라인 기본, 각 CP/상태 클릭 시 상세 드릴다운
   - 이유: 사용자는 에이전트 작업을 직접 조작하기보다 감독한다.

9. 프론트 스택
   - 선택: FastAPI + SQLite + SSE + Vite React SPA
   - 이유: React UI 표현력은 필요하지만, 1 GiB급 Azure 서버에서 Next.js SSR 상시 프로세스는 과하다.

## Resolved Decisions

- Board는 Wily Task 상태를 직접 변경하지 않는다.
- Board DB에는 task write가 아니라 projection, 이벤트 로그, 세션, 머신, UI preference만 저장한다.
- `wily-agent`는 `.wily` 변경 시 snapshot을 push하고, presence는 heartbeat로 보낸다.
- Snapshot은 현재 상태 복구의 기준이고, heartbeat는 연결/작업 중 표시의 기준이다.
- GitHub OAuth allowlist로 브라우저 접근을 제한한다.
- Machine은 one-time code로 등록하고, 이후 bearer token으로 `/agent/*` API를 호출한다.
- `R-W-LAB` org 레포는 협업 레포로 자동 분류한다.
- Allowlist 사용자는 기본적으로 모든 `R-W-LAB` 협업 레포를 볼 수 있다.
- 사용자는 개인 화면에서 프로젝트 hide/pin override를 설정할 수 있다.
- 좌측 레포 목록은 협업/개인으로 나눠 정렬한다.
- 메인 홈은 로그인 사용자 기준 "내 진행 중 작업"과 "다음 작업"을 보여준다.
- 레포 상세 기본 화면은 상태 그룹과 다음 작업 패널이다.
- 레포 상세에는 별도 "로드맵 보기"로 DAG/타임라인 큰그림을 제공한다.
- Agent 감독 기본 UI는 CP 타임라인이다.
- CP/상태를 클릭하면 현재 액션, 상태판 요약, 검증 결과, 메모, result/handoff 요약을 상세로 본다.
- 표준 상위 상태는 한국어 단순 상태로 둔다: 대기, 작업 중, 검증 중, 차단, 완료, 오래됨.
- 실제 CP 이름과 status board 텍스트는 상세에 보존한다.
- UI 문구는 기본 한국어다. 내부 용어를 화면에 그대로 노출하지 않는다.
- 저장 정책은 현재 snapshot 보관 + 이벤트 로그 30일 내외 보존이다.
- 장애 시 agent는 로컬 실패 상태/사유를 남기고 재연결 시 snapshot을 재전송한다.
- UI는 stale 상태, 마지막 성공/실패 사유를 한국어로 표시한다.
- 구현 순서는 계약 우선 + 얇은 UI 검증 + 최종 React UI 확장이다.

## Rejected Alternatives

- Board에서 claim/block/done을 직접 수행
  - 거부 이유: 읽기 전용 감독 보드라는 경계가 흐려지고 `.wily` 쓰기 충돌이 생긴다.
- GitHub push/webhook만으로 sync
  - 거부 이유: 커밋 전 에이전트 진행 상황과 실시간 CP 상태를 볼 수 없다.
- Board 중심 태스크 매니저
  - 거부 이유: Wily local-first 원칙을 뒤집고 Board가 source of truth가 된다.
- Full Next.js SSR + FastAPI
  - 거부 이유: 작은 Azure VM에서 Node SSR 상시 운영 부담이 크고, SEO/SSR 장점이 내부 보드에는 크지 않다.
- 터미널 전체 로그/diff 전문/민감한 실행 출력 저장
  - 거부 이유: 감독 목적에 비해 정보량과 보안 부담이 크다.

## Scenarios Tested

1. 개인 감독
   - 사용자가 보드 접속
   - 좌측에서 개인 레포 목록 확인
   - 메인에서 내 진행 중 Task와 다음 작업 큐 확인
   - 진행 중 Task의 CP 타임라인에서 현재 위치 확인

2. 협업 레포 확인
   - `R-W-LAB` org remote를 가진 프로젝트가 협업 영역에 자동 표시
   - 상대 머신의 heartbeat가 들어오면 상대가 잡은 Task/CP가 표시
   - stale이면 마지막 업데이트와 오래됨 상태를 표시

3. 에이전트 작업 감독
   - 에이전트가 Task를 CP로 나눠 실행
   - `.wily` ledger에 CP start/done/note가 쌓임
   - status board가 있으면 `wily-agent`가 누락된 ledger 이벤트를 import/recovery
   - 보드는 CP 타임라인 기본 표시, 클릭 시 상세 표시

4. 오프라인/장애
   - Azure Board가 잠시 내려가도 Wily CLI 작업은 계속 진행
   - agent는 실패 사유를 로컬에 남김
   - 재연결 시 최신 snapshot으로 수렴
   - UI는 stale과 마지막 성공/실패 정보를 보여줌

5. 레포 큰그림 파악
   - 레포 상세 기본 화면에서 진행 중/대기/차단/완료를 조밀하게 확인
   - 필요 시 로드맵 보기에서 Task 의존 관계를 DAG/타임라인으로 확인

## Boundary Decisions

- Source of truth:
  - `.wily/`가 durable source of truth다.
  - Board SQLite는 읽기 모델/cache다.

- Write boundary:
  - Task 상태 변경은 Wily CLI/agent workflow에서만 발생한다.
  - Board가 쓸 수 있는 것은 session, machine registration, event log, UI preference다.

- Repo boundary:
  - `wily-roadmap` plugin: Wily CLI, `.wily` schema/lifecycle, `wily-agent`.
  - `wily-board` repo: FastAPI server, SQLite projection, SSE, React UI, deployment.

- Sync boundary:
  - Agent가 `.wily`와 status board를 해석해 Board API contract payload를 만든다.
  - Board는 payload validation/storage/rendering을 맡고 `.wily` 세부 파서를 과도하게 중복하지 않는다.

- Collaboration boundary:
  - 협업 여부의 1차 기준은 Git remote owner/org `R-W-LAB`.
  - `actors.yaml`은 표시명, capacity, 작업자 매핑에 사용한다.

- Language boundary:
  - UI는 한국어 우선.
  - 코드/API/내부 contract는 영어 식별자를 유지하되 화면 노출 문구는 한국어로 번역한다.

## Risks And Assumptions

- Azure VM 메모리가 작다. Node SSR 상시 운영은 피하고 정적 React asset을 Caddy로 서빙해야 한다.
- `wily-agent`가 status board를 안정적으로 찾고 import하는 규칙이 필요하다.
- CP 기록 누락은 계속 발생할 수 있다. 실행 패키지 규칙 + agent import recovery + 향후 CLI 경고가 필요하다.
- React SPA는 인증/세션/SSE 연결 상태 처리를 명확히 설계해야 한다.
- `.wily` ledger와 status board가 충돌할 때 우선순위가 필요하다. 기본은 ledger 우선, status board는 누락 복구/힌트로 둔다.
- `R-W-LAB` org 판정은 remote URL 정규화가 정확해야 한다. SSH/HTTPS remote 모두 같은 project_id로 수렴해야 한다.
- Board가 읽기 전용이어도 hide/pin 같은 UI preference 쓰기는 존재한다. 이를 Task write와 구분해야 한다.
- CP 상세에 너무 많은 원문을 노출하면 감독 UI가 로그 뷰로 변질될 수 있다.

## Decision Log

- Q1 Board write 권한: A, 읽기 전용.
- Q2 상태 소스: A, `wily-agent` 실시간 push.
- Q3 인증: A, GitHub OAuth allowlist + machine token.
- Q4 스케줄러 수준: 전역 작업 대기열 + 레포별 큰그림 + 사용자/머신별 화면.
- Q5 협업 분류: `R-W-LAB` org remote 기준.
- Q6 협업 가시성: 전체 공유 + hide/pin override.
- Q7 실시간 표시 깊이: A, 누가 무엇을 잡고 있는지 중심.
- Q8 데이터 보존: A, 현재 snapshot + 짧은 이벤트 로그.
- Q9 첫 화면 IA: 좌측 레포 목록 + 메인 내 진행 중/다음 작업.
- Q10 레포 큰그림: C, 상태 그룹 기본 + 로드맵 보기.
- Q11 Agent sync: A, `.wily` 변경 snapshot + heartbeat.
- Q12 장애 처리: C, stale 표시 + 실패 사유 + 재연결 snapshot.
- Q13 작업 흔적 소스: C, `.wily` ledger + status board import/recovery.
- Q14 작업 흔적 UI: CP 타임라인 기본 + 클릭 상세.
- Q15 상태 체계: C, 표준 상위 상태 + 실제 CP 이름/텍스트 보존.
- Q16 기록 강제력: C, 실행 패키지 규칙 + agent status board 감시/import.
- Q17 첫 구현 범위: 완성형 v1 범위로 가되 얇은 UI부터 검증.
- Q18 구현 순서: C, 계약 우선 + 얇은 UI.
- Q19 프론트 스택: FastAPI + Vite React SPA.

## Requirements Implications

후속 requirements/deep-interview에서 구체화해야 할 항목:

- Agent snapshot payload v1
  - project, repo remote, machine, actor, current task, current CP, task list, dependency list, CP timeline, status board import summary.
- CP ledger contract
  - `wily cp start/done/note`, import-status, idempotency key, timestamp/actor/task/cp/event fields.
- Status board discovery/import
  - 어떤 파일을 status board로 볼지, 어느 Task와 연결할지, 누락분을 어떻게 감지할지.
- Board schema
  - projects, machines, users, task snapshots, tasks, task_progress, cp_events, actor_presence, ui_preferences, agent_events.
- React IA
  - 좌측 레포 목록, 홈 큐, 협업/개인 grouping, 레포 상세, CP timeline, 상세 drawer/panel, 로드맵 보기.
- 한국어 UI glossary
  - snapshot=상태 동기화, heartbeat=연결 상태, task=작업, checkpoint=체크포인트, stale=오래됨/연결 끊김 등.
- Deployment
  - Caddy 정적 asset + FastAPI API reverse proxy + SQLite backup + systemd.
- Security
  - GitHub OAuth allowlist, machine token hashing, HTTPS only, secret handling, event retention.

## Open Questions

- 협업자 GitHub login과 `R-W-LAB` allowlist의 실제 값.
- Azure VM의 정확한 현재 사양과 swap/systemd/Caddy 상태.
- React SPA 빌드/배포를 로컬 수동으로 할지 GitHub Actions로 할지.
- Status board import의 정확한 parser 범위: 현재 action 한 줄만 볼지, 검증/실패/메모까지 구조화할지.
- 로드맵 보기에서 DAG 라이브러리를 쓸지 직접 SVG/HTML layout을 쓸지.
- 모바일에서 좌측 레포 목록을 drawer로 둘지 bottom nav와 병행할지.

## Recommended Next Step

`deep-interview`로 구현 요구사항을 좁힌 뒤, `plan-goal-runner`로 fresh `wily-board` repo 실행 계획을 만든다.

권장 순서:

1. Board API/DB/agent payload contract requirements.
2. `wily-agent` status board import/recovery requirements.
3. React SPA IA and Korean UI glossary requirements.
4. Azure deployment/runbook requirements.
