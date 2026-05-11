"""Solver contract + backend adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Any
from pathlib import Path

from spider_scene import Position, build_maze_text


@dataclass(frozen=True)
class SolveResult:
    """Matches the final path and validation structure."""
    path: list[Position]
    validation_result: str


class BackendAdapter:
    """Calls BE `Maze` + `get_Astar_result` contract."""

    def create_solver_generator(
        self,
        rows: int,
        cols: int,
        spider: Position,
        snacks: set[Position],
    ) -> tuple[Generator[Position, None, list[Position]], Any]:
        """
        Creates a generator for the A* search process.
        Passes maze_text directly to the Maze class to avoid disk I/O.
        """
        maze_text = build_maze_text(rows, cols, spider, snacks)

        # Imported lazily.
        from backend import get_Astar_result  # type: ignore
        from maze import Maze  # type: ignore

        maze = Maze(maze_text)
        generator = get_Astar_result(maze)

        return generator, maze