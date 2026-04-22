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
    goal = maze.getObjectives()
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))
    parents = {start: (-1, -1)}
    g_cost = {start: 0}

    while priority_queue:
        _, node = heapq.heappop(priority_queue)
        yield node
        if node == goal[0]:
            path = []
            while node != start:
                path.append(node)
                node = parents[node]
            #path.reverse()
            #return path
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            new_cost = g_cost[node] + 1
            if n not in g_cost or new_cost < g_cost[n]:
                g_cost[n] = new_cost
                priority = new_cost + heuristic_1(n, goal[0])
                heapq.heappush(priority_queue, (priority, n))
                parents[n] = node
