"""Project entry point: terminal backend demos and pygame viewer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent
BE_DIR = ROOT / "BE"
FE_DIR = ROOT / "FE"

sys.path.insert(0, str(BE_DIR))

from maze import Maze
from backend import get_Astar_result


def make_maze(text: str) -> Maze:
    """Create and return a Maze object from the provided maze text."""
    return Maze(text)


def run(label: str, maze_text: str) -> None:
    print(f"\n=== {label} ===")
    maze = make_maze(maze_text)

    for row in maze.mazeRaw:
        print("  " + "".join(row))

    gen = get_Astar_result(maze)
    explored: list = []
    path: list = []
    try:
        while True:
            step = next(gen)
            explored.append(step["pos"])
    except StopIteration as e:
        path = e.value

    print(f"  Explored : {len(explored)} states")
    print(f"  Path len : {len(path)} steps")
    print(f"  Path     : {path}")
    print(f"  Valid?   : {maze.isValidPath(path)}")


def run_demo() -> None:
    """Run built-in sample mazes and print results to the terminal."""
    run("Single objective", SINGLE)
    run("Multi objective (2 goals)", MULTI)
    run("Multi objective (3 goals)", MULTI_2)
    run("Multi objective (4 goals)", MULTI_3)


def run_viewer(forward_argv: list[str]) -> None:
    """Launch the pygame viewer (FE/viewer.py)."""
    sys.path.insert(0, str(FE_DIR))
    from viewer import main as viewer_main

    viewer_main(forward_argv)


def _print_usage() -> None:
    print(
        "usage: main.py [demo|viewer|gui] [viewer options...]\n\n"
        "  demo (default)  Run sample mazes in the terminal\n"
        "  viewer, gui     Launch interactive pygame viewer\n\n"
        "Viewer flags: run  main.py viewer --help"
    )


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    command = "demo"
    forward_argv: list[str] = []

    if argv:
        if argv[0] in ("demo", "viewer", "gui"):
            command = argv[0]
            forward_argv = argv[1:]
        elif argv[0] in ("-h", "--help"):
            _print_usage()
            return
        else:
            print(f"main.py: unknown command {argv[0]!r}", file=sys.stderr)
            _print_usage()
            sys.exit(2)

    if command in ("viewer", "gui"):
        run_viewer(forward_argv)
    else:
        if any(flag in forward_argv for flag in ("-h", "--help")):
            _print_usage()
            return
        run_demo()


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
    main()
