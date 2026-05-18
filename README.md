# Divine Spider — A\* Maze Solver

[Code](https://github.com/XDturtleXD/Divine-Spider-Astar)

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

You can still run the viewer module directly: `uv run python FE/viewer.py`

See [`FE/FE.md`](FE/FE.md) for viewer UX, modules, and assets.

## User Guide

Interactive pygame viewer. Board is **8×8** playable cells inside a 1-tile border ring. Origin `(0, 0)` is bottom-left.

### Phases

1. **Placement** — set up the board.
2. **Exploration** — A\* expands cells; colored stripes mark explored states, white outline shows the cell just expanded.
3. **Path** — red polyline from spider through all snacks.
4. **Reset** — clear board, return to placement.

### Controls

| Action | How |
|--------|-----|
| Place / move spider | Toolbar → spider tool → left-click cell |
| Place snack | Toolbar → snack tool → left-click cell (max **3**) |
| Remove spider / snack | Right-click the cell (placement phase only) |
| Start A\* search | `start_button` — needs 1 spider + 1–3 snacks |
| Pause / resume animation | `pause` / `Resume` button (running phase only) |
| Reset board | `restart_button` |

### Rules

- Exactly **1** spider, **1–3** snacks.
- Spider and snack cannot share a cell.
- Placing the spider again moves it.
- Pause/resume disabled during placement.

### Reading the visualization

- Explored cells get a vertical color stripe per remaining-objective subset (palette in `FE/theme.py`).
- Same remaining subset → same color across the run.
- Left panel: color legend. Right panel: top-5 priority-queue entries (`Up next`).
- During **Path** phase: snacks on the path hidden, spider rests at the last objective.

### Animation tuning

```bash
uv run python main.py viewer --width 1200 --height 900 --fps 60 --step-ms 80
```

`--step-ms` = ms per A\* step (lower = faster). Full flags: `uv run python main.py viewer --help`.

## Run Tests

```bash
uv run pytest
```
