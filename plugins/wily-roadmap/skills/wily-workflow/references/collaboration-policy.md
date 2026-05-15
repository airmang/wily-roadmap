# Wily Collaboration Policy

Use this policy when a repository shares Wily roadmap state through Git.

## Shared Source Of Truth

Commit these files so every collaborator sees the same roadmap:

- `.wily/roadmap.yaml`
- `.wily/project.md`
- `.wily/decisions.md`
- `.wily/status.md`
- `.wily/stages/**`
- `.wily/phases/**`
- `.wily/revisions/**`

These files are project coordination state. They record Stage definitions, Phase definitions, dependencies, replans, and durable decisions. Legacy phase-only repositories may still use `.wily/phases/**`.

For visible collaboration claims, store compact Stage assignment metadata in `.wily/roadmap.yaml`:

- `owner`, `assignee`, or `assigned_to` records who currently owns the Stage.
- `task` or `assignment` records the specific task being handled.
- `write_scope` records the files or modules the Stage expects to touch.

`$wily-watch` renders those fields as compact `@name` and `task ...` details so collaborators can see who is doing what without reading local session logs.

## Local-Only Execution Traces

Keep these local by default:

- `.wily/sessions/**`
- active runner handoff files
- personal scratch logs, caches, and transient artifacts

Sessions are attempt logs. They may contain local paths, stale pointers, or high-volume output. Share a summarized result through `roadmap.yaml`, Stage notes, revision files, or a later explicit archive policy instead of committing every active session.

## Collaboration Loop

Before starting work:

1. Pull the latest branch.
2. Inspect `$wily-status` or `$wily-next`.
3. Choose a Stage that is ready and not already owned in the shared roadmap or team channel.
4. Check `write_scope` against other ready or in-progress Stages before parallel work.
5. Start the Stage and, when collaboration requires visibility, commit/push the `in_progress` roadmap change before doing long work.

While working:

- Work on one Stage at a time unless the roadmap explicitly shows safe parallel Stages with non-overlapping `write_scope`.
- Keep Stage-local decomposition under `.wily/stages/<stage-id>/stage.yaml` so different Stage owners do not edit the same roadmap chunk.
- Keep code changes and Wily state changes in the same branch when practical.
- Do not rewrite completed Stage or phase history to resolve conflicts.

When finishing:

1. Record verification evidence in the local session.
2. Mark the Stage or phase complete only after implementation and verification are done.
3. Commit code changes with shared Wily state changes.
4. Push only when the user has asked for remote updates.

## Conflict Rules

If `.wily/roadmap.yaml` conflicts:

- Preserve all completed Stages and phases unless the user explicitly approves a correction.
- Preserve newer replans and revision files when possible.
- Merge status changes by Stage or phase id rather than by file chunk.
- If two people claimed the same Stage or phase, stop and ask the user or team which attempt should continue.

## Current Session Pointers

`current_session` is useful locally, but may point to a session path another collaborator does not have. Treat it as an audit pointer, not required shared state. If it becomes noisy in collaboration, prefer a future phase that separates shared phase status from local session pointers.
