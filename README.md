# Divine Spider — A\* Maze Solver

![Tests Status](https://github.com/XDturtleXD/Divine-Spider-Astar/actions/workflows/tests.yml/badge.svg)

DSA Project Group 6. A multi-objective maze solver using A\* search with an MST-based heuristic, with a pygame frontend for visualization.

## Project Structure

```
Divine-Spider-Astar/
├── BE/                  # Backend: maze parsing and A* algorithm
│   ├── maze.py
│   ├── backend.py
│   └── tests/
│       ├── test_sample.py
│       └── bigMaze.txt
├── FE/                  # Frontend: pygame visualization (in development)
├── main.py              # Demo script — runs the backend end-to-end
├── pyproject.toml
└── uv.lock
```

See [`BE/README.md`](BE/README.md) for the full backend API reference and QA guide.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Run the Demo

```bash
uv run python main.py
```

## Run Tests

```bash
uv run pytest
```
