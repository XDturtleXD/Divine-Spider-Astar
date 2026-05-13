"""Grid and renderer for interactive spider viewer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pygame

from frontend_state import AppPhase, FrontendState, PlacementTool
from spider_scene import MAX_SNACKS, Position


# One tile ring around playable cells (indices -1 … rows inclusive).
VISIBLE_EXTRA_CELLS = 2

# Right-side layer panel sizing.
LAYER_PANEL_WIDTH = 140
LAYER_PANEL_GAP = 8
LAYER_SLOT_PAD = 8


@dataclass(frozen=True)
class WindowLayout:
    """Layout rects for the main grid area, right-side layer panel, and bottom toolbar.

    The play field (square grid + border) is derived in `Grid` via
    `fit_square_cells_in_rect`; this layout only carries the surrounding rects.
    """

    button_strip: pygame.Rect
    layer_panel: pygame.Rect


def trim_sprite_to_opaque_bounds(surface: pygame.Surface) -> pygame.Surface:
    """Remove fully transparent margin from a sprite; keeps pixel art crisp."""
    try:
        mask = pygame.mask.from_surface(surface, 127)
    except (TypeError, ValueError):
        return surface
    rects = mask.get_bounding_rects()
    if not rects:
        return surface
    combined = rects[0].unionall(rects[1:]) if len(rects) > 1 else rects[0]
    return surface.subsurface(combined).copy()


def fit_surface_to_rect(surface: pygame.Surface, target: pygame.Rect) -> pygame.Surface:
    """Uniformly scale preserving aspect ratio; callers center-blit."""
    tw, th = target.width, target.height
    iw, ih = surface.get_width(), surface.get_height()
    if iw <= 0 or ih <= 0:
        return surface
    scale = min(tw / iw, th / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    return pygame.transform.scale(surface, (nw, nh))


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
        return self.rows + VISIBLE_EXTRA_CELLS

    @property
    def visible_cols(self) -> int:
        return self.cols + VISIBLE_EXTRA_CELLS

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
    spider_button: pygame.Rect
    snack_button: pygame.Rect
    run_button: pygame.Rect
    reset_button: pygame.Rect
    layer_slot_rects: list[pygame.Rect] = field(default_factory=list)


class SpiderRenderHandler:
    """Draw scene and controls in a stable order."""

    _MARGIN_SIDE = 8
    _MARGIN_TOP = 8
    _MARGIN_BOTTOM = 8
    _BUTTON_GAP = 14
    _BUTTON_STRIP_MIN_H = 100
    _BUTTON_STRIP_PAD_Y = 10

    def __init__(self, assets_dir: str | Path, grid: Grid) -> None:
        self.assets_dir = Path(assets_dir)
        self.grid = grid
        raw_border = pygame.image.load(str(self.assets_dir / "bolderTile.png")).convert_alpha()
        raw_ground = pygame.image.load(str(self.assets_dir / "groundTile.png")).convert_alpha()
        self._src_border = raw_border
        self._src_ground = raw_ground

        raw_run = pygame.image.load(str(self.assets_dir / "start_button.png")).convert_alpha()
        raw_reset = pygame.image.load(str(self.assets_dir / "restart_button.png")).convert_alpha()
        raw_sn_btn = pygame.image.load(str(self.assets_dir / "place_snack_button.png")).convert_alpha()
        raw_layer = pygame.image.load(str(self.assets_dir / "layer.png")).convert_alpha()

        self._src_snack = pygame.image.load(str(self.assets_dir / "Snack.png")).convert_alpha()
        self._src_spider = pygame.image.load(str(self.assets_dir / "Spider.png")).convert_alpha()

        self._btn_run_trim = trim_sprite_to_opaque_bounds(raw_run)
        self._btn_reset_trim = trim_sprite_to_opaque_bounds(raw_reset)
        self._btn_snack_trim = trim_sprite_to_opaque_bounds(raw_sn_btn)
        self._btn_spider_trim = trim_sprite_to_opaque_bounds(self._src_spider)
        self._layer_tile_trim = trim_sprite_to_opaque_bounds(raw_layer)

        self._border_tile: pygame.Surface | None = None
        self._ground_tile: pygame.Surface | None = None
        self._snack_tile: pygame.Surface | None = None
        self._spider_tile: pygame.Surface | None = None
        self._run_button_surface: pygame.Surface | None = None
        self._reset_button_surface: pygame.Surface | None = None
        self._snack_button_surface: pygame.Surface | None = None
        self._spider_button_surface: pygame.Surface | None = None
        self._cached_cell_s: int = -1
        self._last_window_size: tuple[int, int] = (0, 0)
        self._last_button_strip_height: int = self._BUTTON_STRIP_MIN_H
        self._font = pygame.font.SysFont("arial", 18)

    def compute_window_layout(self, surface: pygame.Surface) -> WindowLayout:
        """Partition window into: top-left play field, top-right layer panel, bottom buttons.

        The right-side `layer_panel` is sized via `LAYER_PANEL_WIDTH` but
        clamped on narrow windows so the play grid still gets enough width.
        """
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

        # Carve right-side layer panel; clamp on narrow windows.
        panel_w = min(LAYER_PANEL_WIDTH, max(60, inner_w // 4))
        play_w = max(1, inner_w - panel_w - LAYER_PANEL_GAP)

        play_rect = pygame.Rect(
            self._MARGIN_SIDE,
            self._MARGIN_TOP,
            play_w,
            play_h,
        )
        layer_panel = pygame.Rect(
            self._MARGIN_SIDE + play_w + LAYER_PANEL_GAP,
            self._MARGIN_TOP,
            panel_w,
            play_h,
        )
        button_strip = pygame.Rect(
            self._MARGIN_SIDE,
            self._MARGIN_TOP + play_h,
            inner_w,
            strip_h,
        )

        self.grid.fit_square_cells_in_rect(play_rect)

        self._last_button_strip_height = strip_h

        return WindowLayout(button_strip=button_strip, layer_panel=layer_panel)

    def _resolve_button_strip_height(self, inner_w: int) -> int:
        """Reserve a strip tall enough for four scaled button icons in a row."""
        gap = self._BUTTON_GAP
        slot_w = max(48, (inner_w - gap * 3) // 4)
        refs = [self._btn_run_trim, self._btn_reset_trim, self._btn_snack_trim, self._btn_spider_trim]
        max_h = max(s.get_height() for s in refs)
        scale = min(1.0, slot_w / max(s.get_width() for s in refs))
        row_h = int(max_h * scale) + 2 * self._BUTTON_STRIP_PAD_Y
        return max(self._BUTTON_STRIP_MIN_H, row_h)

    def apply_layout(self, surface: pygame.Surface, num_layer_slots: int = 1) -> tuple[WindowLayout, UiRects]:
        """Recompute layout for current window size; updates grid + assets if needed.

        `num_layer_slots` controls how many layer hit-boxes go into `UiRects`
        (callers pass `max(1, len(state.layers))`).
        """
        ww, wh = surface.get_size()
        layout = self.compute_window_layout(surface)
        if (
            (ww, wh) != self._last_window_size
            or self._cached_cell_s != self.grid.cell_s
        ):
            self._last_window_size = (ww, wh)
            self._cached_cell_s = self.grid.cell_s
            self.reload_scaled_assets()
        ui = self.compute_ui_rects(layout, num_layer_slots)
        return layout, ui

    def reload_scaled_assets(self) -> None:
        cell_s = max(1, self.grid.cell_s)
        self._border_tile = pygame.transform.scale(self._src_border, (cell_s, cell_s))
        self._ground_tile = pygame.transform.scale(self._src_ground, (cell_s, cell_s))
        self._snack_tile = pygame.transform.scale(self._src_snack, (cell_s, cell_s))
        self._spider_tile = pygame.transform.scale(self._src_spider, (cell_s, cell_s))

        ww = max(self._last_window_size[0], 320)
        inner_w = max(1, ww - 2 * self._MARGIN_SIDE)
        gap = self._BUTTON_GAP
        slot_w = max(40, (inner_w - gap * 3) // 4)
        strip_inner_h = max(32, self._last_button_strip_height - 2 * self._BUTTON_STRIP_PAD_Y)
        slot_rect = pygame.Rect(0, 0, slot_w, strip_inner_h)

        self._run_button_surface = fit_surface_to_rect(self._btn_run_trim, slot_rect)
        self._reset_button_surface = fit_surface_to_rect(self._btn_reset_trim, slot_rect)
        self._snack_button_surface = fit_surface_to_rect(self._btn_snack_trim, slot_rect)
        self._spider_button_surface = fit_surface_to_rect(self._btn_spider_trim, slot_rect)

    def compute_ui_rects(self, layout: WindowLayout, num_layer_slots: int = 1) -> UiRects:
        """Lay out toolbar buttons inside button_strip and layer slots inside layer_panel."""
        strip = layout.button_strip
        gap = self._BUTTON_GAP
        pad_x = 12
        inner = pygame.Rect(
            strip.x + pad_x,
            strip.y + self._BUTTON_STRIP_PAD_Y,
            max(1, strip.width - 2 * pad_x),
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
            layer_slot_rects=self._compute_layer_slot_rects(layout.layer_panel, num_layer_slots),
        )

    def _compute_layer_slot_rects(self, panel: pygame.Rect, num_slots: int) -> list[pygame.Rect]:
        """Vertical stack of slot rects inside `panel`. Caps at MAX_SNACKS + 1."""
        cap = MAX_SNACKS + 1
        num_slots = max(1, min(num_slots, cap))
        pad = LAYER_SLOT_PAD
        available_h = max(1, panel.height - 2 * pad)
        slot_h = max(1, available_h // num_slots)
        slot_w = max(1, panel.width - 2 * pad)
        rects: list[pygame.Rect] = []
        for i in range(num_slots):
            rects.append(
                pygame.Rect(
                    panel.x + pad,
                    panel.y + pad + i * slot_h,
                    slot_w,
                    slot_h,
                )
            )
        return rects

    def draw(self, surface: pygame.Surface, state: FrontendState) -> UiRects:
        num_slots = max(1, len(state.layers))
        layout, ui_rects = self.apply_layout(surface, num_slots)

        assert self._border_tile is not None
        assert self._ground_tile is not None
        assert self._snack_tile is not None
        assert self._spider_tile is not None

        surface.fill((20, 20, 20))

        for row in range(-1, self.grid.rows + 1):
            for col in range(-1, self.grid.cols + 1):
                dest = self.grid.cell_rect(row, col)
                if row in (-1, self.grid.rows) or col in (-1, self.grid.cols):
                    surface.blit(self._border_tile, dest)
                else:
                    surface.blit(self._ground_tile, dest)

        in_sub_step = (
            state.phase == AppPhase.PATH
            and state.layers
            and 0 <= state.selected_layer < len(state.layers)
        )

        if in_sub_step:
            self._draw_sub_step_view(surface, state)
        else:
            self._draw_global_view(surface, state)

        self._draw_layer_panel(surface, state, layout.layer_panel, ui_rects.layer_slot_rects)
        self._draw_controls(surface, state, ui_rects)
        self._draw_toast(surface, state, layout.button_strip.top)
        return ui_rects

    def _draw_global_view(self, surface: pygame.Surface, state: FrontendState) -> None:
        """Original full-board rendering for PLACEMENT / EXPLORATION phases."""
        assert self._snack_tile is not None
        assert self._spider_tile is not None

        explored = state.playback.visible_explored()
        for row, col in explored:
            overlay = pygame.Surface((self.grid.cell_s, self.grid.cell_s), pygame.SRCALPHA)
            overlay.fill((255, 220, 70, 110))
            surface.blit(overlay, self.grid.cell_rect(row, col))

        visible_path = state.playback.visible_path()
        for row, col in visible_path:
            path_rect = self.grid.cell_rect(row, col)
            tint = pygame.Surface((path_rect.width, path_rect.height), pygame.SRCALPHA)
            tint.fill((220, 35, 35, 145))
            surface.blit(tint, path_rect)

        consumed = set(visible_path) if state.phase in (AppPhase.PATH, AppPhase.EXPLORATION) else set()
        for row, col in sorted(state.snacks):
            if (row, col) in consumed:
                continue
            surface.blit(self._snack_tile, self.grid.cell_rect(row, col))

        spider_pos = state.spider
        if state.phase == AppPhase.PATH and visible_path:
            spider_pos = visible_path[-1]
        if spider_pos is not None:
            surface.blit(self._spider_tile, self.grid.cell_rect(*spider_pos))

    def _draw_sub_step_view(self, surface: pygame.Surface, state: FrontendState) -> None:
        """Per-layer view: only this layer's snacks + within-layer path + spider head."""
        assert self._snack_tile is not None
        assert self._spider_tile is not None

        layer = state.layers[state.selected_layer]
        # Clamp animation index within this layer's segment.
        visible_within = max(0, min(state.playback.path_index, len(layer.segment)))

        path_cells: list[Position] = [layer.entry] + list(layer.segment[:visible_within])
        for row, col in path_cells:
            path_rect = self.grid.cell_rect(row, col)
            tint = pygame.Surface((path_rect.width, path_rect.height), pygame.SRCALPHA)
            tint.fill((220, 35, 35, 145))
            surface.blit(tint, path_rect)

        # The segment ends at this layer's target snack; once fully walked, hide it.
        eaten_now: set[Position] = set()
        if layer.segment and visible_within == len(layer.segment):
            eaten_now.add(layer.segment[-1])
        for row, col in layer.snacks_remaining:
            if (row, col) in eaten_now:
                continue
            surface.blit(self._snack_tile, self.grid.cell_rect(row, col))

        spider_pos: Position = layer.entry if visible_within == 0 else layer.segment[visible_within - 1]
        surface.blit(self._spider_tile, self.grid.cell_rect(*spider_pos))

    def _blit_icon_centered(self, surface: pygame.Surface, icon: pygame.Surface, slot: pygame.Rect) -> None:
        r = icon.get_rect(center=slot.center)
        surface.blit(icon, r)

    def _draw_controls(self, surface: pygame.Surface, state: FrontendState, ui_rects: UiRects) -> None:
        assert self._run_button_surface is not None
        assert self._reset_button_surface is not None
        assert self._snack_button_surface is not None
        assert self._spider_button_surface is not None

        self._draw_mode_button(
            surface,
            rect=ui_rects.spider_button,
            icon=self._spider_button_surface,
            active=(state.active_tool == PlacementTool.SPIDER),
            disabled=(state.phase != AppPhase.PLACEMENT),
        )
        self._draw_mode_button(
            surface,
            rect=ui_rects.snack_button,
            icon=self._snack_button_surface,
            active=(state.active_tool == PlacementTool.SNACK),
            disabled=(state.phase != AppPhase.PLACEMENT or len(state.snacks) >= MAX_SNACKS),
        )

        run_disabled = state.phase != AppPhase.PLACEMENT or not state.can_run()
        self._draw_action_button(surface, ui_rects.run_button, self._run_button_surface, run_disabled)
        reset_disabled = state.phase == AppPhase.PLACEMENT
        self._draw_action_button(surface, ui_rects.reset_button, self._reset_button_surface, reset_disabled)

    def _blit_tint_overlay(self, surface: pygame.Surface, rect: pygame.Rect, rgb: tuple[int, int, int], alpha: int) -> None:
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*rgb, alpha))
        surface.blit(overlay, rect)

    def _blit_disabled_overlay(self, surface: pygame.Surface, rect: pygame.Rect, alpha: int) -> None:
        self._blit_tint_overlay(surface, rect, (40, 40, 40), alpha)

    def _draw_mode_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        icon: pygame.Surface,
        active: bool,
        disabled: bool,
    ) -> None:
        self._blit_icon_centered(surface, icon, rect)
        if disabled:
            self._blit_disabled_overlay(surface, rect, 150)
        elif active:
            self._blit_tint_overlay(surface, rect, (50, 220, 150), 100)
        else:
            self._blit_tint_overlay(surface, rect, (0, 0, 0), 55)

    def _draw_action_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        icon: pygame.Surface,
        disabled: bool,
    ) -> None:
        self._blit_icon_centered(surface, icon, rect)
        if disabled:
            self._blit_disabled_overlay(surface, rect, 160)

    def _draw_layer_panel(
        self,
        surface: pygame.Surface,
        state: FrontendState,
        panel: pygame.Rect,
        slots: list[pygame.Rect],
    ) -> None:
        """Render the right-side layer selector.

        - Placement phase OR no layers yet: all slots dim (disabled), labelled "—".
        - Selected layer: teal outline.
        - Other layers: dimmed via dark overlay (so the selected one pops).
        """
        bg = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        bg.fill((35, 35, 40, 200))
        surface.blit(bg, panel)

        disabled = state.phase == AppPhase.PLACEMENT or not state.layers

        for i, slot in enumerate(slots):
            # Reserve bottom strip for the label so icon never overlaps text.
            label_band_h = min(22, max(14, slot.height // 4))
            icon_target = pygame.Rect(
                slot.x + 6,
                slot.y + 6,
                max(1, slot.width - 12),
                max(1, slot.height - 12 - label_band_h),
            )
            icon = fit_surface_to_rect(self._layer_tile_trim, icon_target)
            icon_rect = icon.get_rect(center=icon_target.center)
            surface.blit(icon, icon_rect)

            label_text = f"Layer {i}" if state.layers else "—"
            text = self._font.render(label_text, True, (220, 220, 220))
            text_rect = text.get_rect(center=(slot.centerx, slot.bottom - label_band_h // 2 - 2))
            surface.blit(text, text_rect)

            if disabled:
                self._blit_disabled_overlay(surface, slot, 160)
            elif i == state.selected_layer:
                pygame.draw.rect(surface, (80, 220, 180), slot, 3, border_radius=4)
            else:
                self._blit_disabled_overlay(surface, slot, 95)

    def _draw_toast(self, surface: pygame.Surface, state: FrontendState, above_y: int | None = None) -> None:
        if not state.toast_message:
            return
        text_surface = self._font.render(state.toast_message, True, (255, 255, 255))
        padding_x = 12
        padding_y = 8
        toast_y = surface.get_height() - 46
        if above_y is not None:
            toast_y = max(8, above_y - 44)
        toast_rect = pygame.Rect(14, toast_y, text_surface.get_width() + padding_x * 2, 34)
        toast_bg = pygame.Surface((toast_rect.width, toast_rect.height), pygame.SRCALPHA)
        toast_bg.fill((0, 0, 0, 165))
        surface.blit(toast_bg, toast_rect)
        surface.blit(text_surface, (toast_rect.x + padding_x, toast_rect.y + padding_y))
