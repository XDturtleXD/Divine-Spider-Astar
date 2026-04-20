import heapq
import numpy as np


def heuristic_1(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(maze):
    start = maze.getStart()
    goal = maze.getObjectives()
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))
    parents = np.empty((1000, 1000), dtype=object)
    parents[start[0]][start[1]] = (-1,-1)
    
    g_cost = np.zeros((1000, 1000), dtype=int)
    g_cost[start[0]][start[1]] = 0
    
    while priority_queue:
        _, node = heapq.heappop(priority_queue)
        if node == goal[0]:
            path = []
            while node!=start:
                path.append(node)
                node = parents[node[0]][node[1]]
            path.reverse()
            return path
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            new_cost = g_cost[node[0]][node[1]] + 1
            if parents[n[0]][n[1]] is None or new_cost < g_cost[n[0]][n[1]]:
                g_cost[n[0]][n[1]] = new_cost
                priority = new_cost + heuristic_1(n, goal[0])
                heapq.heappush(priority_queue, (priority, n))
                parents[n[0]][n[1]] = node
    
    return []
