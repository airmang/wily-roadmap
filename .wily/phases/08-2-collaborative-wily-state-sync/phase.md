# Phase 08-2: 협업용 Wily state Git 동기화 정책

## Purpose

두 명 이상이 같은 Wily roadmap을 기준으로 프로젝트 진척도를 볼 수 있도록, `.wily/` 상태 중 어떤 파일을 Git으로 공유하고 어떤 파일을 로컬 실행 흔적으로 남길지 정책과 구현을 정한다.

## Background

현재 `.gitignore`는 `.wily/` 전체를 ignore한다. 이 상태에서는 `roadmap.yaml`, `phases/`, `revisions/`가 원격에 올라가지 않아 협업자가 phase 진행 상태를 pull로 동기화할 수 없다.

## Dependencies

- 07-1 GitHub Issues 선택적 연동 계약 정의
- 08-1 Watch pane Stage별 접기 펼치기 인터랙션

## Parallel Group

08

## Expected Output

- `.wily` Git tracking 정책 문서화
- `.gitignore` 조정: 공유 Wily state는 추적하고 로컬-only 실행 산출물은 제외
- 공유 후보:
  - `.wily/roadmap.yaml`
  - `.wily/project.md`
  - `.wily/decisions.md`
  - `.wily/status.md`
  - `.wily/phases/**`
  - `.wily/revisions/**`
- 로컬-only 후보:
  - active `.wily/sessions/**`
  - runner-native transient artifacts
  - 개인별 임시 로그나 cache
- 협업 workflow 문서화:
  - 작업 전 pull
  - phase 담당자 분리
  - 완료 시 roadmap/state와 코드 변경을 함께 commit
  - conflict 발생 시 completed history를 보존하며 해결
- 필요하면 `wily status` 또는 skill 문서에서 협업 모드 주의사항을 안내
- 테스트 또는 smoke check로 `.wily/roadmap.yaml` 파싱과 next/status 동작 확인

## Known Risks

- 두 사람이 동시에 `.wily/roadmap.yaml`을 수정하면 Git conflict가 난다.
- `current_session`은 다른 사람 환경에서 stale pointer가 될 수 있다.
- `.wily/sessions/**`를 모두 공유하면 커밋 노이즈와 충돌이 커질 수 있다.
- `.gitignore` negation rule은 순서가 중요해서 실수하면 공유 파일이 계속 ignored될 수 있다.
