# Wily Collaboration State Sync Implementation Plan

## Goal

Make Wily Roadmap usable by two collaborators through Git by sharing durable roadmap state while keeping personal execution traces local.

## Design

1. Git tracking policy
   - Track `.wily/roadmap.yaml`, `.wily/project.md`, `.wily/decisions.md`, `.wily/status.md`, `.wily/phases/**`, and `.wily/revisions/**`.
   - Keep `.wily/sessions/**` ignored by default because active session paths and logs are personal execution traces.
   - Keep future runner transient artifacts local unless a later phase introduces a durable archive policy.

2. Workflow guidance
   - Add a collaboration policy reference under `skills/wily-workflow/references/`.
   - Keep the main workflow skill concise and link to the detailed reference.
   - Teach start/complete skills to nudge the user toward pull-before-work and commit/push-after-state-change without performing remote actions automatically.

3. Verification
   - Add a focused test proving shared `.wily` files are not ignored and sessions remain ignored.
   - Run Wily status/next smoke checks and focused CLI tests.

## Non-Goals

- Do not commit all `.wily/sessions/**`.
- Do not add remote automation or automatic pushes.
- Do not resolve multi-user roadmap conflicts automatically.
