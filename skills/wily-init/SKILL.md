---
name: wily-init
description: Use when the user types $wily-init or asks to initialize Wily roadmap state for the current repository.
metadata:
  short-description: Initialize Wily roadmap state
---

# Wily Init

Use `$wily-init` to create or refresh the project-level Roadmap Plan.

This is state-changing. It may create `.wily/`, write baseline project files, and define roadmap phases.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py init "<goal>"
```

## First Move

1. Read applicable `AGENTS.md`.
2. Inspect the repository structure, docs, tests, and current `git status --short`.
3. If the user supplied a goal, use it. If not, summarize current state and ask for the intended final outcome before authoring roadmap phases.
4. Ensure local state exists with this internal helper command:

   ```bash
   python3 <plugin-root>/scripts/wily.py init "<goal>"
   ```

   If no goal is available yet, run `python3 <plugin-root>/scripts/wily.py init`; it creates baseline state, prints `Goal: needed`, and leaves the active agent responsible for the repository scan and goal question.

5. Build the Roadmap Plan in `.wily/roadmap.yaml` and phase skeletons under `.wily/phases/` only after the goal is clear.

## Roadmap Language

- Unless the user explicitly asks for another language, author Roadmap Plan content in Korean.
- Use Korean for phase titles and generated `phase.md`, `planner.md`, `verification.md`, and `handoff.md` prose.
- Keep YAML field names and status values in English for tool compatibility.

## Mature Repository Contract

- In a repository without `.wily/`, the helper creates baseline Wily state and reports existing project hints such as `README.md`, `scripts/`, `tests/`, `src/`, or common manifest files.
- Existing project hints are informational only. The active agent still scans the repository, summarizes the current implementation, and asks for the intended final outcome before authoring roadmap phases.
- In a partial `.wily/` state, the helper repairs required directories: `phases/`, `sessions/`, and `revisions/`.
- In an existing `.wily/` state, preserve user-authored `project.md`, `roadmap.yaml`, `status.md`, and `decisions.md`.

## Boundaries

- Do not implement project code during init.
- Keep phase implementation plans delegated through `planner.md`.
- The helper preserves existing top-level `.wily/` authoring files. Ask before overwriting existing `.wily/` state.

## Response Style

- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- If no goal is available, ask only for the intended final outcome after reporting baseline state.
