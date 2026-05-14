# Execution Prompt

Implement Korean stage-based DAG output for `wily-status`.

Scope:
- Keep `.wily/roadmap.yaml` status values in English.
- Translate only user-facing status output.
- Replace `All phases:` list with a `Phase 흐름:` or equivalent stage-based DAG section.
- Keep output stable for tests.
- Do not add external renderer dependencies.
