# Notes

Created by replan 14 from `docs/wily-board-plan.md`.

Plan review:

- The architecture is coherent for a 1 GiB Azure VM: Caddy, one FastAPI worker, SQLite, and htmx keep memory use low.
- The SoT rule is sound: `.wily/` files remain authoritative, while the board keeps a cache and writes through PRs.
- GitHub OAuth plus a two-person whitelist is a pragmatic first auth model.
- The first write action should stay limited to status toggle PRs until collision patterns are known.
- Direct dashboard pushes, background LLM loops, Docker, and broad app integrations should stay out of scope for the first implementation.

Open decisions before live deployment:

- Confirm Light's GitHub account status.
- Choose org/repo name and `wily-board` visibility.
- Choose the DuckDNS hostname.
- Create OAuth and GitHub App credentials.

