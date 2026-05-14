# Wily Runner Artifact Archive and Review Handoff Plan

## Goal

Finish the runner archive lifecycle so `wily-run` dispatch artifacts remain durable in the Wily session after execution, block, review, and completion flows.

## Scope

1. Preserve runner metadata during final status transitions
   - Keep the `runner:` block in `.wily/sessions/<session>/status.yaml` when `wily complete` or `wily block` rewrites the session status.
   - Record final archive metadata without changing older session formats incompatibly.

2. Snapshot runner artifacts at finalization
   - Copy current runner-native `agent-handoffs/<slug>-*.md` files back into `.wily/sessions/<session>/runner/`.
   - Run this snapshot on verified completion and block transitions.
   - Keep dispatch-time snapshots intact for sessions that never finalize.

3. Add review handoff guidance
   - Generate a runner review handoff artifact that explains `needs_review`, `blocked`, and verified completion outcomes.
   - Store it in both `agent-handoffs/` and the session runner archive.
   - Include the artifact path in runner metadata.

4. Tests
   - Prove `wily-run` creates the review handoff and session archive.
   - Prove `wily complete` preserves runner metadata and snapshots updated runner artifacts.
   - Prove `wily block` snapshots updated runner artifacts and records blocked archive metadata.
   - Keep existing proof that `wily-run` does not mark phases done.

## Non-Goals

- Do not execute the runner automatically.
- Do not add hooks or MCP/app integrations.
- Do not introduce a new review state command in this phase.
- Do not rewrite existing completed Wily session history.
