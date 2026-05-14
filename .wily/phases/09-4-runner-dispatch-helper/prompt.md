# Execution Prompt

Implement runner dispatch for `wily-run`.

Scope:
- Validate phase exists and is executable.
- Resolve runner and autonomy mode.
- Start or attach session using existing lifecycle behavior where possible.
- Build phase context bundle.
- Create runner-native handoff files and session runner input.
- Never mark a phase `done` directly from dispatch.
