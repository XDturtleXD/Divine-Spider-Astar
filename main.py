import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "BE"))

from maze import Maze
from backend import get_Astar_result


def make_maze(text: str) -> Maze:
    """Create and return a Maze object from the provided maze text."""
    return Maze(text)


def run(label: str, maze_text: str) -> None:
    print(f"\n=== {label} ===")
    maze = make_maze(maze_text)

    # Print the raw maze
    for row in maze.mazeRaw:
        print("  " + "".join(row))
    # Run A* and collect explored positions
    gen = get_Astar_result(maze)
    explored: list = []
    path: list = []
    try:
        while True:
            pos = next(gen)
            explored.append(pos)
    except StopIteration as e:
        path = e.value
    print(f"  Explored : {len(explored)} states")
    print(f"  Path len : {len(path)} steps")
    print(f"  Path     : {path}")
    print(f"  Valid?   : {maze.isValidPath(path)}")


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

MULTI_2 = """\
#######
#H...##
#*...##
#....*#
#######
"""

MULTI_3 = """\
#########
#H..*..##
#*.....##
#......*#
#########
"""

if __name__ == "__main__":
    run("Single objective", SINGLE)
    run("Multi objective (2 goals)", MULTI)
    run("Multi objective (3 goals)", MULTI_2)
    run("Multi objective (4 goals)", MULTI_3)
