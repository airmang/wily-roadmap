# Wily Roadmap v3 — Full Redesign

Date: 2026-05-18
Author: Wily 박사 (kokyuhyun@goedu.kr) with Claude
Status: Spec — awaiting user approval, implementation handed to Codex
Supersedes: `wily-roadmap-v2` schema, all v2 command surface, wily-board integration

---

## 1. 왜 갈아엎는가

현 wily-roadmap (v2)은 다음과 같은 누적 문제로 사용 가치보다 마찰이 커졌다.

1. **계층이 깊다.** Stage → Phase → Session 3계층은 작은 작업에도 분해 절차를 강요. 박사님이 실제로 원하는 단위는 "goal-sized task" 한 층.
2. **검증 강제력 0.** `wily complete`가 단순 metadata flip이라 라이트 같은 비협조 협업자가 wily 컨트랙트를 무시해도 통과됨.
3. **custom-workflow-skillset (이하 cw) 통합 실패.** `$wily-run`이 cw로 라우팅했지만 cw는 wily 상태 모르고 `/goal`로 밀어붙임. 두 truth가 충돌.
4. **wily-board 부하.** 별도 FastAPI 서비스 + GitHub App + secret rotation까지 따라옴. P6에서 GitHub App 401로 durable sync도 깨진 상태. 갈아엎으면서 같이 정리.
5. **16개 스킬, 4244줄 monolith.** 유지보수 한계.

박사님 의도 한 줄: **"wily는 큰 그림 + Goal-sized Task 리스트를 관리하는 매니저, cw는 실행자."**

---

## 2. 핵심 결정 (요약)

이 문서 전체를 관통하는 강한 결정. 구현 중 흔들지 말 것.

| # | 결정 | 근거 |
|---|------|------|
| D1 | **계층 폐기, Project + Task 평탄 구조** | 박사님: "내부적으로 단계는 나누지 않아" |
| D2 | **Task = goal-sized, cw가 한 번에 처리 가능한 단위** | 분해는 cw 책임 (cp), wily는 침범 안 함 |
| D3 | **wily는 cw를 직접 호출하지 않음. goal 텍스트 출력만, 호출은 박사님 손** | wily↔cw 의존 0 |
| D4 | **라이트는 wily 명령 0개 친다는 비관 가정** | 컨트랙트 강제 무의미 |
| D5 | **actor 1급 시민. 박사님 + 라이트 둘 다 plugin 설치** | 같은 조건. 협업 레포 = 양쪽 lane, 개인 레포 = 본인만 |
| D6 | **cp는 cw 소유, wily는 관찰만** | progress.jsonl + commit trailer 두 채널로 받음 |
| D7 | **wily-board 폐기** | 별도로 완전 재설계 예정 (이 spec 범위 밖) |
| D8 | **`wily done`은 검증 게이트 없음, 단순 status flip + transition sanity** | 박사님: "오버헤드도 생각해야지". 박사님 명령 친 행위 자체로 책임 가시화 |
| D9 | **`assignee` (계획 owner) ≠ `actor` (실제 잡은 사람)** | 협업 레포에서 init/replan으로 분배 가능 |
| D10 | **에이전트 친화 인터페이스** | "T03 cw로 진행해줘" 한 마디로 Claude/Codex가 claim→go→cw→done까지 굴림 |

---

## 3. 디렉토리 구조

```
.wily/
  project.md                  # 큰 그림 (자유 텍스트, init/replan으로 작성·갱신)
  tasks.yaml                  # 모든 task의 single source of truth
  actors.yaml                 # actor 별칭 ↔ git author 매핑
  tasks/
    T05/
      acceptance.md           # 길어지면 분리 (짧으면 tasks.yaml 인라인)
      progress.jsonl          # cw가 cp 시작/완료 시 append
      result.md               # done 시점 wily가 자동 생성
  init/
    draft.yaml                # init/replan 진행 중 상태 (commit 시 삭제)
  archive/
    legacy-2026-05-18/        # 마이그레이션 시 옛 .wily/ 통째 보관
```

