"""Frontend app state machine and placement logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

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
    path: list[Position] = field(default_factory=list)
    explored_index: int = 0
    path_index: int = 0

    def reset(self) -> None:
        self.explored.clear()
        self.path.clear()
        self.explored_index = 0
        self.path_index = 0

    def visible_explored(self) -> set[Position]:
        return set(self.explored[: self.explored_index])

    def visible_path(self) -> list[Position]:
        return self.path[: self.path_index]


@dataclass(frozen=True)
class LayerView:
    """Per-layer sub-step data for visualizing multi-snack A*.

    `segment` is the within-layer path EXCLUDING the entry cell and ending
    at the next snack to be eaten. Terminal layer has empty `segment`.
    """

    index: int
    entry: Position
    snacks_remaining: tuple[Position, ...]
    segment: tuple[Position, ...]


def path_to_layers(
    spider_start: Position,
    snacks: Iterable[Position],
    path: list[Position],
) -> list[LayerView]:
    """Decompose a flat BE path into per-snack layers.

    Caller must only invoke this with a non-empty `path`; otherwise use the
    simulator. Each time a step lands on a still-uneaten snack, the current
    layer's segment is closed (ending at that snack) and a new layer opens
    with that snack as its entry. A terminal layer with empty segment is
    always appended.
    """
    remaining: set[Position] = set(snacks)
    layers: list[LayerView] = []
    current_entry: Position = spider_start
    current_segment: list[Position] = []

    for pos in path:
        current_segment.append(pos)
        if pos in remaining:
            layers.append(
                LayerView(
                    index=len(layers),
                    entry=current_entry,
                    snacks_remaining=tuple(sorted(remaining)),
                    segment=tuple(current_segment),
                )
            )
            remaining.discard(pos)
            current_entry = pos
            current_segment = []

    layers.append(
        LayerView(
            index=len(layers),
            entry=current_entry,
            snacks_remaining=tuple(sorted(remaining)),
            segment=(),
        )
    )
    return layers


@dataclass
class FrontendState:
    spider: Position | None = None
    snacks: set[Position] = field(default_factory=set)
    phase: AppPhase = AppPhase.PLACEMENT
    active_tool: PlacementTool = PlacementTool.SPIDER
    toast_message: str = ""
    toast_until_ms: int = 0
    playback: PlaybackState = field(default_factory=PlaybackState)
    layers: list[LayerView] = field(default_factory=list)
    selected_layer: int = 0

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

    def set_layers(self, layers: list[LayerView]) -> None:
        self.layers = list(layers)
        self.selected_layer = 0

    def set_selected_layer(self, idx: int) -> None:
        if not self.layers:
            return
        if 0 <= idx < len(self.layers):
            self.selected_layer = idx

    def clear_board(self) -> None:
        self.spider = None
        self.snacks.clear()
        self.playback.reset()
        self.layers = []
        self.selected_layer = 0
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
