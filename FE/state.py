"""App state machine and placement logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from config import MAX_SNACKS, Position


class AppPhase(str, Enum):
    PLACEMENT = "placement"
    EXPLORATION = "exploration"
    PATH = "path"


class PlacementTool(str, Enum):
    SPIDER = "spider"
    SNACK = "snack"


PqEntry = tuple[int, Position, frozenset[Position]]


@dataclass
class PlaybackState:
    explored: list[Position] = field(default_factory=list)
    explored_remaining: list[frozenset[Position]] = field(default_factory=list)
    explored_pq_top: list[tuple[PqEntry, ...]] = field(default_factory=list)
    path: list[Position] = field(default_factory=list)
    explored_index: int = 0
    path_index: int = 0

    def reset(self) -> None:
        self.explored.clear()
        self.explored_remaining.clear()
        self.explored_pq_top.clear()
        self.path.clear()
        self.explored_index = 0
        self.path_index = 0

    def current_pq_top(self) -> tuple[PqEntry, ...]:
        """Top-K priority-queue snapshot at the most recently animated step."""
        if self.explored_index == 0 or not self.explored_pq_top:
            return ()
        return self.explored_pq_top[self.explored_index - 1]

    def history_subsets(self) -> list[frozenset[Position]]:
        """Distinct remaining-subsets seen so far, in first-appearance order."""
        seen: list[frozenset[Position]] = []
        seen_set: set[frozenset[Position]] = set()
        for r in self.explored_remaining[: self.explored_index]:
            if r not in seen_set:
                seen_set.add(r)
                seen.append(r)
        return seen

    def visible_explored(self) -> list[tuple[Position, frozenset[Position]]]:
        return list(zip(
            self.explored[: self.explored_index],
            self.explored_remaining[: self.explored_index],
        ))

    def visible_path(self) -> list[Position]:
        return self.path[: self.path_index]

    def current_remaining(self) -> frozenset[Position] | None:
        """Remaining-goal set at the most recently animated A* expansion."""
        if self.explored_index == 0 or not self.explored_remaining:
            return None
        return self.explored_remaining[self.explored_index - 1]


@dataclass
class FrontendState:
    spider: Position | None = None
    snacks: set[Position] = field(default_factory=set)
    phase: AppPhase = AppPhase.PLACEMENT
    active_tool: PlacementTool = PlacementTool.SPIDER
    toast_message: str = ""
    toast_until_ms: int = 0
    paused: bool = False
    playback: PlaybackState = field(default_factory=PlaybackState)

    solver_generator: object | None = None
    solver_finished: bool = False

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
        self.paused = False
        self.solver_generator = None
        self.solver_finished = False

    def place_at(self, cell: Position, now_ms: int) -> None:
        if self.phase != AppPhase.PLACEMENT:
            return

        if self.active_tool == PlacementTool.SPIDER:
            if cell in self.snacks:
                self.set_toast("Cannot place spider on a snack.", now_ms)
                return
            self.spider = cell
            return

        if self.spider == cell:
            self.set_toast("Cannot place snack on spider.", now_ms)
            return
        if cell in self.snacks:
            self.set_toast("Cannot place multiple snacks in the same cell.", now_ms)
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
