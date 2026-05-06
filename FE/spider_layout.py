"""Layout management for interactive spider viewer: grid geometry, UI rects, asset scaling."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from spider_assets import SpiderAssets
from spider_scene import Position


@dataclass(frozen=True)
class WindowLayout:
    """Bottom toolbar rect (play field is derived in `Grid` via `fit_square_cells_in_rect`)."""

    button_strip: pygame.Rect


@dataclass
class Grid:
    """Square cells; geometry includes playable area plus one-cell border."""

    rows: int
    cols: int
    offset_x: int = 0
    offset_y: int = 0
    cell_s: int = 8
    min_cell_px: int = 8

    @property
    def visible_rows(self) -> int:
        return self.rows + 2  # include both borders

    @property
    def visible_cols(self) -> int:
        return self.cols + 2  # include both borders

    def fit_square_cells_in_rect(self, rect: pygame.Rect) -> None:
        """Size square cells so the full border ring (rows+2 × cols+2) fits inside rect."""
        vw, vh = self.visible_cols, self.visible_rows
        if vw <= 0 or vh <= 0 or rect.width <= 0 or rect.height <= 0:
            self.cell_s = self.min_cell_px
            self.offset_x = rect.x
            self.offset_y = rect.y
            return
        cap_w = max(1, rect.width // vw)
        cap_h = max(1, rect.height // vh)
        cell_s = max(self.min_cell_px, min(cap_w, cap_h))
        board_w = vw * cell_s
        board_h = vh * cell_s
        self.cell_s = cell_s
        self.offset_x = rect.x + max(0, (rect.width - board_w) // 2)
        self.offset_y = rect.y + max(0, (rect.height - board_h) // 2)

    def cell_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            self.offset_x + col * self.cell_s,
            self.offset_y + row * self.cell_s,
            self.cell_s,
            self.cell_s,
        )

    def point_to_cell(self, x: int, y: int) -> Position | None:
        rx = x - self.offset_x
        ry = y - self.offset_y
        if rx < 0 or ry < 0:
            return None
        col = rx // self.cell_s
        row = ry // self.cell_s
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None


@dataclass
class UiRects:
    """Clickable UI button rects."""

    spider_button: pygame.Rect
    snack_button: pygame.Rect
    run_button: pygame.Rect
    reset_button: pygame.Rect


class LayoutManager:
    """Handles all layout calculations and asset scaling. No drawing logic."""

    _MARGIN_SIDE = 8
    _MARGIN_TOP = 8
    _MARGIN_BOTTOM = 8
    _BUTTON_GAP = 14
    _BUTTON_STRIP_MIN_H = 100
    _BUTTON_STRIP_PAD_X = 12
    _BUTTON_STRIP_PAD_Y = 10

    def __init__(self, assets: SpiderAssets, grid: Grid) -> None:
        self.assets = assets
        self.grid = grid
        self._cached_cell_s: int = -1
        self._last_window_size: tuple[int, int] = (0, 0)

    def _compute_window_layout(self, surface: pygame.Surface) -> WindowLayout:
        """Partition window into play field (top) and button strip (bottom)."""
        ww, wh = surface.get_size()
        inner_w = max(1, ww - 2 * self._MARGIN_SIDE)
        usable_h = max(1, wh - self._MARGIN_TOP - self._MARGIN_BOTTOM)

        want_strip = self._resolve_button_strip_height(inner_w)
        min_play = self.grid.min_cell_px * self.grid.visible_rows
        strip_h = min(want_strip, max(usable_h - min_play, 52))
        strip_h = max(52, strip_h)
        if strip_h >= usable_h:
            strip_h = max(usable_h // 3, usable_h // 5)
            strip_h = min(strip_h, usable_h - 1)
        play_h = max(1, usable_h - strip_h)

        play_rect = pygame.Rect(
            self._MARGIN_SIDE,
            self._MARGIN_TOP,
            inner_w,
            play_h,
        )
        button_strip = pygame.Rect(
            self._MARGIN_SIDE,
            self._MARGIN_TOP + play_h,
            inner_w,
            strip_h,
        )

        self.grid.fit_square_cells_in_rect(play_rect)

        return WindowLayout(button_strip=button_strip)

    def _resolve_button_strip_height(self, inner_w: int) -> int:
        """Reserve height for four scaled button icons in a row."""
        slot_w = max(48, (inner_w - self._BUTTON_GAP * 3) // 4)
        max_h = self.assets.trimmed_max_height
        scale = min(1.0, slot_w / self.assets.trimmed_max_width)
        row_h = int(max_h * scale) + 2 * self._BUTTON_STRIP_PAD_Y
        return max(self._BUTTON_STRIP_MIN_H, row_h)

    def _compute_ui_rects(self, strip: pygame.Rect) -> UiRects:
        """Lay out four clickable button slots inside the button strip."""
        gap = self._BUTTON_GAP
        inner = pygame.Rect(
            strip.x + self._BUTTON_STRIP_PAD_X,
            strip.y + self._BUTTON_STRIP_PAD_Y,
            max(1, strip.width - 2 * self._BUTTON_STRIP_PAD_X),
            max(1, strip.height - 2 * self._BUTTON_STRIP_PAD_Y),
        )
        usable = max(inner.width - 3 * gap, 40)
        slot_w = usable // 4
        slot_h = inner.height
        excess = inner.width - (4 * slot_w + 3 * gap)
        x0 = inner.x + max(0, excess // 2)
        y0 = inner.y

        return UiRects(
            spider_button=pygame.Rect(x0, y0, slot_w, slot_h),
            snack_button=pygame.Rect(x0 + slot_w + gap, y0, slot_w, slot_h),
            run_button=pygame.Rect(x0 + (slot_w + gap) * 2, y0, slot_w, slot_h),
            reset_button=pygame.Rect(x0 + (slot_w + gap) * 3, y0, slot_w, slot_h),
        )

    def update_layout(self, surface: pygame.Surface) -> tuple[WindowLayout, UiRects]:
        """Recompute layout for current window size; reload assets if needed."""
        layout = self._compute_window_layout(surface)

        wsize = surface.get_size()
        if wsize != self._last_window_size or self._cached_cell_s != self.grid.cell_s:
            self._last_window_size = wsize
            self._cached_cell_s = self.grid.cell_s
            self.assets.reload_scaled(
                cell_s=self.grid.cell_s,
                window_size=wsize,
                button_strip_height=layout.button_strip.height,
                margin_side=self._MARGIN_SIDE,
                button_gap=self._BUTTON_GAP,
                button_strip_pad_y=self._BUTTON_STRIP_PAD_Y,
            )

        ui_rects = self._compute_ui_rects(layout.button_strip)
        return layout, ui_rects
