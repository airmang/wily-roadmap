"""Manage the bundled wily-agent daemon."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
import socket
from typing import Any

from . import _common
from wily.agent.client import register_agent
from wily.agent.config import AgentConfig, default_paths, load_config, save_config
from wily.agent.daemon import run_loop
from wily.agent.launchd import LABEL, foreground_command, launchd_plist
from wily.agent.registry import load_registry, register_repo, unregister_repo
from wily.paths import find_wily_root


DESCRIPTION = "install and manage the bundled Board sync daemon"
USAGE = "usage: wily agent <login|install|configure|register|unregister|start|stop|status|check|run|dev> [args]"
HELP = "\n".join(
    [
        "Commands:",
        "  login      exchange a Board one-time code for a machine token",
        "  install    write the macOS launchd plist",
        "  configure  write local Board connection config",
        "  register   add this .wily repo to the local registry",
        "  unregister remove this .wily repo from the local registry",
        "  start      launch the launchd daemon",
        "  stop       stop the launchd daemon",
        "  status     print install/config/daemon status",
        "  check      best-effort smoke check",
        "  run        run foreground daemon loop",
        "  dev        run foreground daemon loop",
    ]
)


def main(args: list[str]) -> int:
    if not args or args[0] in {"-h", "--help"}:
        print_help()
        return _common.EXIT_OK if args else _common.EXIT_USAGE
    command, rest = args[0], args[1:]
    if command == "login":
        return _login(rest)
    if command == "install":
        return _install(rest)
    if command == "configure":
        return _configure(rest)
    if command == "register":
        return _register(rest)
    if command == "unregister":
        return _unregister(rest)
    if command == "start":
        return _launchctl("bootstrap", rest)
    if command == "stop":
        return _launchctl("bootout", rest)
    if command == "status":
        return _status(rest)
    if command == "check":
        return _check(rest)
    if command in {"run", "dev"}:
        return _dev(rest)
    _common.emit_error(f"unknown agent command: {command!r}")
    _common.emit_error(USAGE)
    return _common.EXIT_USAGE


def print_help() -> None:
    _common.print_command_help("agent")


def _install(args: list[str]) -> int:
    paths = default_paths()
    plugin_root = _plugin_root()
    python_executable = sys.executable
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    text = launchd_plist(
        label=LABEL,
        python_executable=python_executable,
        plugin_root=plugin_root,
        registry_path=paths.registry_path,
        config_path=paths.config_path,
        log_dir=paths.log_dir,
    )
    if "--print" in args:
        _common.emit_text(text)
        return _common.EXIT_OK
    paths.plist_path.parent.mkdir(parents=True, exist_ok=True)
    paths.plist_path.write_text(text, encoding="utf-8")
    _common.emit_text(f"wily-agent launchd plist written: {paths.plist_path}")
    return _common.EXIT_OK


def _configure(args: list[str]) -> int:
    values = _flag_values(args)
    paths = default_paths()
    existing = load_config(paths.config_path)
    config = AgentConfig(
        board_url=values.get("--url", existing.board_url),
        repo=values.get("--repo", existing.repo),
        actor=values.get("--actor", existing.actor),
        secret=values.get("--secret", existing.secret),
        token=values.get("--token", existing.token),
        machine_id=values.get("--machine-id", existing.machine_id),
        heartbeat_interval=int(values.get("--interval", str(existing.heartbeat_interval))),
    )
    save_config(paths.config_path, config)
    _common.emit_json(config.public_dict()) if "--json" in args else _common.emit_text(f"wily-agent config written: {paths.config_path}")
    return _common.EXIT_OK


def _login(args: list[str]) -> int:
    values = _flag_values(args)
    code = values.get("--code") or (args[0] if args and not args[0].startswith("--") else "")
    board_url = values.get("--url") or values.get("--board-url") or ""
    actor = values.get("--actor") or ""
    if not code or not board_url or not actor:
        _common.emit_error("usage: wily agent login <code> --url <board-url> --actor <actor>")
        return _common.EXIT_USAGE
    machine_name = values.get("--machine") or socket.gethostname()
    result = register_agent(board_url=board_url, code=code, actor=actor, machine_name=machine_name)
    if not result.get("token"):
        _common.emit_error(str(result.get("reason") or result))
        return _common.EXIT_FAILURE
    paths = default_paths()
    existing = load_config(paths.config_path)
    config = AgentConfig(
        board_url=board_url,
        repo=existing.repo,
        actor=actor,
        secret=existing.secret,
        token=str(result["token"]),
        machine_id=str(result.get("machine_id") or existing.machine_id),
        heartbeat_interval=existing.heartbeat_interval,
    )
    save_config(paths.config_path, config)
    _common.emit_json(config.public_dict()) if "--json" in args else _common.emit_text(f"wily-agent logged in: {config.machine_id}")
    return _common.EXIT_OK


def _register(args: list[str]) -> int:
    values = _flag_values(args)
    paths = default_paths()
    root = Path(values.get("--path", find_wily_root(Path.cwd())))
    config = load_config(paths.config_path)
    repo = values.get("--repo", config.repo)
    entry = register_repo(root, repo, paths.registry_path)
    payload = {"registered": entry.to_dict(), "registry": str(paths.registry_path)}
    _common.emit_json(payload) if "--json" in args else _common.emit_text(f"wily-agent registered: {entry.path}")
    return _common.EXIT_OK


def _unregister(args: list[str]) -> int:
    values = _flag_values(args)
    paths = default_paths()
    root = Path(values.get("--path", find_wily_root(Path.cwd())))
    removed = unregister_repo(root, paths.registry_path)
    payload = {"removed": removed, "path": str(root.resolve()), "registry": str(paths.registry_path)}
    _common.emit_json(payload) if "--json" in args else _common.emit_text(f"wily-agent unregistered: {root.resolve()}" if removed else f"wily-agent not registered: {root.resolve()}")
    return _common.EXIT_OK


def _status(args: list[str]) -> int:
    payload = status_payload()
    _common.emit_json(payload) if "--json" in args else _common.emit_text(_status_text(payload))
    return _common.EXIT_OK


def _check(args: list[str]) -> int:
    payload = status_payload()
    payload["ok"] = True
    payload["offline"] = "--offline" in args or "--offline-ok" in args
    _common.emit_json(payload) if "--json" in args else _common.emit_text(_status_text(payload))
    return _common.EXIT_OK


def _dev(args: list[str]) -> int:
    values = _flag_values(args)
    paths = default_paths()
    config_path = Path(values.get("--config", str(paths.config_path)))
    registry_path = Path(values.get("--registry", str(paths.registry_path)))
    results = run_loop(load_config(config_path), registry_path, once="--once" in args, offline_ok="--offline-ok" in args)
    _common.emit_json({"results": results}) if "--json" in args else _common.emit_text(f"wily-agent dev tick: {len(results)} repo(s)")
    return _common.EXIT_OK


def _launchctl(action: str, args: list[str]) -> int:
    paths = default_paths()
    if "--print" in args:
        target = f"gui/$(id -u)" if action == "bootstrap" else f"gui/$(id -u)/{LABEL}"
        _common.emit_text(f"launchctl {action} {target} {paths.plist_path if action == 'bootstrap' else ''}".strip())
        return _common.EXIT_OK
    domain = f"gui/{_uid()}"
    command = ["launchctl", action, domain, str(paths.plist_path)] if action == "bootstrap" else ["launchctl", action, f"{domain}/{LABEL}"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        _common.emit_error(result.stderr.strip() or result.stdout.strip() or f"launchctl {action} failed")
        return _common.EXIT_FAILURE
    _common.emit_text(f"wily-agent launchd {action} ok")
    return _common.EXIT_OK


def status_payload() -> dict[str, Any]:
    paths = default_paths()
    config = load_config(paths.config_path)
    repos = load_registry(paths.registry_path)
    return {
        "installed": True,
        "configured": config.configured,
        "config": config.public_dict(),
        "registry": {"path": str(paths.registry_path), "repos": [repo.to_dict() for repo in repos]},
        "launchd": {"label": LABEL, "plist": str(paths.plist_path), "plist_exists": paths.plist_path.exists()},
        "daemon": {"running": _launchctl_running()},
    }


def _status_text(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"installed: {payload['installed']}",
            f"configured: {payload['configured']}",
            f"daemon running: {payload['daemon']['running']}",
            f"registry: {payload['registry']['path']}",
        ]
    )


def _flag_values(args: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("--") and index + 1 < len(args) and not args[index + 1].startswith("--"):
            values[token] = args[index + 1]
            index += 2
            continue
        index += 1
    return values


def _launchctl_running() -> bool:
    if shutil.which("launchctl") is None:
        return False
    result = subprocess.run(["launchctl", "print", f"gui/{_uid()}/{LABEL}"], capture_output=True, text=True)
    return result.returncode == 0


def _uid() -> int:
    try:
        import os

        return os.getuid()
    except AttributeError:
        return 0


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]
