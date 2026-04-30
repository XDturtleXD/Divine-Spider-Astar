"""Interactive spider viewer with backend/simulation adapters."""

from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from backend_adapter import RealBackendAdapter, SolveResult
from frontend_state import AppPhase, FrontendState, PlacementTool
from simulation_backend_adapter import SimulationBackendAdapter, SimulationScenario
from snake_render import Grid, SnakeRenderHandler, UiRects
from snake_scene import BOARD_COLS, BOARD_ROWS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spider maze renderer")
    parser.add_argument("--width", type=int, default=980, help="Initial window width")
    parser.add_argument("--height", type=int, default=720, help="Initial window height")
    parser.add_argument("--fps", type=int, default=60, help="Render FPS")
    parser.add_argument("--step-ms", type=int, default=90, help="Animation step interval (ms)")
    parser.add_argument(
        "--backend-mode",
        choices=["real", "simulation"],
        default="simulation",
        help="Use backend integration or local simulation adapter",
    )
    parser.add_argument(
        "--simulation-scenario",
        choices=[s.value for s in SimulationScenario],
        default=SimulationScenario.VALID.value,
        help="Simulation fixture when backend-mode is simulation",
    )
    parser.add_argument(
        "--assets-dir",
        type=str,
        default=str(Path(__file__).parent / "assets"),
        help="Directory containing frontend assets",
    )
    return parser.parse_args()


def resolve_adapter(args: argparse.Namespace):
    if args.backend_mode == "real":
        return RealBackendAdapter()
    return SimulationBackendAdapter(SimulationScenario(args.simulation_scenario))


def apply_solve_result(state: FrontendState, result: SolveResult) -> None:
    state.playback.explored = result.explored_positions
    state.playback.path = result.path
    state.playback.explored_index = 0
    state.playback.path_index = 0
    state.phase = AppPhase.EXPLORATION


def try_run(state: FrontendState, adapter, now_ms: int) -> None:
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

    apply_solve_result(state, result)
    if not result.path:
        state.set_toast("No path found.", now_ms)


def animate_state(state: FrontendState) -> None:
    if state.phase == AppPhase.EXPLORATION:
        if state.playback.explored_index < len(state.playback.explored):
            state.playback.explored_index += 1
            return
        state.phase = AppPhase.PATH
        return

    if state.phase == AppPhase.PATH and state.playback.path_index < len(state.playback.path):
        state.playback.path_index += 1


def handle_left_click(
    mouse_pos: tuple[int, int],
    state: FrontendState,
    ui_rects: UiRects,
    grid: Grid,
    adapter,
    now_ms: int,
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
            try_run(state, adapter, now_ms)
        return
    if ui_rects.reset_button.collidepoint(mouse_pos):
        state.clear_board()
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
    adapter = resolve_adapter(args)
    state = FrontendState()

    grid = Grid(BOARD_ROWS, BOARD_COLS)
    renderer = SnakeRenderHandler(args.assets_dir, grid)
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
                handle_left_click(event.pos, state, ui_rects, grid, adapter, now_ms)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                cell = grid.point_to_cell(*event.pos)
                if cell is not None:
                    state.remove_at(cell)

        ui_rects = renderer.draw(surface, state)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
