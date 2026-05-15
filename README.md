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
├── main.py              # Project entry point (terminal demo + pygame viewer)
├── pyproject.toml
└── uv.lock
```

See [`BE/README.md`](BE/README.md) for the full backend API reference and QA guide.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Run

All commands go through `main.py`:

| Mode | Command | Description |
|------|---------|-------------|
| **demo** (default) | `uv run python main.py` | Run sample mazes in the terminal (explored count, path, validity) |
| | `uv run python main.py demo` | Same as above |
| **viewer** | `uv run python main.py viewer` | Interactive pygame UI (place spider/snacks, run A\*, animate search) |
| **gui** | `uv run python main.py gui` | Alias for `viewer` |

Terminal backend demos:

```bash
uv run python main.py
# same as:
uv run python main.py demo
```

Interactive pygame viewer:

```bash
uv run python main.py viewer
# or:
uv run python main.py gui

# optional viewer flags, e.g.:
uv run python main.py viewer --width 1200 --step-ms 120
```

Help:

```bash
uv run python main.py --help          # list modes
uv run python main.py viewer --help   # viewer flags (--width, --fps, etc.)
```

You can still run the viewer module directly: `uv run python FE/spider_viewer.py`

## Run Tests

```bash
uv run pytest
```
