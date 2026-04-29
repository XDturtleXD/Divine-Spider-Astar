# Snake Viewer (Independent Renderer)

This repo now includes an independent pygame-ce snake scene viewer that renders
ASCII map snapshots like:

```
######
#S...#
#S*..#
#H...#
######
```

Character mapping:

- `#` -> border tile (`assets/bolderTile.png`)
- `.` and other non-special chars -> ground tile (`assets/groundTile.png`)
- `*` -> snack/cake sprite (`assets/Snack.png`)
- `S` -> snake body (orange overlay)
- `H` -> snake head (red overlay)

Render order is:

1. grid base (border/ground)
2. snacks
3. snake body
4. snake head

## Architecture

- `snake_scene.py`
  - `SceneState` dataclass
  - `parse_scene_map(scene_text)` parser for ASCII scenes
- `snake_render.py`
  - `Grid` class controls row/col rect math and resize behavior
  - `SnakeRenderHandler` scales assets and renders layers
- `snake_state_service.py`
  - thread-safe state store with `get_current_state()`
  - simulation loop that updates current state
- `snake_viewer.py`
  - standalone entrypoint
  - main pygame thread for render/update
  - background simulation thread for scene updates

## Run with uv

```bash
uv sync
uv run python snake_viewer.py
```

Optional args:

```bash
uv run python snake_viewer.py --width 1000 --height 700 --fps 60 --sim-fps 3
```

Notes:

- This viewer is independent from `hw1.py`, `agent.py`, and `maze.py`.
- Legacy homework flow remains unchanged.