**제거되는 것들:** `roadmap.yaml`, `status.md`, `decisions.md`, `migrations/`, `backups/`, `sessions/`, `stages/`, `phases/`, `revisions/`, `local/`, `local/board-last-emit.json`.

---

## 4. 데이터 스키마

### 4.1 `tasks.yaml`

```yaml
schema: wily-v3
project_title: "wily-roadmap 재설계"     # 한 줄 요약. project.md에 본문.
tasks:
  - id: T05                              # T + zero-padded 2자리 이상 정수. 박사님이 그대로 보기 좋게.
    title: "Task lifecycle CLI"
    intent: |                            # 한 단락. 왜 하는지.
      박사님이 wily에서 task entry/exit 칠 때의 contract.
      claim → go → done/block 흐름을 cli로 노출.
    acceptance: |                        # 객관적 완료 조건. cw에 그대로 던지는 입력.
      - `wily claim T05`가 actor + timestamp + claim-sha 기록
      - `wily done T05`가 status flip + result.md 자동 생성
      - 비정상 transition은 거부 (exit code 3)
    scope:                               # git diff에서 자동 매핑/관찰에 쓰이는 path glob
      - "plugins/wily-roadmap/scripts/wily.py"
      - "plugins/wily-roadmap/tests/test_lifecycle.py"
    depends_on: [T03]                    # 다른 task id의 list. cycle 금지.
    status: ready                        # ready | in_progress | done | blocked
    assignee: wily                       # 계획 owner. null 가능.
    actor: null                          # 실제 claim한 사람. claim 시 채워짐.
    claim_sha: null                      # claim 시 HEAD commit sha. 변경 추적 기준.
    claim_at: null                       # ISO8601 UTC (Z suffix). 예: "2026-05-18T11:00:00Z"
    done_at: null                        # ISO8601 UTC (Z suffix)
    blocker: null                        # block 사유 (block 시 채워짐)
```

`acceptance`가 4줄 초과면 `tasks/<id>/acceptance.md`로 옮기고 tasks.yaml에는 `acceptance_file: tasks/T05/acceptance.md`만.

### 4.2 `actors.yaml`

```yaml
schema: wily-v3
actors:
  wily:
    display: "Wily 박사"
    git_author_emails: ["kokyuhyun@goedu.kr"]
    git_author_names: ["kokyuhyun", "wilycastle"]
  right:
    display: "Right 박사"
    git_author_emails: ["<right@email>"]    # init에서 git log 분석으로 자동 후보 제시
    git_author_names: ["<right-name>"]
```

레포 모드 판정:
- actors가 1개만 정의됨 → **개인 레포** (watch에 본인 lane만)
- 2개 이상 → **협업 레포** (actor별 lane)

### 4.3 `project.md`

자유 텍스트. 권장 섹션 (init 인터뷰가 자연스럽게 채움):
- 한 줄 목적
- 사용자 / 이해관계자
- 성공 조건
- 절대 안 하는 것 / 제약
- 협업 인원 요약

박사님이 직접 편집하는 일 없음. `wily init` / `wily replan`이 갱신.

### 4.4 `tasks/<id>/progress.jsonl`

cw가 cp 시작/완료 시 append. wily는 read-only.

```jsonl
{"ts":"2026-05-18T11:03:21Z","actor":"wily","cp":"plan","event":"start"}
{"ts":"2026-05-18T11:05:44Z","actor":"wily","cp":"plan","event":"done","note":"5 cps planned"}
{"ts":"2026-05-18T11:06:01Z","actor":"wily","cp":"implement-parser","event":"start"}
{"ts":"2026-05-18T11:18:33Z","actor":"wily","cp":"implement-parser","event":"done"}
```

필수 필드: `ts` (ISO8601 UTC), `actor`, `cp`, `event` (`start` | `done` | `note`).
선택 필드: `note` (자유 텍스트).

