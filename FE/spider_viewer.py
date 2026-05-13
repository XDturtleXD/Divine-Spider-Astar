"""Interactive spider viewer."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "BE"))

import argparse
from pathlib import Path

import pygame

from backend_adapter import BackendAdapter, SolveResult
from frontend_state import AppPhase, FrontendState, PlacementTool, path_to_layers
from layer_simulator import simulate_layers
from spider_render import Grid, SpiderRenderHandler, UiRects
from spider_scene import BOARD_COLS, BOARD_ROWS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spider maze renderer")
    parser.add_argument("--width", type=int, default=980, help="Initial window width")
    parser.add_argument("--height", type=int, default=720, help="Initial window height")
    parser.add_argument("--fps", type=int, default=60, help="Render FPS")
    parser.add_argument("--step-ms", type=int, default=90, help="Animation step interval (ms)")
    parser.add_argument(
        "--simulate-layers",
        action="store_true",
        help="Force the FE layer simulator (skip deriving layers from the BE path).",
    )
    parser.add_argument(
        "--assets-dir",
        type=str,
        default=str(Path(__file__).parent / "assets"),
        help="Directory containing frontend assets",
    )
    return parser.parse_args()


def apply_solve_result(state: FrontendState, result: SolveResult, force_simulate: bool) -> None:
    """Apply the BE solve result and (re)build the per-layer dataset.

    Picks the layer provider:
    - `force_simulate=True` OR empty path -> `simulate_layers(...)`
    - otherwise -> `path_to_layers(...)` on the real BE path.
    """
    state.playback.explored = result.explored_positions
    state.playback.path = result.path
    state.playback.explored_index = 0
    state.playback.path_index = 0
    state.phase = AppPhase.EXPLORATION

    spider = state.spider
    snacks_sorted = sorted(state.snacks)
    if spider is None:
        state.set_layers([])
        return

    if force_simulate or not result.path:
        layers = simulate_layers(spider, snacks_sorted)
    else:
        layers = path_to_layers(spider, set(snacks_sorted), result.path)
    state.set_layers(layers)


def try_run(state: FrontendState, adapter, now_ms: int, force_simulate: bool) -> None:
    if not state.can_run():
        state.set_toast("Need 1 spider and at least 1 snack.", now_ms)
        return
    assert state.spider is not None
    try:
        result = adapter.solve(
            rows=BOARD_ROWS,
            cols=BOARD_COLS,
            spider=state.spider,
            snacks=set(state.snacks),
        )
    except Exception as exc:
        state.set_toast(f"Backend error: {exc}", now_ms, duration_ms=2600)
        return

    apply_solve_result(state, result, force_simulate)
    if not result.path and not force_simulate:
        state.set_toast("No path found (showing simulated layers).", now_ms)


def animate_state(state: FrontendState) -> None:
    """Advance exploration cursor, then per-layer path animation.

    Per-layer animation: `playback.path_index` walks within the currently
    selected layer's segment. When the segment finishes, auto-advance to
    the next layer (resetting path_index). Terminal layer stops the animation.
    Falls back to the flat BE path if `state.layers` is empty (defensive).
    """
    if state.phase == AppPhase.EXPLORATION:
        if state.playback.explored_index < len(state.playback.explored):
            state.playback.explored_index += 1
            return
        state.phase = AppPhase.PATH
        state.playback.path_index = 0
        return

    if state.phase != AppPhase.PATH:
        return

    if not state.layers:
        if state.playback.path_index < len(state.playback.path):
            state.playback.path_index += 1
        return

    if state.selected_layer >= len(state.layers):
        return
    current_layer = state.layers[state.selected_layer]
    if state.playback.path_index < len(current_layer.segment):
        state.playback.path_index += 1
        return

    if state.selected_layer < len(state.layers) - 1:
        state.selected_layer += 1
        state.playback.path_index = 0


def handle_left_click(
    mouse_pos: tuple[int, int],
    state: FrontendState,
    ui_rects: UiRects,
    grid: Grid,
    adapter,
    now_ms: int,
    force_simulate: bool,
) -> None:
    if ui_rects.spider_button.collidepoint(mouse_pos):
        if state.phase == AppPhase.PLACEMENT:
            state.set_tool(PlacementTool.SPIDER)
        return
    if ui_rects.snack_button.collidepoint(mouse_pos):
        if state.phase == AppPhase.PLACEMENT:
            state.set_tool(PlacementTool.SNACK)
        return
    if ui_rects.run_button.collidepoint(mouse_pos):
        if state.phase == AppPhase.PLACEMENT:
            try_run(state, adapter, now_ms, force_simulate)
        return
    if ui_rects.reset_button.collidepoint(mouse_pos):
        state.clear_board()
        return

    # Layer slots are clickable only outside placement and only when layers exist.
    if state.phase != AppPhase.PLACEMENT and state.layers:
        for idx, slot in enumerate(ui_rects.layer_slot_rects):
            if slot.collidepoint(mouse_pos):
                state.set_selected_layer(idx)
                state.playback.path_index = 0
                return

    cell = grid.point_to_cell(*mouse_pos)
    if cell is not None:
        state.place_at(cell, now_ms)


def main() -> None:
    args = parse_args()
    pygame.init()
    pygame.display.set_caption("Divine Spider Viewer")

    surface = pygame.display.set_mode((args.width, args.height), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    adapter = BackendAdapter()
    state = FrontendState()

    grid = Grid(BOARD_ROWS, BOARD_COLS)
    renderer = SpiderRenderHandler(args.assets_dir, grid)
    _, ui_rects = renderer.apply_layout(surface)
    elapsed_for_step = 0.0

    running = True
    while running:
        dt_ms = clock.tick(args.fps)
        now_ms = pygame.time.get_ticks()
        state.clear_toast_if_expired(now_ms)
        elapsed_for_step += dt_ms

        while elapsed_for_step >= args.step_ms:
            animate_state(state)
            elapsed_for_step -= args.step_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_left_click(event.pos, state, ui_rects, grid, adapter, now_ms, args.simulate_layers)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                cell = grid.point_to_cell(*event.pos)
                if cell is not None:
                    state.remove_at(cell)

        ui_rects = renderer.draw(surface, state)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
