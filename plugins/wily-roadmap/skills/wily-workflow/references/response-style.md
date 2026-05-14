# Response Style

Wily command skills distinguish internal execution from user-facing output.

## Shared Rules

- Do not echo internal helper commands in normal user-facing responses.
- Do not describe routine procedure such as reading files, running helper scripts, or checking generated context unless that detail changes the user's next decision.
- Use Korean when the user is speaking Korean, while keeping file paths, command names, status values, and machine-facing markers in English.
- Keep safety-critical approval requirements when they apply.
- If a command cannot complete, report the blocker and the smallest required user decision or approval.

## State-Changing Commands

- Report only the result, the relevant path or artifact, and the next action or blocker.
- Include changed roadmap/session state only when it helps the user decide what to do next.
- Do not continue into implementation after session-bookkeeping commands unless the user explicitly asks in a separate message.

## Read-Only Commands

- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Show manual fallback commands only when the user must run them outside the agent.
