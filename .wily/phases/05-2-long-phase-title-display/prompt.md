# Execution Prompt

Review and improve how long Phase titles are displayed when they currently become `...`.

Scope:
- Find where title truncation happens in status and watch output.
- Compare practical options: wrapping, middle truncation, preserving full title in a detail line, or width-aware fallback.
- Add focused tests before implementation.
- Keep terminal output stable and readable.
