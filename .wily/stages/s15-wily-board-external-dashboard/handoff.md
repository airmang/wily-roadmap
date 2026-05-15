# Handoff

Read `docs/wily-board-plan.md` first. The plan defines the product intent, stack, data model, auth model, sync loop, PR write model, and owner split.

Important boundary:

- Wily source of truth stays in each repository's `.wily/` files.
- Wily Board is a separate `wily-board` web application, not a feature inside the `wily-roadmap` plugin.
- The dashboard may create GitHub PRs, but it must not directly push to target repositories.

