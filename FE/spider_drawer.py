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
        self._cost_font = pygame.font.SysFont("arial", 16)

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

        # Draw explored cells overlay: yellow for old, green for latest (no cost numbers)
        latest = state.playback.latest_explored()
        for (row, col), _ in state.playback.visible_explored_with_f():
            cell_rect = self.grid.cell_rect(row, col)
            overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
            overlay.fill((80, 220, 80, 180) if (row, col) == latest else (255, 220, 70, 110))
            surface.blit(overlay, cell_rect)

        # Draw top-3 frontier candidates — only during exploration, not in final PATH state
        if state.phase == AppPhase.EXPLORATION:
            next_cell = state.playback.next_cell()
            sub = state.playback.sub_step
            top_frontier = sorted(state.playback.current_frontier().items(), key=lambda x: x[1])[:3]
            for (row, col), f in top_frontier:
                is_selected = (row, col) == next_cell
                cell_rect = self.grid.cell_rect(row, col)

                # Blue overlay + f cost — skip on selected cell once it turns green (sub_step 2)
                if not (is_selected and sub >= 2):
                    overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
                    overlay.fill((80, 160, 255, 120))
                    surface.blit(overlay, cell_rect)
                    f_surf = self._cost_font.render(str(f), True, (10, 10, 80))
                    surface.blit(f_surf, (cell_rect.x + 2, cell_rect.y + 2))

                # Border logic:
                #   sub_step 0 — selected looks same as others (blue border + number, user sees it as candidate)
                #   sub_step 1 — selected border removed (border-removal animation)
                #   sub_step 2 — selected is green; others keep blue border
                if not (is_selected and sub >= 1):
                    pygame.draw.rect(surface, (80, 160, 255), cell_rect, 2)

        # Draw path as offset thin lines (non-overlapping for repeated edges)
        visible_path = state.playback.visible_path()
        if len(visible_path) >= 2:
            LINE_COLOR = (220, 35, 35)
            OFFSET_STEP = 4

            # Count total traversals per canonical edge
            total_count: dict = {}
            for a, b in zip(visible_path, visible_path[1:]):
                key = (min(a, b), max(a, b))
                total_count[key] = total_count.get(key, 0) + 1

            # Draw each segment with perpendicular offset by traversal slot
            seen: dict = {}
            for a, b in zip(visible_path, visible_path[1:]):
                key = (min(a, b), max(a, b))
                slot = seen.get(key, 0)
                seen[key] = slot + 1
                total = total_count[key]
                offset_val = (slot - (total - 1) / 2.0) * OFFSET_STEP
                dr = b[0] - a[0]
                if dr != 0:  # vertical movement → offset horizontally
                    ox, oy = int(offset_val), 0
                else:         # horizontal movement → offset vertically
                    ox, oy = 0, int(offset_val)
                ra = self.grid.cell_rect(*a).center
                rb = self.grid.cell_rect(*b).center
                pygame.draw.line(surface, LINE_COLOR, (ra[0] + ox, ra[1] + oy), (rb[0] + ox, rb[1] + oy), 3)

        elif len(visible_path) == 1:
            center = self.grid.cell_rect(*visible_path[0]).center
            pygame.draw.circle(surface, (220, 35, 35), center, 3)

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
