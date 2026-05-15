# Execution Prompt

Implement Wily Board's first write action.

Scope:

- Add GitHub App authentication for PR creation.
- Implement safe Phase status YAML replacement for `.wily/stages/**/stage.yaml`.
- Create a branch, commit, and PR titled `chore(wily): set <phase-id> -> <status> (via board)`.
- Add route or handler for htmx status toggle requests.
- Record audit events.

Do not directly push to target branches. Do not enable auto-merge.

