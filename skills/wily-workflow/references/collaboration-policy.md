# Wily Collaboration Policy

Use this policy when a repository shares Wily roadmap state through Git.

## Shared Source Of Truth

Commit these files so every collaborator sees the same roadmap:

- `.wily/roadmap.yaml`
- `.wily/project.md`
- `.wily/decisions.md`
- `.wily/status.md`
- `.wily/phases/**`
- `.wily/revisions/**`

These files are project coordination state. They record phase definitions, dependencies, replans, and durable decisions.

## Local-Only Execution Traces

Keep these local by default:

- `.wily/sessions/**`
- active runner handoff files
- personal scratch logs, caches, and transient artifacts

Sessions are attempt logs. They may contain local paths, stale pointers, or high-volume output. Share a summarized result through `roadmap.yaml`, phase notes, revision files, or a later explicit archive policy instead of committing every active session.

## Collaboration Loop

Before starting work:

1. Pull the latest branch.
2. Inspect `$wily-status` or `$wily-next`.
3. Choose a phase that is ready and not already owned in the shared roadmap or team channel.
4. Start the phase and, when collaboration requires visibility, commit/push the `in_progress` roadmap change before doing long work.

While working:

- Work on one phase at a time unless the roadmap explicitly marks safe parallel phases.
- Keep code changes and Wily state changes in the same branch when practical.
- Do not rewrite completed phase history to resolve conflicts.

When finishing:

1. Record verification evidence in the local session.
2. Mark the phase complete only after implementation and verification are done.
3. Commit code changes with shared Wily state changes.
4. Push only when the user has asked for remote updates.

## Conflict Rules

If `.wily/roadmap.yaml` conflicts:

- Preserve all completed phases unless the user explicitly approves a correction.
- Preserve newer replans and revision files when possible.
- Merge status changes by phase id rather than by file chunk.
- If two people claimed the same phase, stop and ask the user or team which attempt should continue.

## Current Session Pointers

`current_session` is useful locally, but may point to a session path another collaborator does not have. Treat it as an audit pointer, not required shared state. If it becomes noisy in collaboration, prefer a future phase that separates shared phase status from local session pointers.
