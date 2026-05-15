# Phase 15-1: Wily Board repository and contract baseline

## Purpose

Establish `wily-board` as a separate web application with explicit boundaries, project structure, and implementation assumptions derived from `docs/wily-board-plan.md`.

## Dependencies

- Stage s14 complete, because Wily Board depends on the Stage/Phase state model being stable enough to consume.

## Expected Output

- A separate `wily-board` repository or local implementation workspace is created or prepared.
- README and project metadata state that Wily Board is a cache and PR-writing dashboard, while `.wily/` files remain the source of truth.
- The chosen Python/FastAPI/SQLite/htmx stack is captured in project scaffolding.
- The unresolved operator decisions are listed before deployment work begins.

## Likely Files

- `wily-board/README.md`
- `wily-board/pyproject.toml`
- `wily-board/app/`
- `wily-board/tests/`

## Known Risks

- Implementing inside `wily-roadmap` would blur plugin and dashboard lifecycles.
- Creating a remote repository requires explicit user approval.
- GitHub org, visibility, and credential choices may block later phases.

