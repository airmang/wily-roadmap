# Verification

Use child Phase verification guidance.

Stage-level acceptance:

- `wily-board` exists as a separate deployable web app or implementation branch.
- The app can ingest `.wily/` state from at least `wily-roadmap`.
- The app can render board/list views on mobile.
- The first write action creates a GitHub PR rather than directly pushing.
- Deployment artifacts fit the Azure 1 GiB RAM constraint.

