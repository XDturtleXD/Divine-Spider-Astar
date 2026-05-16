"""Drawing: grid, exploration overlays, path, panels, toolbar, toasts."""

from __future__ import annotations

import pygame

from assets import SpiderAssets
from config import MAX_SNACKS, Position
from layout import Grid, UiRects, WindowLayout
from state import AppPhase, FrontendState, PlacementTool
from theme import (
    BACKGROUND_RGB,
    EXPLORATION_SUBSET_PALETTE,
    EXPLORED_STRIPE_ALPHA,
    PATH_LINE_RGB,
)


def draw_button(
    surface: pygame.Surface,
    tints: dict[str, pygame.Surface],
    rect: pygame.Rect,
    disabled: bool = False,
    active: bool = False,
) -> None:
    if disabled:
        button = tints["disabled"]
    elif active:
        button = tints["active"]
    else:
        button = tints["normal"]

    r = button.get_rect(center=rect.center)
    surface.blit(button, r)


class SceneDrawer:
    """Handles all rendering operations. No layout or state management."""

    def __init__(self, assets: SpiderAssets, grid: Grid) -> None:
        self.assets = assets
        self.grid = grid
        self._font = pygame.font.SysFont("arial", 18)
        self._panel_title_font = pygame.font.SysFont("arial", 16, bold=True)
        self._panel_font = pygame.font.SysFont("arial", 13)
        self._panel_small_font = pygame.font.SysFont("arial", 11)
        self._subset_color_cache: dict[frozenset[Position], tuple[int, int, int]] = {}
        self._color_cache_signature: int = -1

    def _maybe_invalidate_color_cache(self, state: FrontendState) -> None:
        sig = id(state.playback.explored_remaining)
        if sig != self._color_cache_signature:
            self._color_cache_signature = sig
            self._subset_color_cache.clear()

    def _color_for(self, remaining: frozenset[Position]) -> tuple[int, int, int]:
        cached = self._subset_color_cache.get(remaining)
        if cached is not None:
            return cached
        idx = len(self._subset_color_cache) % len(EXPLORATION_SUBSET_PALETTE)
        color = EXPLORATION_SUBSET_PALETTE[idx]
        self._subset_color_cache[remaining] = color
        return color

    def draw(
        self,
        surface: pygame.Surface,
        state: FrontendState,
        window_layout: WindowLayout,
        ui_rects: UiRects,
    ) -> None:
        self._maybe_invalidate_color_cache(state)

        surface.fill(BACKGROUND_RGB)

        for row in range(-1, self.grid.rows + 1):
            for col in range(-1, self.grid.cols + 1):
                dest = self.grid.cell_rect(row, col)
                if row in (-1, self.grid.rows) or col in (-1, self.grid.cols):
                    surface.blit(self.assets.border_tile, dest)
                else:
                    surface.blit(self.assets.ground_tile, dest)

        cell_subsets: dict[Position, list[frozenset[Position]]] = {}
        for (pos, remaining) in state.playback.visible_explored():
            lst = cell_subsets.setdefault(pos, [])
            if remaining not in lst:
                lst.append(remaining)

        for pos, subsets in cell_subsets.items():
            cell_rect = self.grid.cell_rect(*pos)
            n = len(subsets)
            for i, subset in enumerate(subsets):
                x_start = cell_rect.x + (cell_rect.width * i) // n
                x_end = cell_rect.x + (cell_rect.width * (i + 1)) // n
                stripe_w = max(1, x_end - x_start)
                color = self._color_for(subset)
                stripe = pygame.Surface((stripe_w, cell_rect.height), pygame.SRCALPHA)
                stripe.fill((*color, EXPLORED_STRIPE_ALPHA))
                surface.blit(stripe, (x_start, cell_rect.y))

        if (
            state.phase == AppPhase.EXPLORATION
            and state.playback.explored_index > 0
            and state.playback.explored
        ):
            current_pos = state.playback.explored[state.playback.explored_index - 1]
            hl_rect = self.grid.cell_rect(*current_pos)
            hl_w = max(2, self.grid.cell_s // 8)
            pygame.draw.rect(surface, (255, 255, 255), hl_rect, width=hl_w)

        visible_path = state.playback.visible_path()
        if visible_path and state.spider is not None:
            points = [self.grid.cell_rect(*state.spider).center]
            points.extend(self.grid.cell_rect(r, c).center for r, c in visible_path)
            line_w = max(2, self.grid.cell_s // 6)
            pygame.draw.lines(surface, PATH_LINE_RGB, False, points, line_w)

        consumed = set(visible_path) if state.phase in (AppPhase.PATH, AppPhase.EXPLORATION) else set()
        for row, col in sorted(state.snacks):
            if (row, col) in consumed:
                continue
            surface.blit(self.assets.snack_tile, self.grid.cell_rect(row, col))

        spider_pos = state.spider
        if state.phase == AppPhase.PATH and visible_path:
            spider_pos = visible_path[-1]
        if spider_pos is not None:
            surface.blit(self.assets.spider_tile, self.grid.cell_rect(*spider_pos))

        self._draw_legend_panel(surface, state, window_layout.left_panel)
        self._draw_next_up_panel(surface, state, window_layout.right_panel)
        self._draw_controls(surface, state, ui_rects)
        self._draw_toast(surface, state, window_layout.button_strip.top)

    def _draw_controls(self, surface: pygame.Surface, state: FrontendState, ui_rects: UiRects) -> None:
        spider_disabled = state.phase != AppPhase.PLACEMENT
        spider_active = state.active_tool == PlacementTool.SPIDER
        draw_button(
            surface,
            self.assets.spider_button_tints,
            ui_rects.spider_button,
            disabled=spider_disabled,
            active=spider_active,
        )

        snack_disabled = state.phase != AppPhase.PLACEMENT or len(state.snacks) >= MAX_SNACKS
        snack_active = state.active_tool == PlacementTool.SNACK
        draw_button(
            surface,
            self.assets.snack_button_tints,
            ui_rects.snack_button,
            disabled=snack_disabled,
            active=snack_active,
        )

        run_disabled = state.phase != AppPhase.PLACEMENT or not state.can_run()
        draw_button(
            surface,
            self.assets.run_button_tints,
            ui_rects.run_button,
            disabled=run_disabled,
        )

        pause_disabled = state.phase == AppPhase.PLACEMENT
        pause_tints = (
            self.assets.resume_button_tints if state.paused else self.assets.pause_button_tints
        )
        draw_button(
            surface,
            pause_tints,
            ui_rects.pause_button,
            disabled=pause_disabled,
            active=state.paused and not pause_disabled,
        )

        reset_disabled = state.phase == AppPhase.PLACEMENT
        draw_button(
            surface,
            self.assets.reset_button_tints,
            ui_rects.reset_button,
            disabled=reset_disabled,
        )

    def _draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect, title: str) -> pygame.Rect:
        pygame.draw.rect(surface, (32, 32, 36), rect)
        pygame.draw.rect(surface, (70, 70, 78), rect, width=1)
        title_surf = self._panel_title_font.render(title, True, (235, 235, 235))
        surface.blit(title_surf, (rect.x + 10, rect.y + 8))
        return pygame.Rect(rect.x + 8, rect.y + 32, rect.width - 16, rect.height - 40)

    def _user_coord(self, pos: Position) -> Position:
        return ((self.grid.rows - 1) - pos[0], pos[1])

    def _draw_legend_panel(self, surface: pygame.Surface, state: FrontendState, rect: pygame.Rect) -> None:
        if rect.width <= 0 or rect.height <= 0:
            return
        interior = self._draw_panel_background(surface, rect, "Color legend")

        history = state.playback.history_subsets()
        if not history:
            placeholder = self._panel_font.render(
                "Run A* to see color mapping.", True, (160, 160, 165)
            )
            surface.blit(placeholder, (interior.x, interior.y))
            return

        current = state.playback.current_remaining()
        sw_size = 14
        row_h = 22
        row_y = interior.y
        for subset in history:
            if row_y + row_h > interior.bottom:
                break
            sw_color = self._color_for(subset)
            sw = pygame.Rect(interior.x, row_y + 4, sw_size, sw_size)
            pygame.draw.rect(surface, sw_color, sw)
            pygame.draw.rect(surface, (220, 220, 220), sw, width=1)

            is_current = subset == current
            if not subset:
                label = "0  all collected"
            else:
                coords = ", ".join(f"({r},{c})" for r, c in sorted(self._user_coord(p) for p in subset))
                label = f"{len(subset)}  {coords}"
            text_color = (255, 255, 255) if is_current else (200, 200, 205)
            text_surf = self._panel_font.render(label, True, text_color)
            text_x = sw.right + 8
            clip = pygame.Rect(text_x, row_y, interior.right - text_x, row_h)
            surface.set_clip(clip)
            surface.blit(text_surf, (text_x, row_y + 3))
            surface.set_clip(None)
            row_y += row_h

    def _draw_next_up_panel(self, surface: pygame.Surface, state: FrontendState, rect: pygame.Rect) -> None:
        if rect.width <= 0 or rect.height <= 0:
            return
        interior = self._draw_panel_background(surface, rect, "Up next")

        pq_top = state.playback.current_pq_top()
        if not pq_top:
            placeholder = self._panel_font.render(
                "Run A* to view the frontier.", True, (160, 160, 165)
            )
            surface.blit(placeholder, (interior.x, interior.y))
            return

        header = self._panel_small_font.render(
            "Sorted by f = g + h (cheapest pops first)", True, (170, 170, 175)
        )
        surface.blit(header, (interior.x, interior.y))
        list_y = interior.y + 18

        row_h = 38
        for i, (f_cost, pos, remaining) in enumerate(pq_top):
            row_top = list_y + i * row_h
            if row_top + row_h > interior.bottom:
                break

            color = self._color_for(remaining)
            row_rect = pygame.Rect(interior.x, row_top, interior.width, row_h - 4)
            bg = pygame.Surface(row_rect.size, pygame.SRCALPHA)
            bg.fill((*color, EXPLORED_STRIPE_ALPHA))
            surface.blit(bg, row_rect)
            pygame.draw.rect(surface, (70, 70, 78), row_rect, width=1)

            rank_label = self._panel_title_font.render(
                f"#{i + 1}", True, (255, 255, 255) if i == 0 else (210, 210, 215)
            )
            surface.blit(rank_label, (row_rect.x + 6, row_rect.y + 2))

            ur, uc = self._user_coord(pos)
            main_text = f"f={f_cost}  ({ur},{uc})"
            main_surf = self._panel_font.render(main_text, True, (255, 255, 255))
            surface.blit(main_surf, (row_rect.x + 40, row_rect.y + 2))

            sub_text = "all collected" if not remaining else f"{len(remaining)} left"
            sub_surf = self._panel_small_font.render(sub_text, True, (200, 200, 205))
            surface.blit(sub_surf, (row_rect.x + 40, row_rect.y + 20))

    def _draw_toast(self, surface: pygame.Surface, state: FrontendState, above_y: int | None = None) -> None:
        if not state.toast_message:
            return
        text_surface = self._font.render(state.toast_message, True, (255, 255, 255))
        padding_x = 12
        padding_y = 8
        toast_y = surface.get_height() - 46
        if above_y is not None:
            toast_y = max(8, above_y - 44)
        toast_rect = pygame.Rect(
            14, toast_y, text_surface.get_width() + padding_x * 2, 34
        )
        toast_bg = pygame.Surface((toast_rect.width, toast_rect.height), pygame.SRCALPHA)
        toast_bg.fill((0, 0, 0, 165))
        surface.blit(toast_bg, toast_rect)
        surface.blit(text_surface, (toast_rect.x + padding_x, toast_rect.y + padding_y))
