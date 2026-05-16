import heapq
from collections.abc import Generator

from maze import Maze

type Pos = tuple[int, int] # (row, col)
type State = tuple[Pos, frozenset[Pos]] # (current position, remaining objectives)
type PqEntry = tuple[int, int, int, Pos, frozenset[Pos]] # (f_cost, g_cost, h_cost, position, remaining)

# Number of top priority-queue entries to expose per step for visualization.
PQ_SNAPSHOT_K = 5


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def remaining_color_index(remaining: frozenset[Pos], objectives: tuple[Pos, ...]) -> int:
    """
    Map `remaining` to a stable color index in 1..2**len(objectives).

    Each original objective is assigned a bit by its index in the sorted `objectives` tuple.
    A bit is set iff that objective is still in `remaining`. Returns bitmask + 1.

    With MAX_OBJECTIVES = 3 the range is exactly 1..8:
      - all 3 still uncollected → 0b111 + 1 = 8
      - all collected (terminal step) → 0b000 + 1 = 1
    """
    bits = 0
    for i, obj in enumerate(objectives):
        if obj in remaining:
            bits |= 1 << i
    return bits + 1


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


def get_Astar_result(
    maze: Maze,
) -> Generator[dict, None, list[Pos]]:
    """
    Multi-objective A* search over the maze.

    State is (position, frozenset of remaining objectives)
    so revisiting a cell with a different remaining set is treated as a distinct state —
    necessary for correctness when objectives can be collected in any order.

    Per expansion, yields a dict with keys:
      - "pos": the grid cell just expanded (Pos)
      - "remaining": frozenset of objectives not yet collected at this state
      - "color": stable index in 1..2**len(objectives) for the remaining set —
                 use as a layer/color identifier in the frontend (see remaining_color_index)
      - "cost": {"g": g_cost, "h": h_cost} for the expanded node
      - "pq_top": up to PQ_SNAPSHOT_K cheapest live (non-visited) states,
                  each as (f_cost, pos, remaining); the same cell may appear
                  multiple times with different remaining sets (different layers)

    Returns the path (first step after start → last objective) via StopIteration.value.
    The start position itself is excluded from the returned path.
    """
    # Initialize the priority queue with the starting position and all objectives remaining
    start = maze.getStart()
    if start is None:
        raise ValueError("Maze is missing a start position.")

    objectives = maze.getObjectives()
    if objectives is None:
        raise ValueError("Maze is missing objectives.")

    initial_remaining: frozenset[Pos] = frozenset(objectives)
    # Stable, sorted snapshot of the original objective set — used as the bit-index basis for color hashing.
    objectives_snapshot: tuple[Pos, ...] = tuple(sorted(initial_remaining))
    initial_state: State = (start, initial_remaining)
    initial_h: int = mst_heuristic(start, initial_remaining)
    # Heap entry: (f_cost, h_cost, push_counter, state). Tie-break on equal f: prefer smaller h
    # (closer to goal). Counter is a monotonic int to keep tuples comparable when h also ties
    # — frozenset is not orderable.
    push_counter: int = 0
    priority_queue: list[tuple[int, int, int, State]] = []
    heapq.heappush(priority_queue, (initial_h, initial_h, push_counter, initial_state))
    push_counter += 1

    parents: dict[State, State | None] = {initial_state: None} # to reconstruct the path once we reach the goal
    g_cost: dict[State, int] = {initial_state: 0} # cost from start to this state
    # h depends only on (pos, remaining), so it is invariant under cheaper-g updates — safe to cache once per state.
    h_cost: dict[State, int] = {initial_state: initial_h}
    visited: set[State] = set() # states already expanded; skip stale heap entries

    # Main A* loop
    # We loop until there are no more states to explore (i.e. the priority queue is empty)
    while priority_queue:
        # Pop the state with the lowest f_cost (g_cost + heuristic), breaking ties by smaller h.
        f_priority, _h_tiebreak, _seq, state = heapq.heappop(priority_queue)

        # Skip stale heap entries: if we already expanded this state via a cheaper path, ignore it
        if state in visited:
            continue
        visited.add(state)

        pos, remaining = state
        maze._incrementStatesExplored()

        is_terminal = not remaining

        # Expand neighbours before snapshotting so pq_top reflects the immediate future frontier.
        if not is_terminal:
            for n in maze.getNeighbors(pos[0], pos[1]):
                new_remaining: frozenset[Pos] = remaining - {n}
                new_state: State = (n, new_remaining)
                new_cost: int = g_cost[state] + 1

                if new_state not in g_cost or new_cost < g_cost[new_state]:
                    g_cost[new_state] = new_cost
                    if new_state not in h_cost:
                        h_cost[new_state] = mst_heuristic(n, new_remaining)
                    priority: int = new_cost + h_cost[new_state]
                    heapq.heappush(priority_queue, (priority, h_cost[new_state], push_counter, new_state))
                    push_counter += 1
                    parents[new_state] = state

        # Snapshot top-K live (non-visited) states from the heap.
        # nsmallest returns entries sorted by the heap key (f, h, seq) — matches pop order.
        pq_top: list[PqEntry] = []
        for f, _h, _seq, cand_state in heapq.nsmallest(PQ_SNAPSHOT_K * 4, priority_queue):
            if cand_state in visited:
                continue
            cand_g = g_cost[cand_state]
            cand_h = h_cost[cand_state]
            pq_top.append((f, cand_g, cand_h, cand_state[0], cand_state[1]))
            if len(pq_top) >= PQ_SNAPSHOT_K:
                break

        g = g_cost[state]
        h = h_cost[state]
        # Trace from start to the cell just expanded (inclusive of both endpoints).
        trace: list[Pos] = []
        s: State | None = state
        while s is not None:
            trace.append(s[0])
            s = parents[s]
        trace.reverse()
        yield {
            "pos": pos, # the cell just expanded
            "remaining": remaining, # objectives not yet collected at this state
            "color": remaining_color_index(remaining, objectives_snapshot), # stable 1..2**N index for FE coloring
            "cost": {"g": g, "h": h}, # separate g and h for visualization
            "trace": tuple(trace), # path from start to this cell along A* parents; includes both endpoints
            "pq_top": tuple(pq_top), # up to PQ_SNAPSHOT_K cheapest live (non-visited) PQ entries, each as (f_cost, g_cost, h_cost, pos, remaining)
        }

        if is_terminal:
            path: list[Pos] = []
            s: State | None = state
            while s is not None:
                path.append(s[0])
                s = parents[s]
            path.pop()
            path.reverse()
            return path

    # No solution exists that collects all objectives.
    return []
