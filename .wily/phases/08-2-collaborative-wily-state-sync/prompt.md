# Execution Prompt

Implement collaboration-safe Wily state syncing through Git.

Scope:
- Define which `.wily/` files are shared source of truth and which remain local-only.
- Update `.gitignore` so shared Wily roadmap files can be committed.
- Add or update Wily workflow documentation for two-person collaboration.
- Avoid committing active private session artifacts unless the policy explicitly requires it.
- Preserve completed phase history.
- Confirm `wily status` and `wily next` still parse the roadmap.