파일은 task `claim` 시 wily가 빈 파일로 생성, `done` 시 그대로 보존.

### 4.5 `tasks/<id>/result.md`

`wily done` 시 자동 생성:

```markdown
# T05: Task lifecycle CLI — done

- actor: wily
- claim: 2026-05-18T11:00:00Z (sha a1b2c3d)
- done: 2026-05-18T13:45:00Z
- commit range: a1b2c3d..e4f5g6h
- changed files: 12 (+243 -67)
- cp count: 5/5
- scope drift: 0 files outside scope
- note: (--note "..." 옵션으로 박사님 메모, 없으면 빈 줄)
```

---

## 5. 명령 표면

총 10개 명령. 각 명령은 한 책임. stdout은 사람 친화 텍스트가 기본, `--json` 옵션 시 구조화된 JSON.

### 5.1 `wily init` — 인터뷰 기반 부트스트랩

박사님이 yaml/md 직접 편집하지 않는다는 강한 제약을 받음. 모든 입력이 wily 명령으로.

#### 모드 감지

- `--new`: greenfield (강제)
- `--adopt`: brownfield (강제)
- 옵션 없으면 자동 감지: git history + README + 기존 `.wily/` 존재 여부로 판정. 모호하면 박사님께 확인.

#### Greenfield 인터뷰 단계

순차 질문, 각 질문은 박사님이 `wily init answer <text>`로 응답. wily가 다음 질문 출력.

1. 이 프로젝트의 한 줄 목적은?
2. 누가 쓰나? (사용자/이해관계자)
3. 무엇이 되면 성공인가? (성공 조건)
4. 절대 안 하는 것 / 제약은?
5. 협업 인원? (actor 별칭 + git author 매핑. git log에서 자동 후보 제시)
6. 큰 그림에서 자연스럽게 떨어지는 작업 단위 후보를 wily가 제안 → 박사님이 수정·확정

#### Brownfield 인터뷰 단계

1. 자동 분석 결과 출력 (git log 요약, 파일 트리 1단, README/package metadata)
2. "이 프로젝트가 X를 한다고 추측한다. 맞나?" → 박사님 ok/revise
3. 큰 그림 보강 질문 (greenfield Q2~Q4와 유사)
4. **이미 한 일**: 분석에서 추출한 큰 변경 단위를 done task 후보로 자동 생성
5. **앞으로 할 일**: 남은 그림에서 ready task 후보 생성
6. 박사님 확정

#### Init 서브명령 (전부 wily 안에서)

| 명령 | 동작 |
|------|------|
| `wily init` | 진행 중이면 현재 질문 재출력(이어가기), 처음이면 시작 |
| `wily init --new` / `--adopt` | 모드 강제 |
| `wily init answer <text>` | 현재 질문에 답 저장, 다음 질문으로 |
| `wily init answer --multi` | stdin EOF까지 멀티라인 답 받음 |
| `wily init back` | 한 단계 뒤로 |
| `wily init revise <key> <text>` | 이미 답한 항목 덮어쓰기 (key는 `wily init show`에 표시되는 슬러그) |
| `wily init show` | 지금까지 답 + 현재 단계 요약 |
| `wily init suggest` | 충분히 모였으면 task 후보 출력, 부족하면 부족분 안내 |
| `wily init add-task "<title>"` | task 후보 수동 추가 (인터뷰가 놓친 항목) |
| `wily init revise-task <id> <field> <value>` | task 후보의 title/intent/acceptance/scope/depends_on 수정 |
| `wily init drop-task <id>` | task 후보 제거 |
| `wily init assign <id> <actor>` | task 후보에 assignee 부여 |
| `wily init commit` | draft → `project.md` + `tasks.yaml` 확정, draft 삭제 |
| `wily init cancel` | draft 폐기 |

진행 상태는 `.wily/init/draft.yaml`에 영구 저장. 박사님이 도중에 세션 종료해도 다음 `wily init`에서 이어감.

### 5.2 `wily next` — 다음 ready task

