# Execution Prompt

Implement Wily Board sync ingestion.

Scope:

- Verify webhook HMAC signatures.
- Fetch `.wily/` files from GitHub for a pushed SHA or manual resync target.
- Parse roadmap and stage YAML into repos, stages, phases, and events.
- Add a reusable workflow template for Wily repositories to notify the board.
- Prove the parser can ingest the current `wily-roadmap` Stage/Phase files.

Do not implement dashboard write actions in this phase.

