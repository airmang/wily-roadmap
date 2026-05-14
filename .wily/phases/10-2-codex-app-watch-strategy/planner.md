# Planner

Start with a short investigation before implementation planning.

Questions to answer:

- Codex app에서 `tmux` pane을 기대해도 되는가?
- Codex in-app browser or app surface를 watch companion으로 쓸 수 있는가?
- Watch는 continuous UI가 필요한가, 아니면 app 환경에서는 periodic snapshot이 더 좋은가?
- Current `wily watch --once` output is good enough for app updates, or needs a compact mode?

After the investigation, use `superpowers:writing-plans` if code changes are needed.
