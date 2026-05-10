"""Frontend app state machine and placement logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from spider_scene import MAX_SNACKS, Position


class AppPhase(str, Enum):
    PLACEMENT = "placement"
    EXPLORATION = "exploration"
    PATH = "path"


class PlacementTool(str, Enum):
    SPIDER = "spider"
    SNACK = "snack"


@dataclass
class PlaybackState:
    explored: list[Position] = field(default_factory=list)
    explored_s_costs: list[int] = field(default_factory=list)
    explored_h_costs: list[int] = field(default_factory=list)
    explored_frontiers: list[dict[Position, tuple[int, int]]] = field(default_factory=list)
    explored_remaining: list[frozenset[Position]] = field(default_factory=list)
    path: list[Position] = field(default_factory=list)
    explored_index: int = 0
    path_index: int = 0
    sub_step: int = 0  # 0: borders shown, 1: selected border removed, 2: selected turns green

    def reset(self) -> None:
        self.explored.clear()
        self.explored_s_costs.clear()
        self.explored_h_costs.clear()
        self.explored_frontiers.clear()
        self.explored_remaining.clear()
        self.path.clear()
        self.explored_index = 0
        self.path_index = 0
        self.sub_step = 0

    def visible_explored(self) -> set[Position]:
        return set(self.explored[: self.explored_index])

    def visible_explored_with_costs(self) -> list[tuple[Position, int, int]]:
        """Returns (pos, g, h) for each visible explored cell."""
        # At sub_step 2, include the just-selected cell so it renders green
        count = self.explored_index
        if self.sub_step == 2 and count < len(self.explored):
            count += 1
        return list(zip(self.explored[:count], self.explored_s_costs[:count], self.explored_h_costs[:count]))

    def current_frontier(self) -> dict[Position, tuple[int, int]]:
        if self.explored_index == 0:
            return {}
        return self.explored_frontiers[self.explored_index - 1]

    def latest_explored(self) -> Position | None:
        # At sub_step 2, the next cell has just turned green
        if self.sub_step == 2 and self.explored_index < len(self.explored):
            return self.explored[self.explored_index]
        if self.explored_index == 0:
            return None
        return self.explored[self.explored_index - 1]

    def current_remaining(self) -> frozenset[Position] | None:
        """Remaining snacks for the currently highlighted (green) explored cell."""
        if not self.explored_remaining:
            return None
        if self.sub_step == 2 and self.explored_index < len(self.explored_remaining):
            return self.explored_remaining[self.explored_index]
        if self.explored_index == 0:
            return None
        return self.explored_remaining[self.explored_index - 1]

    def current_s_h(self) -> tuple[int, int] | None:
        """(g, h) costs for the currently highlighted (green) explored cell."""
        if not self.explored_s_costs:
            return None
        if self.sub_step == 2 and self.explored_index < len(self.explored_s_costs):
            return (self.explored_s_costs[self.explored_index], self.explored_h_costs[self.explored_index])
        if self.explored_index == 0:
            return None
        return (self.explored_s_costs[self.explored_index - 1], self.explored_h_costs[self.explored_index - 1])

    def position_visit_counts(self) -> dict[Position, int]:
        """How many times each position has been expanded up to current playback step."""
        count = self.explored_index
        if self.sub_step == 2 and count < len(self.explored):
            count += 1
        counts: dict[Position, int] = {}
        for pos in self.explored[:count]:
            counts[pos] = counts.get(pos, 0) + 1
        return counts

    def next_cell(self) -> Position | None:
        if self.explored_index < len(self.explored):
            return self.explored[self.explored_index]
        return None

    def visible_path(self) -> list[Position]:
        return self.path[: self.path_index]


@dataclass
class FrontendState:
    spider: Position | None = None
    snacks: set[Position] = field(default_factory=set)
    phase: AppPhase = AppPhase.PLACEMENT
    active_tool: PlacementTool = PlacementTool.SPIDER
    toast_message: str = ""
    toast_until_ms: int = 0
    playback: PlaybackState = field(default_factory=PlaybackState)

    def can_run(self) -> bool:
        return self.spider is not None and len(self.snacks) >= 1

    def set_tool(self, tool: PlacementTool) -> None:
        self.active_tool = tool

    def set_toast(self, message: str, now_ms: int, duration_ms: int = 1600) -> None:
        self.toast_message = message
        self.toast_until_ms = now_ms + duration_ms

    def clear_toast_if_expired(self, now_ms: int) -> None:
        if self.toast_message and now_ms >= self.toast_until_ms:
            self.toast_message = ""

    def clear_board(self) -> None:
        self.spider = None
        self.snacks.clear()
        self.playback.reset()
        self.phase = AppPhase.PLACEMENT

    def place_at(self, cell: Position, now_ms: int) -> None:
        if self.phase != AppPhase.PLACEMENT:
            return

        if self.active_tool == PlacementTool.SPIDER:
            if cell in self.snacks:
                self.set_toast("Cannot place spider on a snack.", now_ms)
                return
            self.spider = cell
            return

        # Snack placement mode.
        if self.spider == cell:
            self.set_toast("Cannot place snack on spider.", now_ms)
            return
        if cell in self.snacks:
            return
        if len(self.snacks) >= MAX_SNACKS:
            self.set_toast(f"Snack limit reached ({MAX_SNACKS}/{MAX_SNACKS}).", now_ms)
            return
        self.snacks.add(cell)

    def remove_at(self, cell: Position) -> None:
        if self.phase != AppPhase.PLACEMENT:
            return
        if self.spider == cell:
            self.spider = None
        self.snacks.discard(cell)
