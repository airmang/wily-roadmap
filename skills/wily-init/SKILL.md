---
name: wily-init
description: Use when the user types $wily-init or asks to initialize Wily roadmap state for the current repository.
metadata:
  short-description: Initialize Wily roadmap state
---

# Wily Init

Use `$wily-init` to create or refresh the project-level Roadmap Plan.

This is state-changing. It may create `.wily/`, write baseline project files, and define roadmap phases.

## First Move

1. Read applicable `AGENTS.md`.
2. Inspect the repository structure, docs, tests, and current `git status --short`.
3. If the user supplied a goal, use it. If not, summarize current state and ask for the intended final outcome.
4. Initialize local state with:

   ```bash
   python3 <plugin-root>/scripts/wily.py init "<goal>"
   ```

5. Build the Roadmap Plan in `.wily/roadmap.yaml` and phase skeletons under `.wily/phases/`.

## Boundaries

- Do not implement project code during init.
- Keep phase implementation plans delegated through `planner.md`.
- Ask before overwriting existing `.wily/` state.
