"""Drawing logic for spider viewer scene: grid, entities, controls, toasts."""

from __future__ import annotations

import pygame

from spider_layout import Grid, UiRects, WindowLayout
from spider_assets import SpiderAssets
from frontend_state import AppPhase, FrontendState, PlacementTool
from spider_scene import MAX_SNACKS


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

    def draw(
        self,
        surface: pygame.Surface,
        state: FrontendState,
        window_layout: WindowLayout,
        ui_rects: UiRects,
    ) -> None:
        """Render full scene using precomputed layout data."""
        # Draw background
        surface.fill((20, 20, 20))

        # Draw grid cells and borders
        for row in range(-1, self.grid.rows + 1):
            for col in range(-1, self.grid.cols + 1):
                dest = self.grid.cell_rect(row, col)
                if row in (-1, self.grid.rows) or col in (-1, self.grid.cols):
                    surface.blit(self.assets.border_tile, dest)
                else:
                    surface.blit(self.assets.ground_tile, dest)

        # Draw explored cells overlay
        explored = state.playback.visible_explored()
        for row, col in explored:
            overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
            overlay.fill((255, 220, 70, 110))
            surface.blit(overlay, self.grid.cell_rect(row, col))

        # Draw path overlay
        visible_path = state.playback.visible_path()
        for row, col in visible_path:
            path_rect = self.grid.cell_rect(row, col)
            tint = pygame.Surface((path_rect.width, path_rect.height), pygame.SRCALPHA)
            tint.fill((220, 35, 35, 145))
            surface.blit(tint, path_rect)

        # Draw snacks (skip consumed ones during path/exploration)
        consumed = set(visible_path) if state.phase in (AppPhase.PATH, AppPhase.EXPLORATION) else set()
        for row, col in sorted(state.snacks):
            if (row, col) in consumed:
                continue
            surface.blit(self.assets.snack_tile, self.grid.cell_rect(row, col))

        # Draw spider
        spider_pos = state.spider
        if state.phase == AppPhase.PATH and visible_path:
            spider_pos = visible_path[-1]
        if spider_pos is not None:
            surface.blit(self.assets.spider_tile, self.grid.cell_rect(*spider_pos))

        # Draw UI controls and toast
        self._draw_controls(surface, state, ui_rects)
        self._draw_toast(surface, state, window_layout.button_strip.top)

    def _draw_controls(self, surface: pygame.Surface, state: FrontendState, ui_rects: UiRects) -> None:
        """Render bottom toolbar buttons with correct states."""
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

        reset_disabled = state.phase == AppPhase.PLACEMENT
        draw_button(
            surface,
            self.assets.reset_button_tints,
            ui_rects.reset_button,
            disabled=reset_disabled,
        )

    def _draw_toast(self, surface: pygame.Surface, state: FrontendState, above_y: int | None = None) -> None:
        """Render temporary toast message if present."""
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
