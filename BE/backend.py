import heapq
import functools
from collections.abc import Generator

from maze import Maze

type Pos = tuple[int, int] # (row, col)
type State = tuple[Pos, frozenset[Pos]] # (current position, remaining objectives)


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@functools.lru_cache(maxsize=None)
def mst_heuristic(pos: Pos, remaining: frozenset[Pos]) -> int:
    """
    Lower-bound cost to connect pos to all remaining objectives via Prim's MST.
    Admissible: MST weight <= any walk that visits all nodes, so A* still finds the optimal path.
    """
    # If no remaining objectives, no cost to connect them
    if not remaining:
        return 0

    nodes: list[Pos] = [pos] + list(remaining) # nodes[0] is the current position, nodes[1:] are the remaining objectives
    n: int = len(nodes)

    in_tree: set[int] = {0}
    min_edge: list[int] = [manhattan(pos, nodes[i]) for i in range(n)]
    min_edge[0] = 0
    total: int = 0

    for _ in range(n - 1): # we need to add n-1 edges to connect all n nodes
        min_val, min_idx = min( # find the node with the smallest edge to the tree
            (min_edge[i], i) for i in range(n) if i not in in_tree
        )
        in_tree.add(min_idx) # add the node to the tree
        total += min_val # add the edge weight to the total

        # Update the edge weights for the remaining nodes
        # since the new node might provide a cheaper connection
        for i in range(n):
            if i not in in_tree:
                min_edge[i] = min(min_edge[i], manhattan(nodes[min_idx], nodes[i]))

    return total


def get_Astar_result(maze: Maze) -> Generator[Pos, None, list[Pos]]:
    """
    Multi-objective A* search over the maze.

    State is (position, frozenset of remaining objectives)
    so revisiting a cell with a different remaining set is treated as a distinct state —
    necessary for correctness when objectives can be collected in any order.

    Yields each explored position for visualization. Returns the path
    (start → ... → last objective) via StopIteration.value.
    """
    # Initialize the priority queue with the starting position and all objectives remaining
    start = maze.getStart()
    if start is None:
        raise ValueError("Maze is missing a start position.")

    objectives = maze.getObjectives()
    if objectives is None:
        raise ValueError("Maze is missing objectives.")

    initial_remaining: frozenset[Pos] = frozenset(objectives)
    objectives_set: frozenset[Pos] = initial_remaining
    initial_state: State = (start, initial_remaining)
    priority_queue: list[tuple[int, int, int, int, State]] = []
    counter: int = 0  # FIFO tiebreaker; prevents frozenset comparison on equal f-cost
    heapq.heappush(priority_queue, (0, 0, 1, counter, initial_state))

    parents: dict[State, State | None] = {initial_state: None} # to reconstruct the path once we reach the goal
    g_cost: dict[State, int] = {initial_state: 0} # cost from start to this state
    visited: set[State] = set() # states already expanded; skip stale heap entries

    # Main A* loop
    # We loop until there are no more states to explore (i.e. the priority queue is empty)
    while priority_queue:
        # Pop the state with the lowest f_cost (g_cost + heuristic) from the priority queue
        _, _, _, _, state = heapq.heappop(priority_queue)

        # Skip stale heap entries: if we already expanded this state via a cheaper path, ignore it
        if state in visited:
            continue
        visited.add(state)

        pos, remaining = state
        maze._incrementStatesExplored()
        g = g_cost[state]
        h = mst_heuristic(pos, remaining)

        # Terminal state: yield empty frontier then reconstruct path
        if not remaining:
            yield pos, remaining, g, h, {}
            path: list[Pos] = []
            s: State | None = state
            while s is not None:
                path.append(s[0])
                s = parents[s]
            path.reverse()
            return path

        # Process neighbors FIRST so the frontier snapshot includes them —
        # this guarantees the next cell to be popped is visible as a candidate
        for n in maze.getNeighbors(pos[0], pos[1]):
            new_remaining: frozenset[Pos] = remaining - {n}
            new_state: State = (n, new_remaining)
            new_cost: int = g_cost[state] + 1

            if new_state not in g_cost or new_cost < g_cost[new_state]:
                g_cost[new_state] = new_cost
                priority: int = new_cost + mst_heuristic(n, new_remaining)
                counter += 1
                is_not_snack = 0 if n in objectives_set else 1
                heapq.heappush(priority_queue, (priority, -new_cost, is_not_snack, counter, new_state))
                parents[new_state] = state

        # Snapshot frontier AFTER neighbors are added; store (g, h) per position
        frontier: dict[Pos, tuple[int, int]] = {}
        for entry_f, neg_entry_g, _, _, entry_state in priority_queue:
            if entry_state not in visited:
                entry_pos = entry_state[0]
                entry_g = -neg_entry_g
                entry_h = entry_f - entry_g
                if entry_pos not in frontier or entry_f < sum(frontier[entry_pos]):
                    frontier[entry_pos] = (entry_g, entry_h)

        yield pos, remaining, g, h, frontier

    # No solution exists that collects all objectives.
    return []
