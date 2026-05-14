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
