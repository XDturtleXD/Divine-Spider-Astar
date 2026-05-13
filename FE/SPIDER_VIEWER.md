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
   - right-side layer panel is visible but disabled (all slots dimmed, clicks ignored)
2. Exploration
   - explored cells are rendered with a dim yellow overlay
   - snacks stay visible
   - layer panel is visible but still non-clickable (animation in progress)
3. Path (sub-step view)
   - main grid switches to a per-layer sub-step view driven by the right-side layer selector
   - shows only the selected layer's `snacks_remaining`, the within-layer path segment (red tint), and the spider at the segment head
   - animation walks the segment; when finished, auto-advances to the next layer
   - clicking a layer in the right panel jumps to that layer's view (animation restarts from its entry)
4. Reset
   - clear placements, playback data, and layers
   - return to placement mode

## Modules

- `spider_viewer.py`
  - app entrypoint and single main loop
  - event handling for placement/buttons/layer slots
  - playback animation timing (`--step-ms`)
  - `--simulate-layers` flag forces the FE simulator for per-layer data
- `frontend_state.py`
  - app phase and placement tool enums
  - board placement/removal guards
  - toast message and playback indices for exploration/path animation (`PlaybackState` holds lists + indices; does not mirror `validation_result` from the backend)
  - `LayerView` dataclass and `path_to_layers(spider, snacks, path)` helper that decomposes a non-empty BE path into per-snack layers
  - `FrontendState.layers` / `selected_layer` and `set_layers` / `set_selected_layer` helpers
- `layer_simulator.py`
  - FE-owned simulator: `simulate_layers(spider, snacks)` returns canned `LayerView` data when BE doesn't (or can't) provide one
  - greedy nearest-neighbor snack ordering + L-shaped Manhattan segments, deterministic
- `spider_scene.py`
  - `BOARD_ROWS` / `BOARD_COLS` (`10`), `MAX_SNACKS` (`5`), `Position` alias
  - `build_maze_text(...)` for feeding the real backend adapter
- `spider_render.py`
  - `compute_window_layout(surface)` partitions the window into: top-left play field, top-right `layer_panel`, bottom `button_strip`; calls `Grid.fit_square_cells_in_rect(play_rect)` so the grid + one-tile border fits with **square** cells
  - `apply_layout(surface, num_layer_slots=1)` returns `(WindowLayout, UiRects)`; `WindowLayout` carries `button_strip` + `layer_panel`, `UiRects` carries the four toolbar rects + `layer_slot_rects`
  - square cell count for layout is `(rows + 2) × (cols + 2)` (`VISIBLE_EXTRA_CELLS = 2`) so `bolderTile.png` ring is sized with the board
  - toolbar: `trim_sprite_to_opaque_bounds` removes empty alpha padding, then `fit_surface_to_rect` scales into toolbar slots
  - board geometry (`Grid`), layered drawing (border, ground, overlays, entities), icon-only toolbar buttons, right-side layer panel using `assets/layer.png`
  - `draw(...)` branches: PATH phase with populated layers renders the sub-step view; everything else uses the global full-board renderer
- `backend_adapter.py`
  - `SolveResult` and `BackendAdapter` contract
  - calls backend `Maze` + `get_Astar_result`

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

## Layer Panel & Sub-step View

The right-side `layer_panel` shows one slot per layer (max `MAX_SNACKS + 1 = 6`).
A "layer" represents the conceptual A* sub-step between two consecutive snack eats:

- Layer 0: spider at start, all N snacks remaining, segment goes to the first snack.
- Layer k (1 ≤ k < N): spider at the snack that was just eaten, `N-k` snacks remaining, segment to the next snack.
- Layer N: spider at the last snack, 0 snacks remaining, empty segment (terminal).

Selected layer is outlined teal; other layers are dimmed. During placement (and while no layers are populated) the panel is fully disabled.

### Layer data providers (FE-owned)

Backend currently returns one flat path with no per-layer info, so the FE owns the layer dataset and has two providers:

1. `frontend_state.path_to_layers(spider, snacks, path)` — splits a non-empty BE path on snack hits.
2. `layer_simulator.simulate_layers(spider, snacks)` — canned data: greedy nearest-neighbor order + L-shaped Manhattan segments.

The viewer picks the provider in `apply_solve_result`:

- `--simulate-layers` flag OR empty BE path → simulator
- otherwise → real-path decomposition

## Run

From `FE/`:

```bash
uv run python spider_viewer.py
```

From repository root (same app):

```bash
uv run python FE/spider_viewer.py
```

Force the layer simulator (skips deriving from BE path even when BE returns one):

```bash
uv run python FE/spider_viewer.py --simulate-layers
```

## Assets

Files used by the current viewer: `bolderTile.png`, `groundTile.png`, `Snack.png`, `Spider.png`, `start_button.png`, `restart_button.png`, `place_snack_button.png`, `layer.png`.

`assets/next_step_button.png` is present but **not referenced** by code (reserved for a future step/advance control).
