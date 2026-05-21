# Wily Roadmap Marketplace Agent Guide

## Scope

This file governs the marketplace repository root.

## Project Intent

This repository publishes Wily Roadmap as a Codex plugin marketplace. Keep marketplace metadata at the repository root and keep the plugin implementation under `plugins/wily-roadmap/`.

## Rules

- Keep `.agents/plugins/marketplace.json` present and pointing to `./plugins/wily-roadmap`.
- Keep the plugin manifest at `plugins/wily-roadmap/.codex-plugin/plugin.json`.
- Keep plugin behavior local-first and approval-first for remote actions.
- Do not add hooks, MCP servers, or app integrations until the user explicitly asks for that layer.

## Wily Roadmap

- Treat `.wily/` as the local project/task ledger.
- Prefer `wily next`, `wily claim <id>`, `wily go <id>`, `wily done <id>`, and `wily watch` for Wily-managed work.
- When using Custom Workflow, sync checkpoint status back with `wily cp <id> import-status .wily/handoffs/<id>/status.md`.
- Keep remote or destructive actions approval-first.

## Agent Behavior

- State assumptions when requirements are ambiguous.
- Choose the simplest implementation that satisfies the task.
- Keep edits surgical; do not refactor unrelated code.
- Define success with tests or concrete verification before calling work done.
