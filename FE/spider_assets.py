"""Asset loading, trimming, and scaling for the spider renderer."""

from __future__ import annotations

from pathlib import Path

import pygame


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


def draw_tint_overlay(surface: pygame.Surface, rect: pygame.Rect, rgb: tuple[int, int, int], alpha: int) -> None:
    """Draw a semi-transparent tint overlay over a rect."""
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((*rgb, alpha))
    surface.blit(overlay, rect)


class SpiderAssets:
    """Loads, trims, and scales sprites for the spider grid renderer."""

    def __init__(self, assets_dir: str | Path) -> None:
        self.assets_dir = Path(assets_dir)

        self.src_border = pygame.image.load(str(self.assets_dir / "bolderTile.png")).convert_alpha()
        self.src_ground = pygame.image.load(str(self.assets_dir / "groundTile.png")).convert_alpha()

        raw_run = pygame.image.load(str(self.assets_dir / "start_button.png")).convert_alpha()
        raw_reset = pygame.image.load(str(self.assets_dir / "restart_button.png")).convert_alpha()
        raw_sn_btn = pygame.image.load(str(self.assets_dir / "place_snack_button.png")).convert_alpha()

        self.src_snack = pygame.image.load(str(self.assets_dir / "Snack.png")).convert_alpha()
        self.src_spider = pygame.image.load(str(self.assets_dir / "Spider.png")).convert_alpha()

        self.btn_run_trim = trim_sprite_to_opaque_bounds(raw_run)
        self.btn_reset_trim = trim_sprite_to_opaque_bounds(raw_reset)
        self.btn_snack_trim = trim_sprite_to_opaque_bounds(raw_sn_btn)
        self.btn_spider_trim = trim_sprite_to_opaque_bounds(self.src_spider)

        self.trimmed_buttons = [self.btn_run_trim, self.btn_reset_trim, self.btn_snack_trim, self.btn_spider_trim]
        self.trimmed_max_height = max(s.get_height() for s in self.trimmed_buttons)
        self.trimmed_max_width = max(s.get_width() for s in self.trimmed_buttons)

        self.border_tile: pygame.Surface | None = None
        self.ground_tile: pygame.Surface | None = None
        self.snack_tile: pygame.Surface | None = None
        self.spider_tile: pygame.Surface | None = None
        self.run_button_surface: pygame.Surface | None = None
        self.reset_button_surface: pygame.Surface | None = None
        self.snack_button_surface: pygame.Surface | None = None
        self.spider_button_surface: pygame.Surface | None = None

    def reload_scaled(
        self,
        cell_s: int,
        window_size: tuple[int, int],
        button_strip_height: int,
        margin_side: int = 8,
        button_gap: int = 14,
        button_strip_pad_y: int = 10,
    ) -> None:
        """Recompute all cached scaled surfaces from source assets."""
        cell_s = max(1, cell_s)
        self.border_tile = pygame.transform.scale(self.src_border, (cell_s, cell_s))
        self.ground_tile = pygame.transform.scale(self.src_ground, (cell_s, cell_s))
        self.snack_tile = pygame.transform.scale(self.src_snack, (cell_s, cell_s))
        self.spider_tile = pygame.transform.scale(self.src_spider, (cell_s, cell_s))

        ww = max(window_size[0], 320)
        inner_w = max(1, ww - 2 * margin_side)
        gap = button_gap
        slot_w = max(40, (inner_w - gap * 3) // 4)
        strip_inner_h = max(32, button_strip_height - 2 * button_strip_pad_y)
        slot_rect = pygame.Rect(0, 0, slot_w, strip_inner_h)

        self.run_button_surface = fit_surface_to_rect(self.btn_run_trim, slot_rect)
        self.reset_button_surface = fit_surface_to_rect(self.btn_reset_trim, slot_rect)
        self.snack_button_surface = fit_surface_to_rect(self.btn_snack_trim, slot_rect)
        self.spider_button_surface = fit_surface_to_rect(self.btn_spider_trim, slot_rect)

    def draw_border_tile(self, surface: pygame.Surface, dest: pygame.Rect) -> None:
        assert self.border_tile
        surface.blit(self.border_tile, dest)

    def draw_ground_tile(self, surface: pygame.Surface, dest: pygame.Rect) -> None:
        assert self.ground_tile
        surface.blit(self.ground_tile, dest)

    def draw_snack_tile(self, surface: pygame.Surface, dest: pygame.Rect) -> None:
        assert self.snack_tile
        surface.blit(self.snack_tile, dest)

    def draw_spider_tile(self, surface: pygame.Surface, dest: pygame.Rect) -> None:
        assert self.spider_tile
        surface.blit(self.spider_tile, dest)

    def draw_spider_button(self, surface: pygame.Surface, rect: pygame.Rect, disabled: bool = False, active: bool = False) -> None:
        assert self.spider_button_surface
        r = self.spider_button_surface.get_rect(center=rect.center)
        surface.blit(self.spider_button_surface, r)
        if disabled:
            draw_tint_overlay(surface, rect, (40, 40, 40), 150)
        elif active:
            draw_tint_overlay(surface, rect, (50, 220, 150), 100)
        else:
            draw_tint_overlay(surface, rect, (0, 0, 0), 55)

    def draw_snack_button(self, surface: pygame.Surface, rect: pygame.Rect, disabled: bool = False, active: bool = False) -> None:
        assert self.snack_button_surface
        r = self.snack_button_surface.get_rect(center=rect.center)
        surface.blit(self.snack_button_surface, r)
        if disabled:
            draw_tint_overlay(surface, rect, (40, 40, 40), 150)
        elif active:
            draw_tint_overlay(surface, rect, (50, 220, 150), 100)
        else:
            draw_tint_overlay(surface, rect, (0, 0, 0), 55)

    def draw_run_button(self, surface: pygame.Surface, rect: pygame.Rect, disabled: bool = False) -> None:
        assert self.run_button_surface
        r = self.run_button_surface.get_rect(center=rect.center)
        surface.blit(self.run_button_surface, r)
        if disabled:
            draw_tint_overlay(surface, rect, (40, 40, 40), 160)

    def draw_reset_button(self, surface: pygame.Surface, rect: pygame.Rect, disabled: bool = False) -> None:
        assert self.reset_button_surface
        r = self.reset_button_surface.get_rect(center=rect.center)
        surface.blit(self.reset_button_surface, r)
        if disabled:
            draw_tint_overlay(surface, rect, (40, 40, 40), 160)
