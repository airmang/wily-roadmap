---
name: wily-init
description: Use when the user types $wily-init or asks to start the Wily v3 interview, greenfield or brownfield adopt.
---

# Wily Init

Start or continue the Wily v3 interview and write `.wily/project.md`, `.wily/tasks.yaml`, `.wily/actors.yaml`, plus concise repo-local Wily guidance in `AGENTS.md` and `CLAUDE.md`.

## Internal Command

```bash
python3 <plugin-root>/scripts/wily.py init [--new|--adopt|answer|back|revise|show|suggest|add-task|revise-task|drop-task|assign|commit|cancel|adopt-legacy]
```

## Behavior

- State-changing: stores interview draft in `.wily/init/draft.yaml`.
- `commit` creates or updates only the Wily-managed sections in root `AGENTS.md` and `CLAUDE.md`; existing project guidance is preserved.
- `adopt-legacy` archives old v2 `.wily/` children under `.wily/archive/`.

## Response Style

- Use Korean when the user is speaking Korean.
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
- Do not echo internal helper commands in normal user-facing responses.
