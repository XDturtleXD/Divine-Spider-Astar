from backend import get_Astar_result
from maze import Maze
import pytest
import numpy as np

SINGLE = """\
#########
#H......#
#.......#
#......*#
#########
"""

MULTI = """\
#####
#H.*#
#####
"""

def bfs(maze):
    queue = []
    queue.append(maze.getStart())
    start = maze.getStart()
    goal = maze.getObjectives()
    # Using a dictionary for parents is safer and more flexible than a fixed 1000x1000 array
    parents = {}
    parents[start] = (-1, -1)
    
    while queue:
        node = queue.pop(0)
        if node == goal[0]:
            path = []
            while node != start:
                path.append(node)
                node = parents[node]
            path.reverse()
            return path
        
        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            if n in parents:
                continue
            parents[n] = node
            queue.append(n)
    return []

def make_maze(text: str) -> Maze:
    """Write maze text to a temp file and return a Maze object."""
    return Maze(text)

def get_astar_path(maze):
    """Helper to extract the final path from the A* generator."""
    gen = get_Astar_result(maze)
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value

class TestPathfinding:
    
    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, "./tests/bigMaze.txt"])
    def test_path_length_consistency(self, maze_text):
        """Check that the path length from A* is the same as the path length from BFS (for single goal)."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        bfs_path = bfs(maze)
        
        # A* on a consistent heuristic should find the shortest path, matching BFS
        assert len(astar_path) == len(bfs_path), f"A* length {len(astar_path)} != BFS length {len(bfs_path)}"

    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, "./tests/bigMaze.txt"])
    def test_astar_reaches_goal(self, maze_text):
        """Check that the path is valid and reaches the target goal."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()
        
        # 1. Check if the path is physically valid (no wall jumping)
        assert maze.isValidPath(astar_path) is "Valid", "The path returned by A* is invalid according to maze rules."
        
        # 2. Check if the final position in the path is one of the objectives
        assert len(astar_path) > 0, "A* failed to find a path."
        final_pos = astar_path[-1]
        assert final_pos in goals, f"The path ended at {final_pos}, which is not a goal {goals}."