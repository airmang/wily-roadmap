# Wily Mature Init Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define and test `$wily-init` behavior for mature repositories and partial or existing `.wily` state.

**Architecture:** Keep `init` deterministic and local-first: it repairs directories, preserves authored top-level Wily files, creates a minimal baseline when `.wily` is absent, and reports mature-repo hints without analyzing or overwriting user content. Skill guidance documents the contract so agents do the repository scan and goal question after the helper establishes state.

**Tech Stack:** Python standard library CLI, `unittest`, Markdown skill documentation.

---

## Tasks

- [ ] Add a CLI test proving mature-looking repos without `.wily` get baseline state plus an existing-project hint.
- [ ] Add a deterministic `mature_repo_hints(root)` helper in `scripts/wily.py`.
- [ ] Print existing-project hints from `command_init` without modifying remote state or shell configuration.
- [ ] Update `skills/wily-init/SKILL.md` with the mature repo contract.
- [ ] Run `python3 -m unittest tests.test_wily_cli`, `python3 -m unittest discover`, and `python3 -m py_compile scripts/wily.py`.
