"""`wily watch` - polling loop around the status renderer."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from . import _common
from .status import main as status_main


def main(args: list[str]) -> int:
    ui = watch_ui(args)
    if ui is None:
        return _common.EXIT_USAGE
    if "--dry-run-pane" in args:
        interval = _interval(args)
        if interval is None:
            return _common.EXIT_USAGE
        print(format_shell_command(tmux_watch_command(Path.cwd(), args)))
        return _common.EXIT_OK
    once = "--once" in args
    interval = _interval(args)
    if interval is None:
        return _common.EXIT_USAGE
    status_args = status_args_from_watch_args(args)
    if once:
        return status_main(status_args)
    mode = watch_launch_mode(
        args,
        in_tmux=bool(os.environ.get("TMUX")),
        stdin_tty=sys.stdin.isatty(),
        stdout_tty=sys.stdout.isatty(),
    )
    if mode == "pane":
        return command_watch_pane(Path.cwd(), args)
    if mode == "needs_interactive_terminal":
        _common.emit_error("wily watch needs an interactive terminal outside tmux.")
        _common.emit_error("For a one-shot text preview, run: wily watch --once --ui ascii")
        return _common.EXIT_FAILURE
    while True:
        print("\033[2J\033[H", end="")
        status_main(status_args)
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            return _common.EXIT_OK


def _interval(args: list[str]) -> float | None:
    if "--interval" not in args:
        return 2.0
    index = args.index("--interval")
    if index + 1 >= len(args):
        _common.emit_error("--interval requires a value")
        return None
    try:
        value = float(args[index + 1])
    except ValueError:
        _common.emit_error("--interval value must be a number")
        return None
    if value <= 0:
        _common.emit_error("--interval must be positive")
        return None
    return value


def status_args_from_watch_args(args: list[str]) -> list[str]:
    out: list[str] = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in {"--once", "--here", "--dry-run-pane", "--no-interactive"}:
            continue
        if arg == "--interval":
            skip_next = True
            continue
        out.append(arg)
    return out


def watch_launch_mode(
    args: list[str],
    *,
    in_tmux: bool,
    stdin_tty: bool,
    stdout_tty: bool,
) -> str:
    if "--here" in args:
        return "here"
    if in_tmux:
        return "pane"
    if stdin_tty and stdout_tty:
        return "here"
    return "needs_interactive_terminal"


def watch_ui(args: list[str]) -> str | None:
    if "--ui" not in args:
        return "auto"
    index = args.index("--ui")
    if index + 1 >= len(args):
        _common.emit_error("--ui requires one of: auto, rich, ascii")
        return None
    ui = args[index + 1]
    if ui not in {"auto", "rich", "ascii"}:
        _common.emit_error("--ui requires one of: auto, rich, ascii")
        return None
    return ui


def tmux_watch_command(
    root: Path,
    args: list[str],
    *,
    script: Path | None = None,
    python: str | None = None,
    current_pane: str | None = None,
) -> list[str]:
    script = script or Path(__file__).resolve().parents[2] / "wily.py"
    python = python or sys.executable
    interval = _interval(args)
    if interval is None:
        interval = 2.0
    inner = " ".join(
        [
            "cd",
            shlex.quote(str(root)),
            "&&",
            shlex.quote(python),
            shlex.quote(str(script)),
            "watch",
            "--here",
            "--ui",
            shlex.quote(watch_ui(args) or "auto"),
            "--interval",
            shlex.quote(f"{interval:.1f}"),
        ]
    )
    command = ["tmux", "split-window"]
    pane = current_pane if current_pane is not None else os.environ.get("TMUX_PANE", "").strip()
    if pane:
        command.extend(["-t", pane])
    command.extend(["-h", inner])
    return command


def format_shell_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def command_watch_pane(root: Path, args: list[str]) -> int:
    if not os.environ.get("TMUX"):
        _common.emit_error("tmux 세션이 아니라서 pane을 열 수 없습니다.")
        _common.emit_error("현재 pane에서 보려면 다음을 실행하세요: wily watch --here")
        return _common.EXIT_FAILURE
    result = subprocess.run(tmux_watch_command(root, args), text=True)
    return result.returncode
