import heapq


def heuristic_1(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def mst_heuristic(pos, remaining):
    if not remaining:
        return 0
    nodes = [pos] + list(remaining)
    n = len(nodes)
    in_tree = {0}
    min_edge = [manhattan(pos, nodes[i]) for i in range(n)]
    min_edge[0] = 0
    total = 0
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

def astar(maze):
    start = maze.getStart()
    initial_remaining = frozenset(maze.getObjectives())
    initial_state = (start, initial_remaining)
    priority_queue = []
    heapq.heappush(priority_queue, (0, initial_state))
    parents = {initial_state: None}
    g_cost = {initial_state: 0}

    while priority_queue:
        _, state = heapq.heappop(priority_queue)
        pos, remaining = state
        yield pos
        if not remaining:
            path = []
            s = state
            while s is not None:
                path.append(s[0])
                s = parents[s]
            path.reverse()
            return path
        neighbors = maze.getNeighbors(pos[0], pos[1])
        for n in neighbors:
            new_remaining = remaining - {n}
            new_state = (n, new_remaining)
            new_cost = g_cost[state] + 1
            if new_state not in g_cost or new_cost < g_cost[new_state]:
                g_cost[new_state] = new_cost
                priority = new_cost + mst_heuristic(n, new_remaining)
                heapq.heappush(priority_queue, (priority, new_state))
                parents[new_state] = state
