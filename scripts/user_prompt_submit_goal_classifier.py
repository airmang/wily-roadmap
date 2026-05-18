#!/usr/bin/env python3
"""Compatibility no-op for stale Claude Code UserPromptSubmit hooks.

Wily v3 does not classify or block user prompts from hooks. Some existing local
Claude Code configs still call this repo-relative script, so it must exist and
return success until those hooks are removed.
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        sys.stdin.read()
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
