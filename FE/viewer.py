"""Interactive pygame viewer entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "BE"))

import pygame

from adapter import BackendAdapter
from assets import SpiderAssets
from config import BOARD_COLS, BOARD_ROWS
from drawer import SceneDrawer
from layout import Grid, LayoutManager, UiRects
from state import AppPhase, FrontendState, PlacementTool


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spider maze renderer")
    parser.add_argument("--width", type=int, default=980, help="Initial window width")
    parser.add_argument("--height", type=int, default=720, help="Initial window height")
    parser.add_argument("--fps", type=int, default=60, help="Render FPS")
    parser.add_argument("--step-ms", type=int, default=90, help="Animation step interval (ms)")
    parser.add_argument(
        "--assets-dir",
        type=str,
        default=str(Path(__file__).parent / "assets"),
        help="Directory containing frontend assets",
    )
    return parser.parse_args(argv)


def try_run(state: FrontendState, adapter: BackendAdapter, now_ms: int) -> None:
    if not state.can_run():
        state.set_toast("Need 1 spider and at least 1 snack.", now_ms)
        return
    assert state.spider is not None
    try:
        generator, maze = adapter.create_solver_generator(
            rows=BOARD_ROWS,
            cols=BOARD_COLS,
            spider=state.spider,
            snacks=set(state.snacks),
        )
    except Exception as exc:
        state.set_toast(f"Backend error: {exc}", now_ms, duration_ms=2600)
        return

    state.playback.reset()
    state.phase = AppPhase.EXPLORATION
    state.solver_generator = (generator, maze)
    state.solver_finished = False


def animate_state(state: FrontendState) -> None:
    if state.paused:
        return

    if (
        state.phase == AppPhase.EXPLORATION
        and not state.solver_finished
        and state.solver_generator is not None
    ):
        generator, _maze = state.solver_generator

        try:
            step = next(generator)
            state.playback.explored.append(step["pos"])
            state.playback.explored_remaining.append(step["remaining"])
            state.playback.explored_pq_top.append(step["pq_top"])
            state.playback.explored_index += 1
        except StopIteration as path_result:
            state.playback.path = path_result.value or []
            state.playback.path_index = 0
            state.solver_finished = True
            state.phase = AppPhase.PATH

    elif state.phase == AppPhase.PATH:
        if state.playback.path_index < len(state.playback.path):
            state.playback.path_index += 1


def handle_left_click(
    mouse_pos: tuple[int, int],
    state: FrontendState,
    ui_rects: UiRects,
    grid: Grid,
    adapter: BackendAdapter,
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
    if ui_rects.pause_button.collidepoint(mouse_pos):
        if state.phase != AppPhase.PLACEMENT:
            state.paused = not state.paused
        return
    if ui_rects.reset_button.collidepoint(mouse_pos):
        state.clear_board()
        return

    cell = grid.point_to_cell(*mouse_pos)
    if cell is not None:
        state.place_at(cell, now_ms)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    pygame.init()
    pygame.display.set_caption("Divine Spider Viewer")

    surface = pygame.display.set_mode((args.width, args.height), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    adapter = BackendAdapter()
    state = FrontendState()

    assets = SpiderAssets(args.assets_dir)
    grid = Grid(BOARD_ROWS, BOARD_COLS)
    layout_manager = LayoutManager(assets, grid)
    window_layout, ui_rects = layout_manager.update_layout(surface)
    drawer = SceneDrawer(assets, grid)
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
                window_layout, ui_rects = layout_manager.update_layout(surface)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_left_click(event.pos, state, ui_rects, grid, adapter, now_ms)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                cell = grid.point_to_cell(*event.pos)
                if cell is not None:
                    state.remove_at(cell)

        drawer.draw(surface, state, window_layout, ui_rects)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
