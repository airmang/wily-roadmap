# Execution Prompt

Archive runner artifacts into Wily sessions and connect review handoff.

Scope:
- Add `.wily/sessions/<session>/runner/` artifact snapshot behavior.
- Record actual runner metadata in session status.
- Preserve completed phase/session history.
- Keep final `done` gated by verification evidence and Wily completion.
