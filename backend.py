import heapq
from collections.abc import Generator

from maze import Maze

type Pos = tuple[int, int]
type State = tuple[Pos, frozenset[Pos]]


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def mst_heuristic(pos: Pos, remaining: frozenset[Pos]) -> int:
    """Lower-bound cost to connect pos to all remaining objectives via Prim's MST.

    Admissible: MST weight <= any walk that visits all nodes, so A* still
    finds the optimal path.
    """
    if not remaining:
        return 0

    nodes: list[Pos] = [pos] + list(remaining)
    n: int = len(nodes)
    in_tree: set[int] = {0}

    min_edge: list[int] = [manhattan(pos, nodes[i]) for i in range(n)]
    min_edge[0] = 0
    total: int = 0

    for _ in range(n - 1):
        min_val, min_idx = min(
            (min_edge[i], i) for i in range(n) if i not in in_tree
        )
        in_tree.add(min_idx)
        total += min_val
        for i in range(n):
            if i not in in_tree:
                min_edge[i] = min(min_edge[i], manhattan(nodes[min_idx], nodes[i]))

    return total


def astar(maze: Maze) -> Generator[Pos, None, list[Pos]]:
    """Multi-objective A* search over the maze.

    State is (position, frozenset of remaining objectives) so revisiting a
    cell with a different remaining set is treated as a distinct state —
    necessary for correctness when objectives can be collected in any order.

    Yields each explored position for visualization. Returns the complete
    path (start → ... → last objective) via StopIteration.value.
    """
    start: Pos = maze.getStart()
    initial_remaining: frozenset[Pos] = frozenset(maze.getObjectives())
    initial_state: State = (start, initial_remaining)

    priority_queue: list[tuple[int, State]] = []
    heapq.heappush(priority_queue, (0, initial_state))

    parents: dict[State, State | None] = {initial_state: None}
    g_cost: dict[State, int] = {initial_state: 0}

    while priority_queue:
        _, state = heapq.heappop(priority_queue)
        pos, remaining = state
        yield pos

        if not remaining:
            path: list[Pos] = []
            s: State | None = state
            while s is not None:
                path.append(s[0])
                s = parents[s]
            path.reverse()
            return path

        for n in maze.getNeighbors(pos[0], pos[1]):
            # Stepping onto an objective removes it from the remaining set
            new_remaining: frozenset[Pos] = remaining - {n}
            new_state: State = (n, new_remaining)
            new_cost: int = g_cost[state] + 1
            if new_state not in g_cost or new_cost < g_cost[new_state]:
                g_cost[new_state] = new_cost
                priority: int = new_cost + mst_heuristic(n, new_remaining)
                heapq.heappush(priority_queue, (priority, new_state))
                parents[new_state] = state
