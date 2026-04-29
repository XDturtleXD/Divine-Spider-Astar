"""Scene parsing and state model for the snake renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SceneState:
    """Immutable scene snapshot parsed from ASCII map text."""

    rows: int
    cols: int
    borders: frozenset[tuple[int, int]]
    grounds: frozenset[tuple[int, int]]
    snake_head: tuple[int, int] | None
    snake_body: tuple[tuple[int, int], ...]
    snacks: frozenset[tuple[int, int]]
    raw_lines: tuple[str, ...]


def _normalize_lines(scene_text: str) -> list[str]:
    # Allow multiline literals with leading/trailing empty lines.
    lines = [line.rstrip("\n") for line in scene_text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        raise ValueError("Scene text is empty.")
    return lines


def _validate_rect(lines: Iterable[str]) -> tuple[int, int]:
    rows = list(lines)
    width = len(rows[0])
    if width == 0:
        raise ValueError("Scene rows cannot be empty.")
    for idx, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"Scene must be rectangular. Row {idx} has width {len(row)}, expected {width}.")
    return len(rows), width


def parse_scene_map(scene_text: str) -> SceneState:
    """Parse ASCII scene map.

    Mapping:
    - # => border tile
    - H => snake head
    - S => snake body
    - * => snack
    - other chars => ground
    """
    lines = _normalize_lines(scene_text)
    rows, cols = _validate_rect(lines)

    borders: set[tuple[int, int]] = set()
    grounds: set[tuple[int, int]] = set()
    snacks: set[tuple[int, int]] = set()
    snake_body: list[tuple[int, int]] = []
    snake_head: tuple[int, int] | None = None

    for row_idx, line in enumerate(lines):
        for col_idx, char in enumerate(line):
            pos = (row_idx, col_idx)
            if char == "#":
                borders.add(pos)
                continue

            grounds.add(pos)
            if char == "H":
                if snake_head is not None:
                    raise ValueError("Scene contains multiple snake heads ('H').")
                snake_head = pos
            elif char == "S":
                snake_body.append(pos)
            elif char == "*":
                snacks.add(pos)

    return SceneState(
        rows=rows,
        cols=cols,
        borders=frozenset(borders),
        grounds=frozenset(grounds),
        snake_head=snake_head,
        snake_body=tuple(snake_body),
        snacks=frozenset(snacks),
        raw_lines=tuple(lines),
    )
