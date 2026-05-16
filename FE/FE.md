# Frontend (pygame viewer)

Interactive pygame viewer for multi-objective A* search visualization.

## Run

From repository root (recommended):

```bash
uv run python main.py viewer
```

Direct module:

```bash
uv run python FE/viewer.py
```

Viewer flags: `uv run python main.py viewer --help` (`--width`, `--height`, `--fps`, `--step-ms`, `--assets-dir`).

## Rules and UX

- Board: **8×8** playable cells inside a one-tile border ring (`bolderTile.png`).
- Exactly **one** spider; **1–3** snacks (`MAX_SNACKS = 3`).
- Right-click removes spider or snack in placement mode.
- Placing spider again moves it; spider and snack cannot share a cell.
- **Pause / resume**: `pause.png` while running, `Resume.png` when paused; disabled in placement.
- Origin **(0, 0)** is the bottom-left playable cell.

## Visual phases

1. **Placement** — place spider/snacks; toolbar selects active tool (teal tint on active icon).
2. **Exploration** — subset-colored vertical stripes on explored cells (see `theme.py`); white outline on the cell just expanded; color legend (left) and frontier top-5 (right).
3. **Path** — red polyline from spider through solution (see `PATH_LINE_RGB` in `theme.py`); explored stripes remain; snacks on the path are hidden; spider at path end.
4. **Reset** — clears board and returns to placement.

## Visual theme

Exploration colors live in [`theme.py`](theme.py): `EXPLORATION_SUBSET_PALETTE` (8 earthy ground-tone RGB entries for up to 2³ remaining-subset states — sand, mustard, clay, olive, sage, moss, terracotta, slate). Tuned for **dark gray** background, **light gray** tiles, and **red** spider (no reds in the subset palette). Legend and “Up next” panel use the same first-seen mapping as the board (`drawer.py`).

## Modules

| File | Role |
|------|------|
| `viewer.py` | Entry: main loop, events, animation stepping |
| `state.py` | `AppPhase`, `PlaybackState`, `FrontendState`, placement rules |
| `config.py` | `BOARD_ROWS/COLS`, `MAX_SNACKS`, `build_maze_text` |
| `theme.py` | Exploration palette, stripe alpha, background/path colors |
| `layout.py` | `Grid`, `LayoutManager`, panel and toolbar geometry |
| `drawer.py` | `SceneDrawer` — all drawing |
| `assets.py` | PNG load, trim, scale, button tints |
| `adapter.py` | `BackendAdapter` → BE `Maze` + `get_Astar_result` |

## Backend contract

Each `next(generator)` yields a dict: `pos`, `remaining`, `color`, `cost` (`g`/`h`), `pq_top`. The viewer uses `pos`, `remaining`, and `pq_top` for animation and panels (display colors come from `theme.py`, not BE `color`).

Final path: `StopIteration.value` as `list[(row, col)]`. See [`BE/README.md`](../BE/README.md) for the full API.

## Assets

Used: `bolderTile.png`, `groundTile.png`, `Snack.png`, `Spider.png`, `start_button.png`, `restart_button.png`, `place_snack_button.png`, `pause.png`, `Resume.png`.

Unused on disk: `next_step_button.png`, `layer.png`.
