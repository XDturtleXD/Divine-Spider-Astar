"""Grid geometry, window layout, and toolbar button rects."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets import SpiderAssets
from config import Position


@dataclass(frozen=True)
class WindowLayout:
    """Bottom toolbar rect plus left/right side panels (play field is derived in `Grid`)."""

    button_strip: pygame.Rect
    left_panel: pygame.Rect
    right_panel: pygame.Rect


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
        return self.rows + 2

    @property
    def visible_cols(self) -> int:
        return self.cols + 2

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
        display_row = (self.rows - 1) - row
        return pygame.Rect(
            self.offset_x + (col + 1) * self.cell_s,
            self.offset_y + (display_row + 1) * self.cell_s,
            self.cell_s,
            self.cell_s,
        )

    def point_to_cell(self, x: int, y: int) -> Position | None:
        rx = x - self.offset_x
        ry = y - self.offset_y
        if rx < 0 or ry < 0:
            return None
        col = rx // self.cell_s - 1
        display_row = ry // self.cell_s - 1
        row = (self.rows - 1) - display_row
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None


@dataclass
class UiRects:
    spider_button: pygame.Rect
    snack_button: pygame.Rect
    run_button: pygame.Rect
    pause_button: pygame.Rect
    reset_button: pygame.Rect


class LayoutManager:
    """Layout calculations and asset scaling on resize. No drawing."""

    _MARGIN_SIDE = 8
    _MARGIN_TOP = 8
    _MARGIN_BOTTOM = 8
    _BUTTON_GAP = 14
    _BUTTON_STRIP_MIN_H = 100
    _BUTTON_STRIP_PAD_X = 12
    _BUTTON_STRIP_PAD_Y = 10
    _PANEL_W = 200
    _PANEL_GAP = 8
    _MIN_BOARD_W = 320

    def __init__(self, assets: SpiderAssets, grid: Grid) -> None:
        self.assets = assets
        self.grid = grid
        self._cached_cell_s: int = -1
        self._last_window_size: tuple[int, int] = (0, 0)

    def _compute_window_layout(self, surface: pygame.Surface) -> WindowLayout:
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

        panel_w = self._PANEL_W
        gap = self._PANEL_GAP
        board_w_if_panels = inner_w - 2 * panel_w - 2 * gap
        if board_w_if_panels < self._MIN_BOARD_W:
            panel_w = 0
            gap = 0
            board_w = inner_w
        else:
            board_w = board_w_if_panels

        left_x = self._MARGIN_SIDE
        board_x = left_x + panel_w + gap
        right_x = board_x + board_w + gap
        panels_top = self._MARGIN_TOP
        panels_h = play_h

        left_panel = pygame.Rect(left_x, panels_top, panel_w, panels_h)
        right_panel = pygame.Rect(right_x, panels_top, panel_w, panels_h)
        play_rect = pygame.Rect(board_x, panels_top, board_w, play_h)
        button_strip = pygame.Rect(
            self._MARGIN_SIDE,
            self._MARGIN_TOP + play_h,
            inner_w,
            strip_h,
        )

        self.grid.fit_square_cells_in_rect(play_rect)

        return WindowLayout(
            button_strip=button_strip,
            left_panel=left_panel,
            right_panel=right_panel,
        )

    def _resolve_button_strip_height(self, inner_w: int) -> int:
        max_h = self.assets.trimmed_max_height
        row_h = max_h + 2 * self._BUTTON_STRIP_PAD_Y
        return max(self._BUTTON_STRIP_MIN_H, row_h)

    def _compute_ui_rects(self, strip: pygame.Rect) -> UiRects:
        gap = self._BUTTON_GAP
        inner = pygame.Rect(
            strip.x + self._BUTTON_STRIP_PAD_X,
            strip.y + self._BUTTON_STRIP_PAD_Y,
            max(1, strip.width - 2 * self._BUTTON_STRIP_PAD_X),
            max(1, strip.height - 2 * self._BUTTON_STRIP_PAD_Y),
        )

        assets = self.assets
        h = assets.toolbar_height
        pause_w = max(assets.pause_button_size[0], assets.resume_button_size[0])
        button_sizes = [
            assets.spider_button_size,
            assets.snack_button_size,
            assets.run_button_size,
            (pause_w, h),
            assets.reset_button_size,
        ]
        total_w = sum(w for w, _ in button_sizes) + gap * 4
        x = inner.x + max(0, (inner.width - total_w) // 2)

        rects: list[pygame.Rect] = []
        for bw, bh in button_sizes:
            y = inner.y + max(0, (inner.height - bh) // 2)
            rects.append(pygame.Rect(x, y, bw, bh))
            x += bw + gap

        return UiRects(
            spider_button=rects[0],
            snack_button=rects[1],
            run_button=rects[2],
            pause_button=rects[3],
            reset_button=rects[4],
        )

    def update_layout(self, surface: pygame.Surface) -> tuple[WindowLayout, UiRects]:
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
