"""Asset loading, trimming, and scaling for the viewer."""

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


def fit_surface_to_height(surface: pygame.Surface, target_h: int) -> pygame.Surface:
    """Scale so height matches target_h; width follows aspect ratio."""
    ih = surface.get_height()
    if ih <= 0:
        return surface
    scale = target_h / ih
    nw = max(1, int(round(surface.get_width() * scale)))
    nh = max(1, target_h)
    return pygame.transform.scale(surface, (nw, nh))


def _toolbar_width_at_height(trims: tuple[pygame.Surface, ...], target_h: int) -> int:
    total = 0
    for surf in trims:
        ih = surf.get_height()
        if ih <= 0:
            continue
        total += max(1, int(round(surf.get_width() * target_h / ih)))
    return total


def tint_surface(surface: pygame.Surface, rgba: tuple[int, int, int, int]) -> pygame.Surface:
    """Apply a color tint only on non-transparent pixels."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill(rgba)
    alpha_mask = surface.copy()
    alpha_mask.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
    overlay.blit(alpha_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    tinted = surface.copy()
    tinted.blit(overlay, (0, 0))
    return tinted


def build_button_tints(surface: pygame.Surface) -> dict[str, pygame.Surface]:
    return {
        "normal": tint_surface(surface, (0, 0, 0, 55)),
        "disabled": tint_surface(surface, (40, 40, 40, 150)),
        "active": tint_surface(surface, (50, 220, 150, 100)),
    }


class SpiderAssets:
    """Loads, trims, and scales sprites for the grid renderer."""

    def __init__(self, assets_dir: str | Path) -> None:
        self.assets_dir = Path(assets_dir)

        self._src_border = pygame.image.load(str(self.assets_dir / "bolderTile.png")).convert_alpha()
        self._src_ground = pygame.image.load(str(self.assets_dir / "groundTile.png")).convert_alpha()

        raw_run = pygame.image.load(str(self.assets_dir / "start_button.png")).convert_alpha()
        raw_reset = pygame.image.load(str(self.assets_dir / "restart_button.png")).convert_alpha()
        raw_sn_btn = pygame.image.load(str(self.assets_dir / "place_snack_button.png")).convert_alpha()
        raw_pause = pygame.image.load(str(self.assets_dir / "pause.png")).convert_alpha()
        raw_resume = pygame.image.load(str(self.assets_dir / "Resume.png")).convert_alpha()

        self._src_snack = pygame.image.load(str(self.assets_dir / "Snack.png")).convert_alpha()
        self._src_spider = pygame.image.load(str(self.assets_dir / "Spider.png")).convert_alpha()

        self._btn_run_trim = trim_sprite_to_opaque_bounds(raw_run)
        self._btn_reset_trim = trim_sprite_to_opaque_bounds(raw_reset)
        self._btn_snack_trim = trim_sprite_to_opaque_bounds(raw_sn_btn)
        self._btn_spider_trim = trim_sprite_to_opaque_bounds(self._src_spider)
        self._btn_pause_trim = trim_sprite_to_opaque_bounds(raw_pause)
        self._btn_resume_trim = trim_sprite_to_opaque_bounds(raw_resume)

        trimmed_buttons = [
            self._btn_run_trim,
            self._btn_reset_trim,
            self._btn_snack_trim,
            self._btn_spider_trim,
            self._btn_pause_trim,
            self._btn_resume_trim,
        ]
        self.trimmed_max_height = max(s.get_height() for s in trimmed_buttons)
        self.trimmed_max_width = max(s.get_width() for s in trimmed_buttons)

        self.border_tile = self._src_border
        self.ground_tile = self._src_ground
        self.snack_tile = self._src_snack
        self.spider_tile = self._src_spider
        self.run_button_tints = build_button_tints(self._btn_run_trim)
        self.reset_button_tints = build_button_tints(self._btn_reset_trim)
        self.snack_button_tints = build_button_tints(self._btn_snack_trim)
        self.spider_button_tints = build_button_tints(self._btn_spider_trim)
        self.pause_button_tints = build_button_tints(self._btn_pause_trim)
        self.resume_button_tints = build_button_tints(self._btn_resume_trim)

        self.toolbar_height = self.trimmed_max_height
        self.spider_button_size = self._btn_spider_trim.get_size()
        self.snack_button_size = self._btn_snack_trim.get_size()
        self.run_button_size = self._btn_run_trim.get_size()
        self.pause_button_size = self._btn_pause_trim.get_size()
        self.resume_button_size = self._btn_resume_trim.get_size()
        self.reset_button_size = self._btn_reset_trim.get_size()

    def _scale_toolbar_buttons(
        self,
        target_h: int,
        inner_w: int,
        gap: int,
    ) -> int:
        """Scale all toolbar sprites to the same height; shrink h until row fits inner_w."""
        trims = (
            self._btn_spider_trim,
            self._btn_snack_trim,
            self._btn_run_trim,
            self._btn_pause_trim,
            self._btn_reset_trim,
        )
        h = min(target_h, self.trimmed_max_height)
        min_h = 28
        gaps_total = gap * 4
        while h >= min_h:
            if _toolbar_width_at_height(trims, h) + gaps_total <= inner_w:
                break
            h -= 1
        h = max(min_h, h)

        def apply(trim: pygame.Surface) -> tuple[dict[str, pygame.Surface], tuple[int, int]]:
            scaled = fit_surface_to_height(trim, h)
            return build_button_tints(scaled), scaled.get_size()

        self.toolbar_height = h
        self.spider_button_tints, self.spider_button_size = apply(self._btn_spider_trim)
        self.snack_button_tints, self.snack_button_size = apply(self._btn_snack_trim)
        self.run_button_tints, self.run_button_size = apply(self._btn_run_trim)
        self.pause_button_tints, self.pause_button_size = apply(self._btn_pause_trim)
        self.resume_button_tints, self.resume_button_size = apply(self._btn_resume_trim)
        self.reset_button_tints, self.reset_button_size = apply(self._btn_reset_trim)
        return h

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
        self.border_tile = pygame.transform.scale(self._src_border, (cell_s, cell_s))
        self.ground_tile = pygame.transform.scale(self._src_ground, (cell_s, cell_s))
        self.snack_tile = pygame.transform.scale(self._src_snack, (cell_s, cell_s))
        self.spider_tile = pygame.transform.scale(self._src_spider, (cell_s, cell_s))

        ww = max(window_size[0], 320)
        inner_w = max(1, ww - 2 * margin_side)
        strip_inner_h = max(32, button_strip_height - 2 * button_strip_pad_y)
        self._scale_toolbar_buttons(strip_inner_h, inner_w, button_gap)
