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
        self._badge_font = pygame.font.SysFont("arial", 11, bold=True)

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

        # Draw explored cells overlay: yellow for old, green for latest
        latest = state.playback.latest_explored()
        visit_counts = state.playback.position_visit_counts()
        current_remaining = state.playback.current_remaining()
        current_sh = state.playback.current_s_h()
        for (row, col), _g, _h in state.playback.visible_explored_with_costs():
            cell_rect = self.grid.cell_rect(row, col)
            is_latest = (row, col) == latest
            overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
            overlay.fill((80, 220, 80, 180) if is_latest else (255, 220, 70, 110))
            surface.blit(overlay, cell_rect)

            # Badge: show ×N when same position expanded multiple times (different snack states)
            if visit_counts.get((row, col), 1) > 1:
                self._draw_visit_badge(surface, cell_rect, visit_counts[(row, col)])

            # Latest cell: show g/h breakdown and snack dot count
            if is_latest:
                if current_sh is not None:
                    self._draw_gh_label(surface, cell_rect, current_sh[0], current_sh[1])
                if current_remaining is not None:
                    self._draw_snack_dots(surface, cell_rect, len(current_remaining))

        # Draw top-3 frontier candidates — only during exploration, not in final PATH state
        if state.phase == AppPhase.EXPLORATION:
            next_cell = state.playback.next_cell()
            sub = state.playback.sub_step
            top_frontier = sorted(state.playback.current_frontier().items(), key=lambda x: x[1][0] + x[1][1])[:3]
            for (row, col), (fg, fh) in top_frontier:
                is_selected = (row, col) == next_cell
                cell_rect = self.grid.cell_rect(row, col)

                # Blue overlay + g/h breakdown — skip on selected cell once it turns green (sub_step 2)
                if not (is_selected and sub >= 2):
                    overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
                    overlay.fill((80, 160, 255, 120))
                    surface.blit(overlay, cell_rect)
                    f_surf = self._cost_font.render(f"c={fg + fh}", True, (10, 10, 80))
                    gh_surf = self._badge_font.render(f"s={fg} h={fh}", True, (10, 10, 80))
                    surface.blit(f_surf, (cell_rect.x + 2, cell_rect.y + 2))
                    surface.blit(gh_surf, (cell_rect.x + 2, cell_rect.y + 2 + f_surf.get_height()))

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

    def _draw_gh_label(self, surface: pygame.Surface, cell_rect: pygame.Rect, s: int, h: int) -> None:
        """Show c=s+h breakdown at top-left of the currently expanded (green) cell."""
        c_surf = self._cost_font.render(f"c={s + h}", True, (255, 255, 255))
        sh_surf = self._badge_font.render(f"s={s} h={h}", True, (220, 220, 255))
        surface.blit(c_surf, (cell_rect.x + 2, cell_rect.y + 2))
        surface.blit(sh_surf, (cell_rect.x + 2, cell_rect.y + 2 + c_surf.get_height()))

    def _draw_visit_badge(self, surface: pygame.Surface, cell_rect: pygame.Rect, count: int) -> None:
        """Draw ×N badge at top-right of cell when same position expanded N times."""
        text_surf = self._badge_font.render(f"\xd7{count}", True, (255, 220, 100))
        bg_w = text_surf.get_width() + 4
        bg_h = text_surf.get_height() + 2
        bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        bx = cell_rect.right - bg_w
        surface.blit(bg, (bx, cell_rect.top))
        surface.blit(text_surf, (bx + 2, cell_rect.top + 1))

    def _draw_snack_dots(self, surface: pygame.Surface, cell_rect: pygame.Rect, count: int) -> None:
        """Draw orange dots at bottom of cell indicating remaining snack count in current A* state."""
        if count == 0:
            return
        dot_r = 3
        spacing = 8
        total_w = (count - 1) * spacing
        cx_start = cell_rect.centerx - total_w // 2
        cy = cell_rect.bottom - 6
        for i in range(count):
            pygame.draw.circle(surface, (255, 150, 30), (cx_start + i * spacing, cy), dot_r)

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