```
$ wily next
T03 ready  "Task lifecycle CLI"  assignee=wily  depends_on=[T01,T02] satisfied
```

- depends_on 모두 done이고 status=ready인 task 중 첫 번째.
- 협업 레포면 `--mine`으로 본인 assignee만 필터.
- 없으면 exit 1.

### 5.3 `wily claim <id>` — task 잡기

```
$ wily claim T03
T03: ready → in_progress
actor: wily (kokyuhyun@goedu.kr)
claim_sha: a1b2c3d
progress.jsonl initialized: .wily/tasks/T03/progress.jsonl
```

- status가 `ready` 또는 `blocked`에서만 가능 (blocked에서 claim 시 blocker 필드 클리어). `in_progress` / `done`은 거부.
- 이미 다른 actor가 claim 중이면 거부 (`--force`로 빼앗기 가능. assignee와 actor 불일치 시 warn).
- claim sha는 HEAD. 이후 `git diff <claim_sha>...HEAD`가 scope drift 추적 기준.

### 5.4 `wily go <id>` — cw에 던질 goal 텍스트 출력

```
$ wily go T03
==== copy below into custom-workflow-skillset:plan-goal-runner ====
# Wily Task T03: Task lifecycle CLI

## Intent
박사님이 wily에서 task entry/exit 칠 때의 contract.
claim → go → done/block 흐름을 cli로 노출.

## Acceptance
- `wily claim T03`가 actor + timestamp + claim-sha 기록
- ...

## Scope (변경 허용 경로)
- plugins/wily-roadmap/scripts/wily.py
- plugins/wily-roadmap/tests/test_lifecycle.py

## Progress 기록 위치
- .wily/tasks/T03/progress.jsonl  (cp 시작·완료 매번 한 줄 append)
- commit trailer: Wily-Task: T03, Wily-CP: <cp-name>

## 검증 후 박사님께 보고할 항목
- acceptance 각 항목 대조 결과
- scope 밖 변경이 있다면 명시
====================================================================
```

- 출력은 stdout. 박사님이 복붙해서 cw에 던지거나, Claude/Codex 에이전트가 이 출력을 그대로 cw 스킬에 invoke.
- status는 안 바꿈 (이미 in_progress).
- `--json`으로 구조화 출력 (에이전트가 파싱하기 좋게).

### 5.5 `wily done <id>` — 마감

```
$ wily done T03
T03: in_progress → done
result.md 작성됨 (변경 12 files, 5 cp, commit range a1b2..c3d4)
```

- status가 `in_progress`가 아니면 거부.
- `result.md` 자동 생성 (4.5 형식).
- **검증 묻지 않음**. 박사님이 친 명령 = 검증 완료 의사.

옵션:
- `--note "<text>"` — result.md에 박사님 메모 첨부
- `--observed` — 라이트 등 다른 actor의 작업을 박사님이 대신 마감 (`actor`는 observed commit author로 추론·기록)

### 5.6 `wily block <id> <reason>` — 차단

```
$ wily block T03 "Codex API 키 만료 - 라이트가 갱신해야 함"
T03: in_progress → blocked
blocker recorded.
```

- in_progress 또는 ready에서 가능.
- `wily watch`에서 blocker 텍스트 표시.
- 해제는 `wily claim <id>`가 자동으로 처리: blocked → in_progress로 전이하면서 `blocker` 필드 클리어. 별도 unblock 명령 없음 (명령 표면 10개 유지).

### 5.7 `wily replan` — task 추가·수정·제거

init과 흐름 유사. draft.yaml 같은 임시 파일 사용 가능 (`.wily/init/draft.yaml` 재활용 또는 별도). 서브명령:

