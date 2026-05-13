"""Simulated layer data for visualization development.

Generates per-layer `LayerView` data without invoking the backend. Used when
BE returns no usable path, or when the viewer is launched with
`--simulate-layers`. Snacks are ordered greedy nearest-neighbor from the
spider, and each layer's path segment is an L-shaped Manhattan walk (row
first, then column) from the layer's entry to the next snack.
"""

from __future__ import annotations

from frontend_state import LayerView
from spider_scene import Position


def _manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _order_snacks_nearest_first(spider: Position, snacks: list[Position]) -> list[Position]:
    """Greedy nearest-neighbor ordering with deterministic (row, col) tiebreak."""
    remaining = list(snacks)
    ordered: list[Position] = []
    current = spider
    while remaining:
        remaining.sort(key=lambda p: (_manhattan(current, p), p))
        next_snack = remaining.pop(0)
        ordered.append(next_snack)
        current = next_snack
    return ordered


def _l_shaped_segment(start: Position, end: Position) -> list[Position]:
    """L-shaped Manhattan walk: excludes `start`, includes `end`. Rows first."""
    r0, c0 = start
    r1, c1 = end
    segment: list[Position] = []
    r, c = r0, c0
    if r1 != r0:
        row_step = 1 if r1 > r0 else -1
        while r != r1:
            r += row_step
            segment.append((r, c))
    if c1 != c0:
        col_step = 1 if c1 > c0 else -1
        while c != c1:
            c += col_step
            segment.append((r, c))
    return segment


def simulate_layers(
    spider: Position,
    snacks: list[Position],
    rows: int = 10,
    cols: int = 10,
) -> list[LayerView]:
    """Produce canned `LayerView` data for visualization.

    Returns `len(snacks) + 1` layers; the final layer is terminal (empty
    segment, no remaining snacks). `rows`/`cols` are reserved for future
    bounds-aware path shaping; current L-shape stays inside the board for
    any in-board endpoints.
    """
    del rows, cols  # reserved for future bounds-aware shaping

    if not snacks:
        return [
            LayerView(
                index=0,
                entry=spider,
                snacks_remaining=(),
                segment=(),
            )
        ]

    ordered = _order_snacks_nearest_first(spider, list(snacks))
    layers: list[LayerView] = []
    remaining_in_order: list[Position] = list(ordered)
    entry: Position = spider

    for idx, target in enumerate(ordered):
        segment = _l_shaped_segment(entry, target)
        layers.append(
            LayerView(
                index=idx,
                entry=entry,
                snacks_remaining=tuple(sorted(remaining_in_order)),
                segment=tuple(segment),
            )
        )
        remaining_in_order.remove(target)
        entry = target

    layers.append(
        LayerView(
            index=len(layers),
            entry=entry,
            snacks_remaining=(),
            segment=(),
        )
    )
    return layers
