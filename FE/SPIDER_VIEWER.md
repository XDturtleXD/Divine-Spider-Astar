# Spider Viewer (Frontend)

This frontend is a single-thread pygame viewer for Divine Spider A*.

It supports:

- placement mode for spider/snacks
- backend-driven exploration + final path rendering
- simulation backend mode for deterministic UI testing

## Rules and UX

- Board size is fixed to `10x10`.
- The 10x10 playable area is wrapped by a visual border ring using `assets/bolderTile.png`.
- Exactly one spider is required to run.
- Snack count is limited to `5`.
- At least one snack is required to run.
- Right-click removes placed spider/snack.
- Placing spider again moves the existing spider.
- Spider and snack cannot overlap on placement.

## Visual States

1. Placement
   - user places spider/snacks
   - spider/snack mode button toggles: active tool gets a teal tint overlay; the other tool is slightly dimmed (no outlines)
   - all control buttons are icon-only and fixed at the bottom side of window
2. Exploration
   - explored cells are rendered with a dim yellow overlay
   - snacks stay visible
3. Path
   - predicted path is rendered with red tint overlay
   - explored cells stay visible as context
   - snacks consumed by revealed path are hidden
   - spider is rendered at current/last path position
4. Reset
   - clear placements and playback data
   - return to placement mode

## Modules

- `spider_viewer.py`
  - app entrypoint and single main loop
  - event handling for placement/buttons
  - playback animation timing (`--step-ms`)
- `frontend_state.py`
  - app phase and placement tool enums
  - board placement/removal guards
  - toast message and playback indices for exploration/path animation (`PlaybackState` holds lists + indices; does not mirror `validation_result` from the backend)
- `spider_scene.py`
  - `BOARD_ROWS` / `BOARD_COLS` (`10`), `MAX_SNACKS` (`5`), `Position` alias
  - `build_maze_text(...)` for feeding the real backend adapter
- `spider_render.py`
  - `compute_window_layout(surface)` splits the window into an upper rect (play field) and a bottom `button_strip`; calls `Grid.fit_square_cells_in_rect(play_rect)` so the grid + one-tile border fits with **square** cells
  - `apply_layout(surface)` returns `(WindowLayout, UiRects)`; `WindowLayout` currently only carries `button_strip` (play geometry lives on `Grid`)
  - square cell count for layout is `(rows + 2) × (cols + 2)` (`VISIBLE_EXTRA_CELLS = 2`) so `bolderTile.png` ring is sized with the board
  - toolbar: `trim_sprite_to_opaque_bounds` removes empty alpha padding, then `fit_surface_to_rect` scales into toolbar slots
  - board geometry (`Grid`), layered drawing (border, ground, overlays, entities), icon-only toolbar buttons
- `backend_adapter.py`
  - `SolveResult` and `BackendAdapter` contract
  - `RealBackendAdapter`: calls backend `Maze` + `get_Astar_result`
- `simulation_backend_adapter.py`
  - `SimulationBackendAdapter`: deterministic scenarios for UI/QA
- `simulation_backend.py`
  - CLI helper that prints simulation outputs for quick validation

Removed in recent refactors (do not look for these):

- `snake_state_service.py` — deleted; there is no separate threading/playback service module anymore.

## Backend Contract

Real backend mode follows:

- `next(generator)` yields explored `(row, col)` cells
- `StopIteration.value` returns final `path`
- `maze.isValidPath(path)` provides validation text

Adapter return type `SolveResult`:

- `explored_positions: list[(row, col)]`
- `path: list[(row, col)]`
- `validation_result: str`

The viewer copies explored/path into `PlaybackState` for stepping animation; **`validation_result` is not stored on `FrontendState`** (only returned from `adapter.solve` / printed by `simulation_backend.py` unless you add UI for it later).

## Run

From `Frontend/`:

```bash
uv run python spider_viewer.py
```

From repository root (same app):

```bash
uv run python FE/spider_viewer.py
```


## Assets

Files used by the current viewer: `bolderTile.png`, `groundTile.png`, `Snack.png`, `Spider.png`, `start_button.png`, `restart_button.png`, `place_snack_button.png`.

`assets/next_step_button.png` is present but **not referenced** by code (reserved for a future step/advance control).
