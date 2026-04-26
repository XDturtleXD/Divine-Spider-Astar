# Divine Spider — A\* Backend

![Tests Status](https://github.com/XDturtleXD/Divine-Spider-Astar/actions/workflows/tests.yml/badge.svg)

DSA Project Group 6. We implemented an A\* search algorithm to solve multi-objective maze problems, where the goal is to find the shortest path that visits all objectives in a maze. The heuristic used is based on the weight of a Minimum Spanning Tree (MST) over the current position and remaining objectives, which provides an admissible lower bound for the search.

## File Overview

| File | Role |
| --- | --- |
| `BE/maze.py` | the `Maze` class that parses a `.txt` maze file and exposes grid info and neighbor queries |
| `BE/backend.py` | the search algorithm `get_Astar_result(maze)`, which is a **generator** that streams explored positions and returns the final path |
| `BE/tests/` | pytest suite for the backend |
| `main.py` | demo script at project root — exercises the backend end-to-end |

## Backend Overview

This module solves multi-objective maze problems using A\* search with an MST-based heuristic. It provides a `Maze` class for parsing maze files and a generator function `get_Astar_result(maze)` that yields explored positions and returns the optimal path. The backend is designed to be used with a frontend that can visualize the search process and the resulting path.

Given a maze with one start position (`H`) and one or more objectives (`*`), the solver finds the **shortest path that visits all objectives**, in any order.

The core algorithm is A\* where the heuristic is the weight of a **Minimum Spanning Tree** (MST, built with Prim's algorithm) over the current position and all remaining objectives, giving a tight admissible lower bound and keeping the search efficient.

### Maze File Format

Plain text, using these characters:

| Char | Meaning |
| --- | --- |
| `#` | Wall |
| `H` | Start position (exactly one) |
| `*` | Objective / food dot (one or more) |
| `.` or space | Open corridor |

Example:

```plaintext
#####
#H.*#
#####
```

## Interface for Frontend

### `Maze(filename: str)`

```python
from maze import Maze
maze = Maze("path/to/maze.txt")
```

Useful methods:

```python
maze.getDimensions()   # -> (rows, cols): grid size
maze.getStart()        # -> (row, col): start position
maze.getObjectives()   # -> list[(row, col)]: all objective positions
maze.isValidPath(path) # -> "Valid" or an error string
```

### `get_Astar_result(maze)` Generator

```python
from backend import get_Astar_result
gen = get_Astar_result(maze)
```

`get_Astar_result` is a **Python generator**. It has two kinds of output:

1. **`yield`** — emits each `(row, col)` position as A\* explores it (use this to animate the search)
2. **`return`** — the final shortest path as `list[(row, col)]`, retrieved via `StopIteration.value`

#### Minimal usage (path only)

```python
from maze import Maze
from backend import get_Astar_result

maze = Maze("maze.txt")
gen = get_Astar_result(maze)

path = []
try:
    while True:
        next(gen)          # drive the generator with ignoring explored positions
except StopIteration as e:
    path = e.value         # list[(row, col)]: the complete optimal path
```

#### Full usage (explored positions + path)

```python
explored = []
path = []
try:
    while True:
        pos = next(gen)    # (row, col) of each node A* expands
        explored.append(pos)
except StopIteration as e:
    path = e.value
```

#### Return values

| Variable | Type | Description |
| --- | --- | --- |
| `pos` | `tuple[int, int]` | A grid cell explored during search — for visualizing the search frontier |
| `path` | `list[tuple[int, int]]` | Ordered positions from start to the last objective; guaranteed optimal |

All coordinates are `(row, col)`, zero-indexed from the top-left corner.

## Running the Example

Requires Python 3.13+.

```bash
uv run python main.py   # run from the project root
```

Expected output (one block per test case):

```plaintext
=== Single objective ===
  Explored : 21 states
  Path len : 9 steps
  Path     : [(1, 1), (1, 2), ...]
  Valid?   : Valid
```

## Validating a Path

```python
result = maze.isValidPath(path)
# "Valid"                    — correct
# "Not all goals passed"     — missed an objective
# "Unnecessary path detected"— path backtracks without reason
# "Last position is not goal"— path does not end on an objective
```

> **Note:** The returned path **excludes the start position** (`H`) and **includes all objective positions** (`*`). `path[0]` is the first step taken, `path[-1]` is the last objective reached.

## QA Testing Guide

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Environment Setup

```bash
git clone <repo-url>
cd Divine-Spider-Astar
uv sync        # installs all runtime and dev dependencies from uv.lock
```

### 2. Automated Test Suite

```bash
uv run pytest
```

Expected: **22 passed**. The suite covers:

| Test class | What it verifies |
| --- | --- |
| `TestPathfinding` | A\* returns an optimal path (matches BFS length) and ends at a goal — tested on small, medium, and large single-goal mazes |
| `TestMultiGoal` | A\* visits **every** objective in a two-goal maze and ends at a goal |
| `TestUnreachable` | A\* returns `[]` when the goal is walled off with no path |
| `TestMaze` | `Maze` correctly parses start, objectives, dimensions, and neighbor counts; loading from a file and from a string give identical results |
| `TestIsValidPath` | `isValidPath` correctly rejects: empty path, path through a wall, path that skips a goal, path that doesn't end at a goal, non-consecutive steps |

### 3. Manual Smoke Test

```bash
uv run python main.py
```

Each test case should print a block like:

```plaintext
=== <label> ===
  Explored : <N> states
  Path len : <N> steps
  Path     : [(row, col), ...]
  Valid?   : Valid
```

**Pass criterion:** every `Valid?` line must print `Valid`.

### 4. Custom Maze Testing

Create a `.txt` maze file, then run:

```python
from maze import Maze
from backend import get_Astar_result

maze = Maze("your_maze.txt")
gen = get_Astar_result(maze)
explored, path = [], []
try:
    while True:
        explored.append(next(gen))
except StopIteration as e:
    path = e.value

print("Explored:", len(explored), "states")
print("Path:", path)
print("Valid?", maze.isValidPath(path))
```

**What to verify:**

- `Valid?` prints `Valid`
- `path` is non-empty (only `[]` when the goal is genuinely unreachable)
- Every `*` position appears in `path`
- `path[-1]` is the position of the last objective

### 5. Edge Case Checklist

| Scenario | How to set it up | Expected result |
| --- | --- | --- |
| Single objective, open maze | One `*`, no dead ends | Optimal path, `Valid` |
| Multiple objectives | Two or more `*` | All `*` in path, `Valid` |
| Goal blocked by walls | `#` surrounds `*` | `path == []` |
| Start adjacent to goal | `H` and `*` are neighbors | `path` of length 1, `Valid` |
| Large maze | Use `BE/tests/bigMaze.txt` | Completes without error, `Valid` |
