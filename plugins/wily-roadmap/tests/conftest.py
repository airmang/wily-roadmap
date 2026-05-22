"""Test-suite isolation for the bundled wily-agent.

Several CLI paths -- `wily init commit` (`_best_effort_agent_register`) and the
`wily agent` commands -- resolve the agent config, registry, plist, and log
paths from `default_paths()`, which defaults to the developer's real
`~/.config/wily/agent/`. Without isolation, running the suite registers test
tempdirs into the developer's live registry and can rewrite their launchd
plist.

`default_paths()` honours the `WILY_AGENT_*` environment variables, and test
subprocesses inherit `os.environ`, so pointing those variables at a throwaway
directory for the whole session makes every CLI path -- in-process and
subprocess -- hermetic.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_WILY_AGENT_ENV = {
    "WILY_AGENT_CONFIG": "agent/config.json",
    "WILY_AGENT_REGISTRY": "agent/registry.json",
    "WILY_AGENT_SYNC_HEALTH": "agent/sync-health.json",
    "WILY_AGENT_PLIST": "agent/com.wily.roadmap.agent.plist",
    "WILY_AGENT_LOG_DIR": "agent/logs",
}


@pytest.fixture(scope="session", autouse=True)
def isolate_wily_agent_paths():
    """Redirect every WILY_AGENT_* path into a session-scoped temp directory."""
    with tempfile.TemporaryDirectory(prefix="wily-agent-test-") as tmp:
        base = Path(tmp)
        previous = {key: os.environ.get(key) for key in _WILY_AGENT_ENV}
        for key, relative in _WILY_AGENT_ENV.items():
            os.environ[key] = str(base / relative)
        try:
            yield base
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
