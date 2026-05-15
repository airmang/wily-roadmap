# Wily Status

Roadmap version 16 has Stage s15 in a blocked state.

Current baseline:
- `R-W-LAB/wily-board` exists as a private repository and has the local FastAPI/SQLite/htmx implementation pushed.
- Child Phases 15-1, 15-3, 15-4, 15-5, and 15-6 are implemented and verified locally.
- Child Phase 15-2 is blocked because `ssh airman@20.17.177.129` returns `Connection refused` on port 22. The host is reachable on ports 80 and 443.
- Child Phase 15-7 opened draft workflow PRs for all four initial repositories and configured `WILY_BOARD_URL` plus `WILY_BOARD_SECRET` secrets, then blocked until Azure SSH access and remaining live credentials exist.
- Stage s14 is done; child Phase 14-2 remains superseded by user request.

Next action:
- Restore SSH access to `20.17.177.129:22` or provide the correct SSH host/port/user. The current evidence points to SSH service/port/firewall/NSG configuration, not a dead host.
- Provide GitHub OAuth App and GitHub App credentials before live onboarding and PR-writing verification.
- Workflow PRs now have required `WILY_BOARD_URL` and `WILY_BOARD_SECRET` repo secrets available:
  - `R-W-LAB/wily-roadmap#2`
  - `R-W-LAB/Digit#4`
  - `R-W-LAB/mac2win#187`
  - `R-W-LAB/BounceBall#55`
