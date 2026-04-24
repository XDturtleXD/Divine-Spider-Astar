import heapq
from collections.abc import Generator

from maze import Maze

type Pos = tuple[int, int] # (row, col)
type State = tuple[Pos, frozenset[Pos]] # (current position, remaining objectives)


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


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


def astar(maze: Maze) -> Generator[Pos, None, list[Pos]]:
    """
    Multi-objective A* search over the maze.

    State is (position, frozenset of remaining objectives)
    so revisiting a cell with a different remaining set is treated as a distinct state —
    necessary for correctness when objectives can be collected in any order.

    Yields each explored position for visualization. Returns the complete
    path (start → ... → last objective) via StopIteration.value.
    """
    # Initialize the priority queue with the starting position and all objectives remaining
    start = maze.getStart()
    if start is None:
        raise ValueError("Maze is missing a start position.")

    objectives = maze.getObjectives()
    if objectives is None:
        raise ValueError("Maze is missing objectives.")

    initial_remaining: frozenset[Pos] = frozenset(objectives)
    initial_state: State = (start, initial_remaining)
    priority_queue: list[tuple[int, State]] = []
    heapq.heappush(priority_queue, (0, initial_state))

    parents: dict[State, State | None] = {initial_state: None} # to reconstruct the path once we reach the goal
    g_cost: dict[State, int] = {initial_state: 0} # cost from start to this state
    visited: set[State] = set() # states already expanded; skip stale heap entries

    # Main A* loop
    # We loop until there are no more states to explore (i.e. the priority queue is empty)
    while priority_queue:
        # Pop the state with the lowest f_cost (g_cost + heuristic) from the priority queue
        _, state = heapq.heappop(priority_queue)

        # Skip stale heap entries: if we already expanded this state via a cheaper path, ignore it
        if state in visited:
            continue
        visited.add(state)

        pos, remaining = state
        yield pos

        # If there are no remaining objectives, we have found a path to collect them all
        if not remaining:
            path: list[Pos] = []
            s: State | None = state
            while s is not None: # reconstruct the path by following the parent pointers back to the start
                path.append(s[0])
                s = parents[s]
            path.reverse() # reverse the path to get it from start to goal
            return path

        # For each valid neighboring position,
        for n in maze.getNeighbors(pos[0], pos[1]):
            new_remaining: frozenset[Pos] = remaining - {n} # if n is an objective, remove it from the remaining set
            new_state: State = (n, new_remaining) # the new state is the neighbor position and the updated remaining objectives
            new_cost: int = g_cost[state] + 1 # the cost to move to a neighbor is always 1

            # A* logic: if we haven't seen this state before, or we found a cheaper path to it,
            # update the costs and add it to the priority queue
            if new_state not in g_cost or new_cost < g_cost[new_state]:
                g_cost[new_state] = new_cost
                priority: int = new_cost + mst_heuristic(n, new_remaining) # f_cost = g_cost + heuristic
                heapq.heappush(priority_queue, (priority, new_state)) # push the new state with its f_cost into the priority queue
                parents[new_state] = state # update the parent pointer for path reconstruction

    # No solution exists that collects all objectives.
    return []
