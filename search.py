# search.py
# ---------------
# Licensing Information:  You are free to use or extend this projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to the University of Illinois at Urbana-Champaign
#
# Created by Michael Abir (abir2@illinois.edu) on 08/28/2018
# Modified by Shang-Tse Chen (stchen@csie.ntu.edu.tw) on 03/03/2022

"""
This is the main entry point for HW1. You should only modify code
within this file -- the unrevised staff files will be used for all other
files and classes when code is run, so be careful to not modify anything else.
"""
# Search should return the path.
# The path should be a list of tuples in the form (row, col) that correspond
# to the positions of the path taken by your search algorithm.
# maze is a Maze object based on the maze from the file specified by input filename
# searchMethod is the search method specified by --method flag (bfs,dfs,astar,astar_multi,fast)
import numpy as np
import heapq
from itertools import combinations

def search(maze, searchMethod):
    return {
        "bfs": bfs,
        "astar": astar,
        "astar_corner": astar_corner,
        "astar_multi": astar_multi,
        "fast": fast,
    }.get(searchMethod)(maze)

def bfs(maze):
    queue = []
    queue.append(maze.getStart())
    start = maze.getStart()
    goal = maze.getObjectives()
    parents = np.empty((1000,1000), dtype=object)
    parents[start[0]][start[1]] = (-1,-1)
    while queue:
        node = queue.pop(0)
        #print(f"Exploring {node}")
        if node == goal[0]:
            path = []
            while node!=start:
                path.append(node)
                node = parents[node[0]][node[1]]
            path.reverse()
            return path
        neightbors = maze.getNeighbors(node[0], node[1])
        for n in neightbors:
            if parents[n[0]][n[1]]:
                continue
            parents[n[0]][n[1]] = node
            queue.append(n)

    return []


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
def heuristic_2(a, goals):
    return min(abs(a[0] - g[0]) + abs(a[1] - g[1]) for g in goals)
def astar_corner(maze):
    start = maze.getStart()
    goals = maze.getObjectives()
    goal_count = len(goals)
    goal_index = {goals[i]: i for i in range(goal_count)} 
    
    priority_queue = []
    heapq.heappush(priority_queue, (0, start, 0))
    
    parents = {}
    parents[(start, 0)] = None
    
    g_cost = {} 
    g_cost[(start, 0)] = 0
    
    final_state = (1 << goal_count) - 1

    while priority_queue:
        _, node, visited = heapq.heappop(priority_queue)
        if node in goals:
            c = g_cost[(node, visited)]
            new_visited = visited
            new_visited |= (1 << goal_index[node])
            parents[(node, new_visited)] = parents[(node, visited)]
            g_cost[(node, new_visited)] = c
            visited = new_visited
        if visited == final_state:
            path = []
            while (node, visited) in parents and parents[(node, visited)] is not None:
                path.append(node)
                node, visited = parents[(node, visited)]
            path.append(start)
            path.reverse()
            return path
        
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            new_cost = g_cost[(node, visited)] + 1
            if (n, visited) not in g_cost or new_cost < g_cost[(n, visited)]:
                g_cost[(n, visited)] = new_cost
                priority = new_cost + heuristic_2(n, [goals[i] for i in range(goal_count) if not (visited & (1 << i))])
                heapq.heappush(priority_queue, (priority, n, visited))
                parents[(n, visited)] = (node, visited)
    
    return []
def dummy(maze):
    """
    Runs A star for part 2 of the assignment in the case where there are four corner objectives.

    @param maze: The maze to execute the search on.

    @return path: a list of tuples containing the coordinates of each state in the computed path
        """
    start = maze.getStart()
    goals = maze.getObjectives()
    priority_queue = []
    heapq.heappush(priority_queue, (0, start, 0))
    parents = np.empty((1000, 1000, 10), dtype=object)
    parents[start[0]][start[1]][0] = (-1,-1)
    
    g_cost = np.zeros((1000, 1000, 10), dtype=int)
    g_cost[start[0]][start[1]] = 0

    goals_cnt = len(goals)
    while priority_queue:
        _, node, cnt = heapq.heappop(priority_queue)
        if node in goals:
            cnt += 1
            parents[node[0]][node[1]][cnt] = (-1,-1)
        if cnt == goals_cnt:
            path = []
            cnt -= 1
            while cnt > 0:
                if parents[node[0]][node[1]][cnt] == (-1,-1):
                    cnt -= 1
                print (node, cnt)
                path.append(node)
                node = parents[node[0]][node[1]][cnt]
            path.reverse()
            return path
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            new_cost = g_cost[node[0]][node[1]][cnt] + 1
            if parents[n[0]][n[1]][cnt] is None or new_cost < g_cost[n[0]][n[1]][cnt]:
                g_cost[n[0]][n[1]][cnt] = new_cost
                priority = new_cost + heuristic_2(n, goals)
                heapq.heappush(priority_queue, (priority, n, cnt))
                parents[n[0]][n[1]][cnt] = node
    
    return []


def heuristic_3(node, goals):
    if not goals:
        return 0
    # 先計算離當前點最近的目標點
    min_dist = min(abs(node[0] - g[0]) + abs(node[1] - g[1]) for g in goals)
    # 計算最小生成樹 (MST) 近似值
    mst_cost = 0
    goal_list = list(goals)
    for g1, g2 in combinations(goal_list, 2):
        mst_cost += abs(g1[0] - g2[0]) + abs(g1[1] - g2[1])
    mst_cost /= len(goals)  # 近似為每個點的最小連接成本
    
    return min_dist + mst_cost

def astar_multi(maze):
    start = maze.getStart()
    goals = maze.getObjectives()
    goal_count = len(goals)
    goal_index = {goals[i]: i for i in range(goal_count)} 
    
    priority_queue = []
    heapq.heappush(priority_queue, (0, start, 0))
    
    parents = {}
    parents[(start, 0)] = None
    
    g_cost = {} 
    g_cost[(start, 0)] = 0
    
    final_state = (1 << goal_count) - 1

    while priority_queue:
        _, node, visited = heapq.heappop(priority_queue)
        if node in goals:
            c = g_cost[(node, visited)]
            new_visited = visited
            new_visited |= (1 << goal_index[node])
            parents[(node, new_visited)] = parents[(node, visited)]
            g_cost[(node, new_visited)] = c
            visited = new_visited
        if visited == final_state:
            path = []
            while (node, visited) in parents and parents[(node, visited)] is not None:
                path.append(node)
                node, visited = parents[(node, visited)]
            path.append(start)
            path.reverse()
            return path
        
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            new_cost = g_cost[(node, visited)] + 1
            if (n, visited) not in g_cost or new_cost < g_cost[(n, visited)]:
                g_cost[(n, visited)] = new_cost
                priority = new_cost + heuristic_3(n, [goals[i] for i in range(goal_count) if not (visited & (1 << i))])
                heapq.heappush(priority_queue, (priority, n, visited))
                parents[(n, visited)] = (node, visited)
    
    return []


def fast(maze):
    """
    Runs suboptimal search algorithm for part 4.

    @param maze: The maze to execute the search on.

    @return path: a list of tuples containing the coordinates of each state in the computed path
    """
    # TODO: Write your code here
    start = maze.getStart()
    goals = maze.getObjectives()
    priority_queue = []
    for g in goals:
        heapq.heappush(priority_queue, goal)
    while priority_queue:
        goal = heuristic_3
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