| 명령 | 동작 |
|------|------|
| `wily replan` | 현재 tasks.yaml 요약 출력, "추가/수정/제거 어떤 작업?" 안내 |
| `wily replan add "<title>"` | 새 task 인터뷰 시작 (intent/acceptance/scope/depends_on/assignee) |
| `wily replan revise <id> <field> <value>` | 기존 task 수정. status=done이면 거부 (history 보존). in_progress면 warn. |
| `wily replan drop <id>` | task 제거. status=done이면 거부, ready만 가능. |
| `wily replan assign <id> <actor>` | assignee 부여·변경 |
| `wily replan project` | project.md 갱신 인터뷰 (큰 그림 진화 시) |
| `wily replan commit` | 변경 확정 |
| `wily replan cancel` | 변경 폐기 |

의존성 일관성 검사:
- depends_on에 존재하지 않는 id 있으면 commit 거부
- cycle 검출 시 commit 거부

### 5.8 `wily land <id>` — git commit + push

```
$ wily land T03
변경 수집: 12 files (모두 scope 내)
commit message:
  T03: Task lifecycle CLI

  - claim/go/done flow 구현
  - acceptance 게이트 (transition sanity)
  - result.md 자동 생성

  Wily-Task: T03

push to origin? [y/N]
```

동작:
1. task status가 `done`이 아니면 거부 (`--force`로 우회 가능).
2. `git status` + scope path로 변경 파일 자동 수집.
3. scope 밖 파일 있으면 warn + 박사님이 select/exclude.
4. commit message 자동 조립 (`<id>: <title>` + result.md 요약 + `Wily-Task: <id>` trailer).
5. `git add` → `git commit` → 박사님 확인 후 `git push`.
6. push 실패 시 commit은 유지, push만 재시도 가능.

라이트의 작업은 land에 안 들어옴 (라이트가 자기 PR로 처리). 박사님이 라이트 PR을 머지한 경우 `wily done T0X --observed` 후 land는 안 함.

### 5.9 `wily watch` — 라이브 표시

기존 watch의 ASCII rail/glyph 시각언어 유지. 협업 레포면 actor lane.

```
Project: wily-roadmap 재설계
─────────────────────────────────────────────────────────────────────
T01  ✓ done         wily   "watch initial sketch"           +12 -3
T02  ✓ done         wily   "schema migration"               +5 -1
T03  ▶ in_progress  wily   [▓▓▓░░ 3/5 cp]  cp:implement-parser
T04    ready                assignee=wily
T05    ready                assignee=right
T06  ⏵ observed     right  3 commits, scope=plugins/...
                            └ guessed task: T05 (no trailer)
T07    blocked      right  "GitHub App 401 (commit abc123)"

actors: wily kokyuhyun@goedu.kr  ·  right <right@email>
modes: collaborative repo
```

글리프:
- `✓ done`
- `▶ in_progress`
- `⏵ observed` — 라이트 commit, formal claim 없음
- `blocked`
- `ready`

cp 게이지는 `progress.jsonl` 라이브 카운트. 개인 레포면 라이트 lane 자연 축소 (행 없음).

폴링 주기는 기본 2초. `--interval <seconds>`로 변경. `--once`로 1회 출력 후 종료.

`wily watch`는 read-only. 어떤 상태도 안 바꿈.

### 5.10 `wily status` — 스냅샷

`wily watch --once`의 alias 수준. CI/pipe용으로 명확한 종료 코드:
- 0: 모든 task done
- 1: ready/in_progress task 남음
- 2: blocked task 존재

`--json`으로 전체 상태 JSON 덤프 (에이전트/외부 도구 친화).

---

## 6. 라이트 작업 관찰 메커니즘

라이트는 wily 명령 0개 친다. wily가 라이트의 진척을 잡는 채널:

### 6.1 Git author로 actor 식별

`actors.yaml`의 `git_author_emails` / `git_author_names`로 매칭. 매칭 없으면 `unknown`으로 그림자 표시.

### 6.2 Commit trailer로 task 매핑

권장 trailer (라이트가 박아주면 자동 매핑):
- `Wily-Task: T05`
- `Wily-CP: <cp-name>` (선택, cp 단위 진척 표시용)
- `Wily-Done: T05` (선택, 머지 시 자동 done 트리거)

