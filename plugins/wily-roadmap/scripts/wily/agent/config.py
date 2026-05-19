"""Local configuration for the bundled wily-agent."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentPaths:
    config_path: Path
    registry_path: Path
    plist_path: Path
    log_dir: Path


@dataclass(frozen=True)
class AgentConfig:
    board_url: str = ""
    repo: str = ""
    actor: str = ""
    secret: str = ""
    token: str = ""
    machine_id: str = ""
    heartbeat_interval: int = 5

    @property
    def configured(self) -> bool:
        return self.snapshot_configured or self.live_configured

    @property
    def snapshot_configured(self) -> bool:
        return bool(self.board_url and self.token)

    @property
    def live_configured(self) -> bool:
        return bool(self.board_url and self.repo and self.actor and self.secret)

    def public_dict(self) -> dict[str, Any]:
        return {
            "board_url": self.board_url,
            "repo": self.repo,
            "actor": self.actor,
            "secret_configured": bool(self.secret),
            "token_configured": bool(self.token),
            "machine_id": self.machine_id,
            "heartbeat_interval": self.heartbeat_interval,
            "configured": self.configured,
        }


def default_paths(home: Path | None = None) -> AgentPaths:
    base_home = home or Path.home()
    config_dir = base_home / ".config" / "wily" / "agent"
    return AgentPaths(
        config_path=Path(os.environ.get("WILY_AGENT_CONFIG", config_dir / "config.json")),
        registry_path=Path(os.environ.get("WILY_AGENT_REGISTRY", config_dir / "registry.json")),
        plist_path=Path(os.environ.get("WILY_AGENT_PLIST", base_home / "Library" / "LaunchAgents" / "com.wily.roadmap.agent.plist")),
        log_dir=Path(os.environ.get("WILY_AGENT_LOG_DIR", base_home / "Library" / "Logs" / "wily-agent")),
    )


def load_config(path: Path) -> AgentConfig:
    env_config = AgentConfig(
        board_url=os.environ.get("WILY_BOARD_URL", ""),
        repo=os.environ.get("WILY_BOARD_REPO", ""),
        actor=os.environ.get("WILY_BOARD_ACTOR", ""),
        secret=os.environ.get("WILY_BOARD_SECRET", ""),
        token=os.environ.get("WILY_AGENT_TOKEN", ""),
        machine_id=os.environ.get("WILY_AGENT_MACHINE_ID", ""),
        heartbeat_interval=_int_env("WILY_AGENT_HEARTBEAT_INTERVAL", 5),
    )
    if not path.exists():
        return env_config
    data = json.loads(path.read_text(encoding="utf-8"))
    return AgentConfig(
        board_url=str(data.get("board_url") or env_config.board_url),
        repo=str(data.get("repo") or env_config.repo),
        actor=str(data.get("actor") or env_config.actor),
        secret=str(data.get("secret") or env_config.secret),
        token=str(data.get("token") or env_config.token),
        machine_id=str(data.get("machine_id") or env_config.machine_id),
        heartbeat_interval=int(data.get("heartbeat_interval") or env_config.heartbeat_interval),
    )


def save_config(path: Path, config: AgentConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            config.public_dict() | {"secret": config.secret, "token": config.token},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default
