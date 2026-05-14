# External Workflow Reference

Wily Roadmap owns durable roadmap memory, phase lifecycle, dependency checks, attempts, status transitions, replans, and completion history.

External workflows such as Custom Workflow may execute a selected phase, but they are not bundled into Wily and are not required for core Wily behavior. Wily uses them by reference only.

## Handoff Contract

`$wily-run` creates a reference-only external workflow handoff with:

- phase id and title
- phase path and phase files
- roadmap context
- current Wily session path
- selected external workflow label
- autonomy mode label
- suggested native `/goal` command
- completion, review, and blocker instructions

The handoff is written to `agent-handoffs/` for external workflow use and copied into the active Wily session for audit history.

## External Workflow Output

An external workflow may produce:

- result summary
- verification evidence
- changed files
- progress log
- blocker text, if blocked
- recommended phase status: `needs_review`, `blocked`, `ready`, or `done`
- raw artifacts useful for audit

The external workflow must not mark Wily phases done directly. Final completion still requires Wily verification evidence and `$wily-complete`.

## Autonomy Modes

Wily owns the autonomy policy label passed to external workflows.

`conservative`:

- local edits use normal agent judgment
- remote actions require explicit approval
- destructive actions require explicit approval
- push, PR, merge, and GitHub comments require explicit approval

`goal_scoped`:

- local implementation and verification may continue within the approved phase
- dependency installs may proceed when clearly phase-scoped and non-destructive
- remote actions require explicit approval
- destructive actions require explicit approval

`yolo`:

- only for explicit autonomous runs in safe repositories
- hard stops still apply for broad destructive commands, payments, credential exposure, forbidden actions, and repeated verification failure without new evidence

Do not inherit an external workflow's more permissive default unchanged.

## Policy

- Use Custom Workflow and similar systems as external references only.
- Do not bundle external workflow implementation files inside Wily.
- Do not require hooks, MCP servers, or app integrations for core Wily behavior.
- Remote and destructive actions remain approval-first.
- Preserve current plugin discovery compatibility through `.codex-plugin/plugin.json` and top-level `skills/`.
- Use top-level wrapper skills only when direct plugin discovery requires them.
