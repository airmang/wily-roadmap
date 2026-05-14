# Wily Runner Adapter Contract Implementation Plan

## Goal

Define the first stable runner adapter contract and bundled Custom Workflow manifest without moving Custom Workflow implementation details into Wily core.

## Scope

1. Add `runners/custom-workflow/runner.yaml`
   - Keep it small and declarative.
   - Mark `custom-workflow` as the bundled default runner.
   - Record version, adapter version, entrypoint paths, capabilities, artifact paths, autonomy modes, and approval policy.

2. Add `skills/wily-workflow/references/runner-adapter-contract.md`
   - Explain Wily core vs runner responsibilities.
   - Define runner inputs, outputs, archive layout, status recommendations, and autonomy modes.
   - State that `goal_scoped` is the default and that remote/destructive actions require approval.

3. Update `skills/wily-workflow/SKILL.md`
   - Link the new contract reference.
   - Mention runner selection as a Wily responsibility without adding dispatch behavior yet.

4. Add focused tests
   - Verify the manifest exists and contains the stable contract fields.
   - Verify the workflow skill links the contract reference.

## Non-Goals

- Do not implement `wily-run`.
- Do not bundle Custom Workflow skill/agent/script files yet.
- Do not install hooks or add MCP/app integrations.
- Do not change existing Wily phase/session lifecycle behavior.
