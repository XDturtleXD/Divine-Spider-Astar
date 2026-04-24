# Divine Snakes — A\* Backend

DSA Project Group 6. This module solves multi-objective maze problems using A\* search with an MST-based heuristic.

## What It Does

Given a maze with one start position (`H`) and one or more objectives (`*`), the solver finds the **shortest path that visits all objectives**, in any order.

The core algorithm is A\* where the heuristic is the weight of a **Minimum Spanning Tree** (MST, built with Prim's algorithm) over the current position and all remaining objectives, giving a tight admissible lower bound and keeping the search efficient.

## File Overview

| File | Role |
|---|---|
| `maze.py` | the `Maze` class that parses a `.txt` maze file and exposes grid info and neighbor queries |
| `backend.py` | the search algorithm `get_Astar_result(maze)`, which is a **generator** that streams explored positions and returns the final path |
| `main.py` | Example usage and test cases |


## Maze File Format

Plain text, using these characters:

| Char | Meaning |
|---|---|
| `#` | Wall |
| `H` | Start position (exactly one) |
| `*` | Objective / food dot (one or more) |
| `.` or space | Open corridor |

Example:

```
#####
#H.*#
#####
```

---

## Interface for Frontend

### `Maze(filename: str)`

```python
from maze import Maze
maze = Maze("path/to/maze.txt")
```

Useful methods:

```python
maze.getDimensions()   # → (rows, cols): grid size
maze.getStart()        # → (row, col): start position
maze.getObjectives()   # → list[(row, col)]: all objective positions
maze.isValidPath(path) # → "Valid" or an error string
```

---

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
|---|---|---|
| `pos` | `tuple[int, int]` | A grid cell explored during search — for visualizing the search frontier |
| `path` | `list[tuple[int, int]]` | Ordered positions from start to the last objective; guaranteed optimal |

All coordinates are `(row, col)`, zero-indexed from the top-left corner.

---

## Running the Example

Requires Python 3.13+.

```bash
python3 main.py
```

Expected output (one block per test case):

```
=== Single objective ===
  Explored : 21 states
  Path len : 9 steps
  Path     : [(1, 1), (1, 2), ...]
  Valid?   : Valid
```

---

## Validating a Path

```python
result = maze.isValidPath(path)
# "Valid"                    — correct
# "Not all goals passed"     — missed an objective
# "Unnecessary path detected"— path backtracks without reason
# "Last position is not goal"— path does not end on an objective
```

---

## Notes

- Coordinates throughout are `(row, col)`, not `(x, y)`.
