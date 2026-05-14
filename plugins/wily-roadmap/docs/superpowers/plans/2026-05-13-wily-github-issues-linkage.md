# Wily GitHub Issues Linkage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `$wily-issues` command that reads GitHub Issues, shows Wily linkage status, and can add approved local roadmap phases for unlinked issues.

**Architecture:** Keep Wily core commands GitHub-free. `$wily-issues` is explicit and optional: default mode is read-only issue discovery; `--add-to-roadmap` performs only local Wily roadmap mutation after user approval. Tests use fixture JSON via `WILY_ISSUES_JSON` instead of network calls.

**Tech Stack:** Python standard library CLI, Markdown command skill/reference docs, Python `unittest`.

---

## Tasks

- [ ] Add tests for `$wily-issues` read-only output, no-source fallback, and approved local roadmap additions.
- [ ] Implement `scripts/wily.py issues` with `WILY_ISSUES_JSON` fixture input and `gh issue list` fallback.
- [ ] Add `skills/wily-issues/SKILL.md` and `github-issues-policy.md`.
- [ ] Update workflow references and command skill tests.
- [ ] Run `python3 -m unittest tests.test_wily_cli tests.test_wily_command_skills`, `python3 -m unittest discover`, and `python3 -m py_compile scripts/wily.py`.
