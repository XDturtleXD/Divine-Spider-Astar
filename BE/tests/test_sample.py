from pathlib import Path
from backend import get_Astar_result
from maze import Maze
import pytest

BIG_MAZE = str(Path(__file__).parent / "bigMaze.txt")

# ── Maze fixtures ─────────────────────────────────────────────────────────────

SINGLE = """\
#########
#H......#
#.......#
#......*#
#########
"""
# Start: (1,1)  Objective: (3,7)  Dimensions: (5,9)

MULTI = """\
#####
#H.*#
#####
"""
# Start: (1,1)  Objective: (1,3)  Single goal

MULTI_GOAL = """\
#######
#H.*.*#
#######
"""
# Start: (1,1)  Objectives: (1,3) and (1,5)  Two goals

UNREACHABLE = """\
#####
#H#*#
#####
"""
# Start: (1,1)  Objective: (1,3)  Wall at (1,2) — no path exists

# ── Helpers ───────────────────────────────────────────────────────────────────

def bfs(maze):
    """BFS for single-goal mazes only. Returns path excluding start."""
    queue = []
    queue.append(maze.getStart())
    start = maze.getStart()
    goal = maze.getObjectives()
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
    return Maze(text)


def get_astar_path(maze):
    """Drain the A* generator and return the final path (or None if unreachable)."""
    gen = get_Astar_result(maze)
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


# ── Single-goal correctness ───────────────────────────────────────────────────

class TestPathfinding:

    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, BIG_MAZE])
    def test_path_length_consistency(self, maze_text):
        """A* path length must match BFS (optimal) for single-goal mazes."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        bfs_path = bfs(maze)

        assert len(astar_path) == len(bfs_path), \
            f"A* length {len(astar_path)} != BFS length {len(bfs_path)}"

    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, BIG_MAZE])
    def test_astar_reaches_goal(self, maze_text):
        """A* path must be physically valid and end at a goal."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert maze.isValidPath(astar_path) == "Valid", \
            "The path returned by A* is invalid according to maze rules."
        assert len(astar_path) > 0, "A* failed to find a path."
        assert astar_path[-1] in goals, \
            f"Path ended at {astar_path[-1]}, which is not a goal {goals}."


# ── Multi-goal correctness ────────────────────────────────────────────────────

class TestMultiGoal:

    def test_all_objectives_collected(self):
        """A* must visit every objective in a multi-goal maze."""
        maze = make_maze(MULTI_GOAL)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert len(goals) > 1, "Fixture must have more than one goal"
        assert maze.isValidPath(astar_path) == "Valid"
        for goal in goals:
            assert goal in astar_path, f"Objective {goal} was not visited"

    def test_multi_goal_ends_at_a_goal(self):
        """The final position in a multi-goal path must be one of the objectives."""
        maze = make_maze(MULTI_GOAL)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert astar_path[-1] in goals


# ── Unreachable goal ──────────────────────────────────────────────────────────

class TestUnreachable:

    def test_unreachable_goal_returns_empty(self):
        """A* must return an empty list when no path to the goal exists."""
        maze = make_maze(UNREACHABLE)
        assert get_astar_path(maze) == []


# ── Maze parsing ──────────────────────────────────────────────────────────────

class TestMaze:

    def test_start_parsed_correctly(self):
        assert make_maze(SINGLE).getStart() == (1, 1)

    def test_objective_parsed_correctly(self):
        assert make_maze(SINGLE).getObjectives() == [(3, 7)]

    def test_dimensions_parsed_correctly(self):
        assert make_maze(SINGLE).getDimensions() == (5, 9)

    def test_multi_goal_objective_count(self):
        assert len(make_maze(MULTI_GOAL).getObjectives()) == 2

    def test_string_and_file_give_same_result(self):
        """Maze loaded from a file and from its string content must be equivalent."""
        maze_from_file = Maze(BIG_MAZE)
        with open(BIG_MAZE) as f:
            content = f.read()
        maze_from_string = Maze(content)

        assert maze_from_file.getStart() == maze_from_string.getStart()
        assert maze_from_file.getObjectives() == maze_from_string.getObjectives()
        assert maze_from_file.getDimensions() == maze_from_string.getDimensions()

    def test_neighbors_interior_cell(self):
        """An interior open cell should have 4 neighbors."""
        maze = make_maze(SINGLE)
        assert len(maze.getNeighbors(2, 4)) == 4

    def test_neighbors_corner_cell(self):
        """The start cell (1,1) is bounded by walls on two sides — 2 neighbors only."""
        maze = make_maze(SINGLE)
        assert len(maze.getNeighbors(1, 1)) == 2


# ── isValidPath edge cases ────────────────────────────────────────────────────

class TestIsValidPath:

    def test_empty_path_invalid(self):
        assert make_maze(SINGLE).isValidPath([]) != "Valid"

    def test_astar_path_is_valid(self):
        maze = make_maze(SINGLE)
        assert maze.isValidPath(get_astar_path(maze)) == "Valid"

    def test_path_through_wall(self):
        maze = make_maze(SINGLE)
        # (0,1) is a wall; single hop from start (1,1) -> (0,1)
        assert maze.isValidPath([(1, 1), (0, 1)]) != "Valid"

    def test_path_misses_goal(self):
        maze = make_maze(SINGLE)
        # Valid moves but goal (3,7) never reached
        assert maze.isValidPath([(1, 2), (1, 3), (1, 4)]) != "Valid"

    def test_path_visits_goal_but_does_not_end_there(self):
        maze = make_maze(SINGLE)
        # Passes through (3,7) but continues to (2,7)
        path = [(1,2),(2,2),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(2,7)]
        assert maze.isValidPath(path) != "Valid"

    def test_non_consecutive_steps(self):
        maze = make_maze(SINGLE)
        # Teleports from start directly to goal — Manhattan distance 8
        assert maze.isValidPath([(1, 1), (3, 7)]) != "Valid"
