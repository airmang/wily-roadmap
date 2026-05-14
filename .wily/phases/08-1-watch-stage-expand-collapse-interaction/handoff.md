# Handoff

Start by designing the interaction contract.

Recommended direction:

- Keep `--once` non-interactive.
- Add an internal watch state object that tracks expanded/collapsed stage IDs or the leading done summary.
- Parse terminal mouse escape events in a small pure helper so tests can feed fixture strings.
- Add keyboard fallback before relying on mouse-only behavior.
- Make footer text reflect current state, for example `click/d expand done · r refresh · q quit`.
