# Board Coordination Operations Contract

This document is the Wily Roadmap side of the Board coordination deploy and
evidence contract. Board owns browser OAuth, machine registration, runtime task
transitions, and production deployment. Wily Roadmap owns local `.wily/` state
and the `wily-agent` snapshot and heartbeat payloads that Board ingests.

## Trust Boundaries

- Browser OAuth is for humans only. Operators authenticate to Board through the
  GitHub OAuth session cookie and the allowlist configured on Board.
- Machine tokens are for `wily-agent` only. A token is returned once by Board
  registration, stored locally by the agent, and sent only as
  `Authorization: Bearer <machine-token>` to Board agent endpoints.
- Wily Roadmap never writes OAuth secrets, browser session cookies, machine
  tokens, token peppers, bearer headers, private keys, or registration codes to
  handoffs, progress logs, screenshots, or git.
- Parent-owned coordination mode remains local-first. `.wily/tasks.yaml`,
  `.wily/coordination.yaml`, and task progress ledgers stay under the parent
  workspace; Board displays and caches them but does not directly write those
  files.

## Snapshot And Heartbeat Semantics

- Snapshots use the existing Board v3 payload with optional
  `active_mode=coordination` and `coordination` metadata.
- The coordination payload describes the parent project, child repos, display
  ownership hints, parent task roadmap, repo-qualified scope, child target
  summaries, and claim snapshot summaries.
- Heartbeats are presence signals. They may include checkout identity, branch,
  and local path, but they are not proof that task definitions changed.
- Snapshot and heartbeat delivery is best effort. Operators should verify Board
  ingest through the Board UI or API before treating production E2E as complete.

## Production Approval And Evidence

Production-affecting actions require explicit approval before they run. This
includes SSH writes, package installs, service restarts, Caddy reloads, database
backup or restore, OAuth callback changes, DNS changes, registration-code
issuance, and public machine onboarding.

Approved production E2E evidence should show:

- public OAuth login succeeds with auth bypass disabled;
- an agent snapshot is accepted;
- heartbeat presence updates;
- the coordination portfolio displays the parent workstream once;
- child repos are not duplicated in default workspace/global queue views;
- direct child repo routes remain addressable;
- portfolio lanes sort by latest activity;
- parent roadmap/detail shows scope, target repos, and claim snapshot summaries;
- heartbeat stability remains acceptable after refresh.

Evidence must be redacted. Record command names, timestamps, status codes, route
names, and screenshots without raw cookies, bearer tokens, OAuth secrets,
machine tokens, token peppers, private keys, or registration codes.

## Rollback And Stop Conditions

Use the Board deployment runbook as the production source of truth:
`wily-board/docs/DEPLOY.md`.

Stop and do not mark deploy/E2E complete when:

- production approval is unavailable;
- OAuth, snapshot ingest, heartbeat, direct child routes, or portfolio ordering
  cannot be verified;
- evidence would require storing a raw secret;
- rollback is needed or has been performed;
- repeated verification failures occur without new diagnostic evidence.

If local implementation passes but production approval is unavailable, parent UI
work can be recorded complete while deploy/E2E remains partial or blocked.
