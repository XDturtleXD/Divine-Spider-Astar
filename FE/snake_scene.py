"""Shared scene constants and maze text conversion helpers."""

from __future__ import annotations

BOARD_ROWS = 10
BOARD_COLS = 10
MAX_SNACKS = 5


Position = tuple[int, int]


def build_maze_text(rows: int, cols: int, spider: Position, snacks: set[Position]) -> str:
    """Build backend maze text from frontend placements."""
    grid = [["." for _ in range(cols)] for _ in range(rows)]
    spider_row, spider_col = spider
    grid[spider_row][spider_col] = "H"

    for snack_row, snack_col in snacks:
        grid[snack_row][snack_col] = "*"

    return "\n".join("".join(row) for row in grid)
