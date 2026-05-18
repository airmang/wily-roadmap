from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

WatchPanel = Literal["header", "summary", "tasks", "activity", "log"]


@dataclass
class WatchLayoutConfig:
    width: int = 96
    height: int = 24
    ascii_mode: bool = False
    compact: bool = False
    show_observed: bool = True
    show_checkpoint_timeline: bool = False
    show_dependency_graph: bool = False
    panel_order: list[WatchPanel] = field(
        default_factory=lambda: [
            "header",
            "summary",
            "tasks",
            "activity",
            "log",
        ]
    )

    @property
    def layout_mode(self) -> Literal["compact", "standard", "wide"]:
        if self.width < 80 or self.compact:
            return "compact"
        if self.width >= 120:
            return "wide"
        return "standard"

    @property
    def task_pane_width(self) -> int:
        mode = self.layout_mode
        if mode == "compact":
            return self.width - 2
        if mode == "wide":
            return min(80, self.width // 2)
        return min(60, self.width - 24)

    @property
    def activity_pane_width(self) -> int:
        mode = self.layout_mode
        if mode in ("compact", "standard"):
            return 0
        return self.width - self.task_pane_width - 4

    @property
    def max_task_title_width(self) -> int:
        return max(20, self.task_pane_width - 35)

    @property
    def show_activity_panel(self) -> bool:
        return self.layout_mode == "wide" and "activity" in self.panel_order

    @property
    def show_log_panel(self) -> bool:
        return self.layout_mode == "wide" and "log" in self.panel_order
