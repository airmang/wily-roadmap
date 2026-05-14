# Phase 07-1: GitHub Issues 선택적 연동 계약 정의

## Purpose

Wily roadmap이 GitHub Issues를 사용하는 협업 프로젝트와 연결될 수 있도록 선택적 linkage 계약을 정의한다. GitHub Issues를 쓰지 않는 프로젝트에서는 기존 local-first Wily 흐름이 그대로 동작해야 한다.

## Dependencies

- 06-3 zsh repo launcher
- 06-4 mature repo init contract
- 06-5 watch pane compaction

## Parallel Group

07

## Expected Starting Conditions

- Phase 06 work is done.
- Wily remains local-first and approval-first for remote actions.
- GitHub Issues are not assumed to exist for every project.

## Expected Output

- Wily phase metadata에서 GitHub issue 번호/URL을 선택적으로 표현하는 계약이 문서화된다.
- GitHub Issues와 Wily phase/session의 source-of-truth 경계가 명확해진다.
- GitHub issue 조회가 자동 기본 동작이 아니라 explicit request 또는 별도 command skill 후보임이 정리된다.
- GitHub 없는 프로젝트에서 영향이 없다는 테스트/문서 계약이 생긴다.

## Likely Files

- `skills/wily-workflow/SKILL.md`
- `skills/wily-workflow/references/`
- `skills/wily-next/SKILL.md`
- `tests/test_wily_command_skills.py`
- `.codex-plugin/plugin.json` only if new command skill metadata is added

## Known Risks

- GitHub 조회를 기본 command path에 넣으면 GitHub를 쓰지 않는 프로젝트가 느려지거나 불필요한 remote dependency를 갖게 된다.
- Issue body를 Wily state에 복제하면 두 source of truth가 충돌할 수 있다.
- GitHub API/CLI 호출은 remote inspection이므로 approval-first 경계를 흐리면 안 된다.
