"""Solver contract + backend adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from spider_scene import Position, build_maze_text


@dataclass(frozen=True)
class SolveResult:
    explored_positions: list[Position]
    explored_f_costs: list[int]
    explored_frontiers: list[dict[Position, int]]
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

        explored_f_costs: list[int] = []
        explored_frontiers: list[dict[Position, int]] = []

        with tempfile.TemporaryDirectory(prefix="spider_maze_") as temp_dir:
            maze_path = Path(temp_dir) / "frontend_generated_maze.txt"
            maze_path.write_text(maze_text, encoding="utf-8")
            maze = Maze(str(maze_path))
            generator = get_Astar_result(maze)
            try:
                while True:
                    pos, f, frontier = next(generator)
                    explored_positions.append(pos)
                    explored_f_costs.append(f)
                    explored_frontiers.append(frontier)
            except StopIteration as stop_signal:
                path = stop_signal.value or []

            validation = maze.isValidPath(path)
            return SolveResult(
                explored_positions=explored_positions,
                explored_f_costs=explored_f_costs,
                explored_frontiers=explored_frontiers,
                path=path,
                validation_result=validation,
            )
