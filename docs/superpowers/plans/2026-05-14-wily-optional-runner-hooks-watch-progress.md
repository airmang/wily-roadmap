# Wily Optional Runner Hooks and Watch Progress Plan

## Goal

Finish the bundled runner follow-up by adding opt-in hook helper behavior and lightweight `wily-watch` runner progress visibility without making hooks required for core Wily commands.

## Scope

1. Keep hooks opt-in
   - Leave bundled hook installation disabled by default.
   - Document concrete optional hook entrypoints in `runners/custom-workflow/hooks/hooks.json`.
   - Make hook helper scripts deterministic and safe to run manually or from an opt-in hook config.

2. Add optional runner hook helpers
   - Add PostToolUse-style verification capture helper that appends event evidence to runner verification artifacts.
   - Add Stop-style guard helper that reads Wily session status, runner metadata, and autonomy mode to decide whether continuation should be allowed.
   - Keep remote/destructive policy approval-first through explicit helper output, not automatic enforcement.

3. Add `wily-watch` runner progress display
   - Read stable session runner artifacts from `.wily/sessions/<session>/runner/`.
   - Show compact runner status next to a phase when a current session has runner progress.
   - Do not require runner artifacts for normal watch rendering.

4. Tests
   - Verify hook manifest stays opt-in and points to helper scripts.
   - Verify evidence capture updates both session runner verification and active handoff verification when available.
   - Verify stop guard reads autonomy/status and reports a continuation/block decision.
   - Verify watch output shows runner progress from session artifacts.

## Non-Goals

- Do not auto-install hooks.
- Do not add MCP servers or app integrations.
- Do not make hooks required for `wily-run`, `wily-complete`, or `wily-watch`.
- Do not perform remote writes.