trailer 없어도 wily는:
- commit author로 actor 식별 (`right`)
- 변경 파일을 `scope` glob과 매칭해서 후보 task `guessed` 표시
- 둘 다 실패하면 `observed (unmatched)` 행으로 표시 (수동 매핑은 11절의 open 항목 — `wily attribute` 추후 도입 가능)

### 6.3 동기화

`wily watch` / `wily status`가 매번 `git fetch origin <branch>` 후 `git log origin/<branch>...HEAD` 비교. 별도 webhook/polling 인프라 없음.

박사님 환경에서 fetch가 필요 — 박사님이 작업 전 `git fetch`를 안 했어도 watch가 처음 호출 시 자동으로 한 번 fetch.

---

## 7. 스킬과 에이전트 통합

새 wily 플러그인의 스킬 수: **10개 명령 + 1개 메타 가이드 = 11개 (또는 commands/와 skills/를 정리하면 6~7개)**.

### 7.1 명령별 skill 파일

각 명령에 대해 `plugins/wily-roadmap/skills/wily-<cmd>/SKILL.md` 1개. 기존 v2 스킬 16개는 전부 폐기, 새로 작성.

내용 권장 구조 (기존 컨벤션 유지):
- 메타 (name, description)
- 무엇을 하는지 한 단락
- Internal command (실제 `wily.py <subcommand>` 호출 매핑)
- 인자/옵션
- Response style (기존 한국어 응대 규칙 유지)

### 7.2 메타 가이드 스킬: `wily-execute`

이름은 옛 `wily-run`을 의도적으로 피함. 책임 다름:

- **옛 `wily-run`**: cw 라우터, request/result 파일 만들고 cw 호출 지시
- **새 `wily-execute`**: 에이전트가 wily 명령을 어떤 순서로 굴리는지 가이드

내용 권장:
- "박사님이 `T03 cw로 진행해줘`라고 하면: `wily next` 또는 `wily status`로 확인 → `wily claim T03` → `wily go T03` → 출력 텍스트를 `custom-workflow-skillset:plan-goal-runner`에 invoke → cw 종료 후 acceptance 대조 → `wily done T03`. 박사님 명시 승인 후 `wily land T03`."
- "scope 밖 변경이 있으면 done 전에 박사님께 알림. 박사님 결정 따름."
- "원격 액션(land 포함)은 박사님 명시 승인 후."
- "라이트 작업의 done은 박사님이 명시적으로 요청한 경우에만. `wily done --observed`."

### 7.3 에이전트 친화성 요구사항

모든 `wily <cmd>`는 다음을 보장:

- **exit code**:
  - 0: 성공
  - 1: 명령 실패 (네트워크, 파일 IO, git 등)
  - 2: usage 오류 (인자 부족, 알 수 없는 옵션)
  - 3: 상태 transition 거부 (이미 done인 걸 claim 등)
- **stdout**: 사람 친화 텍스트 기본. `--json`으로 구조화 출력.
- **stderr**: 오류/경고만.
- **한 명령 = 한 책임**: claim과 go를 합치지 않음. 에이전트가 조합.

---

## 8. 마이그레이션

기존 `.wily/`는 31 stage + 200+ 파일 + 다수 session. 자동 마이그레이션은 `wily init --adopt`가 담당.

### 8.1 흐름

1. **archive**: 기존 `.wily/` 전체를 `.wily/archive/legacy-2026-05-18/`로 mv.
2. **분석**: archive에서 `roadmap.yaml` 읽어 31 stage의 id/title/status 추출. `stages/<sid>/stage.yaml` 있으면 거기서 intent/scope 후보 끌어옴. `sessions/`에서 done timestamp 추출.
3. **draft 생성**: brownfield 인터뷰 시작. 자동 분석 결과를 1차 draft로 띄움.
4. **박사님 확인**: 
   - 큰 그림 (project.md) — 옛 `status.md` 본문을 초안으로 띄우고 박사님 수정
   - 옛 stage들을 통째로 `done` task로 흡수할지 / 일부만 / 전혀
   - 옛 stage id (s01...s31) → 새 task id (T01...T31) 매핑 박사님 승인
   - 남은 그림에서 새 ready task 도출
