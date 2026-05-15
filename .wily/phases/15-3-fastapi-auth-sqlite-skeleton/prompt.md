# Execution Prompt

Implement the Wily Board backend skeleton.

Scope:

- Add FastAPI app setup, config loading, SQLite schema and repository helpers.
- Add `/healthz`, `/`, `/repos/{owner}/{name}`, and auth start/callback routes.
- Implement GitHub OAuth and whitelist session logic with testable seams.
- Add tests for schema creation, webhook signature helper if introduced, and OAuth callback behavior using mocks.

Do not implement sync ingestion or PR-writing in this phase.

