# Phase 06-2: Claude Code 호환성 확보

## Purpose

Wily plugin workflow가 Codex뿐 아니라 Claude Code에서도 이해 가능하고 실행 가능한 형태로 동작하도록 호환성 지침과 명령 경로를 정리한다.

## Expected Starting Conditions

- Phase 05 is done.
- Plugin discovery and skill command entrypoints are documented.

## Likely Files

- `skills/wily-*/SKILL.md`
- `skills/wily-workflow/references/`
- `.codex-plugin/plugin.json`
- `README.md` or plugin documentation if present
- `tests/test_wily_command_skills.py`

## Completion Criteria

- Claude Code에서 사용할 때 필요한 command invocation, skill mapping, local-first boundary가 문서화된다.
- Codex 전용 표현이 있으면 플랫폼 중립 표현으로 정리된다.
- 기존 Codex plugin discovery compatibility는 유지된다.
- 테스트가 핵심 문서 문구와 plugin metadata를 검증한다.

## Known Risks

- Claude Code와 Codex의 tool naming 차이를 과하게 추상화하면 실제 사용 지침이 흐려질 수 있다.
- Codex plugin discovery 파일 구조를 깨면 안 된다.
