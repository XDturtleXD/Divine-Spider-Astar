"""Deterministic simulation adapter for frontend rendering tests."""

from __future__ import annotations

from enum import Enum

from backend_adapter import BackendAdapter, SolveResult
from snake_scene import Position


class SimulationScenario(str, Enum):
    VALID = "valid"
    UNREACHABLE = "unreachable"
    INVALID = "invalid"


class SimulationBackendAdapter(BackendAdapter):
    def __init__(self, scenario: SimulationScenario = SimulationScenario.VALID) -> None:
        self.scenario = scenario

    def solve(self, rows: int, cols: int, spider: Position, snacks: set[Position]) -> SolveResult:
        ordered_snacks = sorted(snacks)
        explored = self._build_explored(rows, cols, spider)
        path = self._build_path(spider, ordered_snacks)

        if self.scenario == SimulationScenario.UNREACHABLE:
            return SolveResult(explored_positions=explored, path=[], validation_result="No path found")
        if self.scenario == SimulationScenario.INVALID:
            broken_path = path[:-1] if len(path) > 1 else path
            return SolveResult(
                explored_positions=explored,
                path=broken_path,
                validation_result="Last position is not goal",
            )
        return SolveResult(explored_positions=explored, path=path, validation_result="Valid")

    def _build_explored(self, rows: int, cols: int, spider: Position) -> list[Position]:
        sr, sc = spider
        explored: list[Position] = []
        for radius in range(1, 4):
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    rr, cc = sr + dr, sc + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        pos = (rr, cc)
                        if pos not in explored:
                            explored.append(pos)
        return explored

    def _build_path(self, spider: Position, snacks: list[Position]) -> list[Position]:
        if not snacks:
            return []
        current = spider
        path: list[Position] = []
        for target in snacks:
            segment = self._manhattan_segment(current, target)
            path.extend(segment)
            current = target
        return path

    def _manhattan_segment(self, start: Position, end: Position) -> list[Position]:
        cr, cc = start
        er, ec = end
        segment: list[Position] = []
        while cr != er:
            cr += 1 if er > cr else -1
            segment.append((cr, cc))
        while cc != ec:
            cc += 1 if ec > cc else -1
            segment.append((cr, cc))
        return segment
