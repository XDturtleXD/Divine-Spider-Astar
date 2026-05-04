"""Solver contract + backend adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from spider_scene import Position, build_maze_text


@dataclass(frozen=True)
class SolveResult:
    explored_positions: list[Position]
    path: list[Position]
    validation_result: str


class BackendAdapter:
    """Calls BE `Maze` + `get_Astar_result` contract."""

    def solve(self, rows: int, cols: int, spider: Position, snacks: set[Position]) -> SolveResult:
        maze_text = build_maze_text(rows, cols, spider, snacks)
        explored_positions: list[Position] = []
        path: list[Position] = []

        # Imported lazily.
        from backend import get_Astar_result  # type: ignore
        from maze import Maze  # type: ignore

        with tempfile.TemporaryDirectory(prefix="spider_maze_") as temp_dir:
            maze_path = Path(temp_dir) / "frontend_generated_maze.txt"
            maze_path.write_text(maze_text, encoding="utf-8")
            maze = Maze(str(maze_path))
            generator = get_Astar_result(maze)
            try:
                while True:
                    explored_positions.append(next(generator))
            except StopIteration as stop_signal:
                path = stop_signal.value or []

            validation = maze.isValidPath(path)
            return SolveResult(
                explored_positions=explored_positions,
                path=path,
                validation_result=validation,
            )
