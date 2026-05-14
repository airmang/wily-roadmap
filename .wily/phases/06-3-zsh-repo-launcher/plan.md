# Implementation Plan

Detailed plan: `docs/superpowers/plans/2026-05-12-wily-zsh-repo-launcher.md`

## Summary

- Add a checked-in root `./wily` zsh wrapper that delegates to `scripts/wily.py`.
- Keep the current working directory as the target repository.
- Document `./wily status` and `./wily watch` usage without modifying shell startup files or PATH.
- Add focused tests for wrapper behavior, safety boundaries, and documentation.
