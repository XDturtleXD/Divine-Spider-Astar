"""Grid and render handler for snake scene rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from snake_scene import SceneState


@dataclass
class Grid:
    """Geometry helper that controls cell sizing and placement."""

    rows: int
    cols: int
    window_size: tuple[int, int]
    min_cell_px: int = 4

    def __post_init__(self) -> None:
        self.resize(self.window_size)

    def resize(self, window_size: tuple[int, int]) -> None:
        self.window_size = window_size
        width, height = window_size

        self.cell_w = max(self.min_cell_px, width // self.cols)
        self.cell_h = max(self.min_cell_px, height // self.rows)

        self.board_w = self.cell_w * self.cols
        self.board_h = self.cell_h * self.rows

        # Keep the board centered if the window is larger than required board space.
        self.offset_x = max(0, (width - self.board_w) // 2)
        self.offset_y = max(0, (height - self.board_h) // 2)

    def cell_size(self) -> tuple[int, int]:
        return (self.cell_w, self.cell_h)

    def cell_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            self.offset_x + col * self.cell_w,
            self.offset_y + row * self.cell_h,
            self.cell_w,
            self.cell_h,
        )


class SnakeRenderHandler:
    """Draws scene layers in a stable order using Grid geometry."""

    def __init__(self, assets_dir: str | Path, grid: Grid) -> None:
        self.assets_dir = Path(assets_dir)
        self.grid = grid
        self._base_border = pygame.image.load(str(self.assets_dir / "bolderTile.png")).convert_alpha()
        self._base_ground = pygame.image.load(str(self.assets_dir / "groundTile.png")).convert_alpha()
        self._base_snack = pygame.image.load(str(self.assets_dir / "Snack.png")).convert_alpha()

        self._border_tile: pygame.Surface | None = None
        self._ground_tile: pygame.Surface | None = None
        self._snack_tile: pygame.Surface | None = None
        self._cached_cell_size: tuple[int, int] | None = None
        self.reload_scaled_assets()

    def reload_scaled_assets(self) -> None:
        cell_size = self.grid.cell_size()
        self._border_tile = pygame.transform.smoothscale(self._base_border, cell_size)
        self._ground_tile = pygame.transform.smoothscale(self._base_ground, cell_size)
        self._snack_tile = pygame.transform.smoothscale(self._base_snack, cell_size)
        self._cached_cell_size = cell_size

    def draw(self, surface: pygame.Surface, state: SceneState) -> None:
        if self._cached_cell_size != self.grid.cell_size():
            self.reload_scaled_assets()

        assert self._border_tile is not None
        assert self._ground_tile is not None
        assert self._snack_tile is not None

        # Clear whole window first (outside-board background).
        surface.fill((20, 20, 20))

        # Layer 1: base board tiles.
        for row in range(state.rows):
            for col in range(state.cols):
                dest = self.grid.cell_rect(row, col)
                if (row, col) in state.borders:
                    surface.blit(self._border_tile, dest)
                else:
                    surface.blit(self._ground_tile, dest)

        # Layer 2: snacks/cakes.
        for row, col in state.snacks:
            surface.blit(self._snack_tile, self.grid.cell_rect(row, col))

        # Layer 3: snake body then head.
        for row, col in state.snake_body:
            pygame.draw.rect(surface, (255, 140, 0), self.grid.cell_rect(row, col))

        if state.snake_head is not None:
            row, col = state.snake_head
            pygame.draw.rect(surface, (220, 20, 60), self.grid.cell_rect(row, col))