5. **commit**: `project.md` + `tasks.yaml` + `actors.yaml` 작성. draft 삭제.

### 8.2 부수효과 정리 (마이그레이션 마지막 단계가 안내만, 실행은 박사님)

- **Codex hooks 정리**: `~/.codex/hooks.json`의 PostToolUse → `wily.py live-worked` 항목 제거. wily가 안내 텍스트만 출력.
- **GitHub Actions workflow 폐기**: `.github/workflows/wily-board-sync.yml` (또는 동등 파일) 삭제 PR. 박사님이 별도 처리.
- **board 관련 파일 폐기**: `runners/` 같은 board용 자산 있으면 정리. wily 플러그인 내 board 관련 코드 전부 제거.
- **`~/.wily/board.json`**: 새 wily는 안 읽음 (gracefully ignore). 박사님이 직접 지우든 말든 무관.
- **마켓플레이스 manifest 갱신**: `.agents/plugins/marketplace.json`과 `plugins/wily-roadmap/.codex-plugin/plugin.json`을 새 명령·스킬 목록으로 갱신.

### 8.3 archive 보존 정책

`.wily/archive/`는 wily가 안 만짐. 박사님이 참조용으로만 사용. 새 wily의 어떤 명령도 archive를 읽지 않음 (단 brownfield init 시 1회 분석만).

---

## 9. 폐기 목록

### 9.1 v2 명령 → 새 v3에서 빠짐

| 폐기 | 사유 |
|------|------|
| `wily run` | cw 직접 호출 안 함 (D3) |
| `wily retry` | attempt 개념 폐기 |
| `wily decompose-stage` | 분해 안 함 (D2) |
| `wily issues` | 별도 — 필요 시 추후 |
| `wily clean` | 정리할 임시 파일 자체가 적음 |
| `wily update` | 별도 plugin 업데이트 메커니즘 사용 |
| `wily board check` / `wily board check --probe` | board 폐기 (D7) |
| `wily live-heartbeat` / `wily live-worked` / `wily live-event` | board 폐기 |

### 9.2 v2 스킬 → 새 v3에서 빠짐

옛 16개 (`wily-block`, `wily-clean`, `wily-complete`, `wily-decompose-stage`, `wily-init`, `wily-issues`, `wily-land`, `wily-next`, `wily-replan`, `wily-retry`, `wily-run`, `wily-start`, `wily-status`, `wily-update`, `wily-watch`, `wily-workflow`) 전부 폐기.

새 11개:
- 명령별 10개: `wily-init`, `wily-next`, `wily-claim`, `wily-go`, `wily-done`, `wily-block`, `wily-replan`, `wily-land`, `wily-watch`, `wily-status`
- 메타 가이드 1개: `wily-execute`

각 새 스킬은 v3 명령에 정확히 1:1 매핑. 이름이 v2와 겹치는 경우(`wily-init`, `wily-block`, `wily-replan`, `wily-land`, `wily-watch`, `wily-status`)는 내용 전면 재작성.

### 9.3 board 관련 코드/자산 일괄 폐기

- `plugins/wily-roadmap/scripts/wily.py`에서 board 관련 함수 전부 제거: `emit_board_live_event`, `_surface_emit_failure`, `_record_board_emit_result`, `probe_board_endpoint`, `command_board`, `read_board_last_emit` 등
- `_active_live_bridge_warning`, `_board_bridge_last_emit_line` 등 watch UI의 board 의존 부분 제거
- runners/, agent-handoffs/ 중 board 통신 관련 자산 archive 또는 삭제

---

## 10. 비기능 요구사항

### 10.1 코드 크기

v2 monolith `wily.py` 4244줄. v3 목표:
- 단일 파일 유지 가능. 단 3000줄 이하 권장 (board 코드 제거로 자연 감소).
- 또는 모듈 분리: `wily/` 패키지로 명령별 파일. Codex가 선택.

