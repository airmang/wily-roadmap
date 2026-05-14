# Wily Plugin Agent Guide

## Scope

This file governs `plugins/wily-roadmap/`.

## Project Intent

This project contains Wily's personal Codex plugin. Keep it focused on reusable Codex workflow behavior, especially skills, references, scripts, and future plugin integrations.

## Rules

- Keep plugin behavior local-first and approval-first for remote actions.
- Keep skill bodies concise; move detailed policy into `references/`.
- Put deterministic repeated logic in `scripts/`.
- Do not add hooks, MCP servers, or app integrations until the user explicitly asks for that layer.
- Preserve compatibility with Codex plugin discovery: keep `.codex-plugin/plugin.json` and `skills/` in this plugin root.
