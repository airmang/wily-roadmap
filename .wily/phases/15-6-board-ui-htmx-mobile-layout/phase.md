# Phase 15-6: Board UI views, htmx interactions, and mobile layout

## Purpose

Implement the server-rendered dashboard UI for all repositories, repository detail, Stage detail, filters, Phase cards, htmx partials, mobile layout, and dark mode.

## Dependencies

- 15-3 FastAPI auth and SQLite skeleton

## Expected Output

- `/` renders all-board kanban or list views with repo, owner, and status filters.
- `/repos/{owner}/{name}` renders a Stage tree with child Phases.
- `/repos/{owner}/{name}/stages/{id}` renders one Stage detail.
- Phase cards show status, id, title, owner, task, and current session.
- htmx partials update filters and status action responses.
- Mobile layout works under 600px with compact cards.

## Likely Files

- `app/web/routes.py`
- `app/web/templates/base.html`
- `app/web/templates/board.html`
- `app/web/templates/repo_detail.html`
- `app/web/templates/stage_detail.html`
- `app/web/templates/phase_card.html`
- `app/web/static/app.css`
- `tests/test_web_routes.py`

## Known Risks

- UI should preserve the Stage/Phase two-level language from Wily watch instead of inventing a third hierarchy.
- htmx status toggles depend on Phase 15-5 for live write behavior, but read-only UI can be built earlier with fixtures.

