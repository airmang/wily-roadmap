# T05: custom-workflow checkpoint가 Roadmap에 보이지 않은 원인

## 대조 결과

T04 실행 중 custom-workflow 진행 기록은 다음 Markdown 파일에 남았다.

- `agent-handoffs/t04-parallel-watch-progress.md`
- `agent-handoffs/t04-parallel-watch-status.md`
- `agent-handoffs/t04-parallel-watch-verification.md`

반면 Wily Roadmap이 watch checkpoint를 계산할 때 읽는 파일은 다음 JSONL ledger다.

- `.wily/tasks/T04/progress.jsonl`

T04 완료 직후 이 파일은 0바이트였고, `.wily/tasks/T04/result.md`도 `cp count: 0/0`로 기록했다.

## 원인

단절 지점은 watch renderer가 아니라 Wily/custom-workflow handoff 계약이다.

- `wily watch`는 `cp_summary()`를 통해 `.wily/tasks/<id>/progress.jsonl`만 읽는다.
- `wily go`는 custom-workflow에게 "append one JSON line per cp start/done"이라고 말했지만, 안정적인 CLI 명령이나 예시를 제공하지 않았다.
- `wily-execute`는 custom-workflow가 cp event를 append한다고 가정했지만, custom-workflow의 실제 runtime contract는 `agent-handoffs/*-progress.md`와 `*-status.md`를 유지하는 것이다.

결과적으로 T04의 checkpoint는 custom-workflow Markdown에는 남았지만 Wily JSONL ledger에는 쓰이지 않았고, watch는 표시할 cp가 없었다.

## 해결 방향

Wily가 로컬 진행 ledger의 소유자여야 한다. custom-workflow나 일반 agent가 JSONL을 직접 편집하게 하지 않고, 명시적인 Wily CLI로 checkpoint를 기록하게 한다.

- `wily cp <task-id> start <cp-name>`
- `wily cp <task-id> done <cp-name>`
- `wily cp <task-id> note <cp-name> --note <text>`
- `wily cp <task-id> import-status <agent-handoffs/...-status.md>`

`import-status`는 custom-workflow status board를 보수적으로 파싱해서 `DONE` checkpoint는 `start`+`done`, `RUNNING`/`VERIFYING`/`PARTIAL`/`BLOCKED` checkpoint는 `start`로 변환한다. 같은 이벤트를 중복으로 추가하지 않아 재실행 가능해야 한다.
