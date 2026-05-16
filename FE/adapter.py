"""Backend bridge: maze text and A* generator."""

from __future__ import annotations

from typing import Any, Generator

from config import Position, build_maze_text


class BackendAdapter:
    """Calls BE `Maze` + `get_Astar_result` contract."""

    def create_solver_generator(
        self,
        rows: int,
        cols: int,
        spider: Position,
        snacks: set[Position],
    ) -> tuple[Generator[dict[str, Any], None, list[Position]], Any]:
        maze_text = build_maze_text(rows, cols, spider, snacks)

        from backend import get_Astar_result  # type: ignore
        from maze import Maze  # type: ignore

        maze = Maze(maze_text)
        generator = get_Astar_result(maze)

        return generator, maze