### 10.2 의존성

- Python 표준 라이브러리만으로 동작 (yaml 파싱은 PyYAML 허용, 기존 v2와 동일).
- rich, prompt_toolkit 등 watch UI 의존성은 기존 .venv-watch 그대로 활용.
- 외부 네트워크 호출 0 (git fetch 외).

### 10.3 테스트

- 새 명령마다 단위 테스트.
- 마이그레이션은 fixture (`.wily/` v2 더미 1개)로 e2e 테스트.
- v2 호환성 테스트는 없음 (전면 교체).

### 10.4 호환성

- 옛 명령은 wily v3에서 호출 시 명시적 에러:
  ```
  $ wily run T01
  Error: 'run' is removed in wily v3. Use 'wily claim' + 'wily go' instead.
  See wily-execute skill for the new workflow.
  ```
- 옛 명령 호출 → exit code 2 (usage). 사일런트 fallback 안 함.

---

## 11. Codex 구현 시 결정해도 되는 항목 (open)

이 spec이 강하게 박는 부분이 아닌, 구현 디테일:

- `wily.py` 단일 파일 유지 vs 모듈 분리 — Codex가 가독성 기준으로 결정.
- `init` 인터뷰 질문의 정확한 문구 — 위 4.1 구조만 지키면 됨.
- `progress.jsonl` 파싱 시 깨진 줄 처리 정책 — best-effort (warn + skip) 권장.
- watch UI의 색상 팔레트 — 기존 v2 watch 유지하면 됨.
- task id 자동 부여 알고리즘 — `init add-task` 시 다음 빈 id 찾기. 단순한 max+1로 충분.
- 마이그레이션 시 옛 stage id → 새 task id 자동 매핑 알고리즘 — 박사님이 init 단계에서 승인하니 단순 1:1 (s01→T01) 기본값.
- `wily attribute <commit-sha> <task-id>` — 라이트 `observed (unmatched)` commit을 박사님이 수동으로 task에 매핑하는 명령. v3 출시에 포함할지, v3.1로 미룰지는 Codex가 구현 부하 보고 결정. 포함 시 명령 표면 11개로 늘어남.

이 외 spec에 명시된 결정은 흔들지 말 것.

---

## 12. 출구 조건 (Done Definition for the redesign itself)

다음이 모두 충족되면 v3 출시:

1. `plugins/wily-roadmap/scripts/wily.py` (또는 새 패키지) 가 10개 명령 + init 서브명령 다 구현.
2. `plugins/wily-roadmap/skills/` 에 11개 v3 스킬 작성.
3. v2 명령·스킬·board 코드 전부 제거.
4. 마이그레이션 명령(`wily init --adopt`)이 기존 박사님 레포(이 repo) 위에서 통째로 옛 .wily/를 archive하고 새 `.wily/` 생성하는 e2e가 박사님 손에서 통과.
5. `wily init` greenfield e2e가 빈 디렉토리에서 project.md + tasks.yaml 생성까지 통과.
6. `wily watch`가 협업 모드에서 박사님 + 라이트 lane을 정상 표시 (라이트 commit fixture로 verify).
7. `~/.codex/hooks.json` 정리 안내, 마켓플레이스 manifest 갱신 완료.
8. 새 wily 안에 board 호출 코드 0줄.

---

## 13. 이 spec 범위 밖

- **wily-board v2 폐기 및 신 board 재설계** — 별도 spec. 새 wily는 board 안 씀.
- **secret rotation (P6 핸드오프)** — 별도 작업. 폐기되는 wily-board 서비스의 secret는 더 이상 사용 안 함.
- **외부 LLM 통합** — 새 wily는 LLM API 호출 없음. 박사님이 Claude/Codex 안에서 wily 명령을 굴리는 모델.
- **GitHub Issues 통합 (`wily issues`)** — v3에서 폐기, 추후 별도 항목으로 검토 가능.
