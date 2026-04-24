"""Standalone snake scene viewer using pygame-ce."""

from __future__ import annotations

import argparse
import threading
from pathlib import Path

import pygame

from snake_render import Grid, SnakeRenderHandler
from snake_scene import parse_scene_map
from snake_state_service import SceneStateService, run_simulation_frames


DEMO_FRAMES = [
    """
######
#S...#
#S*..#
#H...#
######
""",
    """
######
#....#
#SS*.#
#H...#
######
""",
    """
######
#....#
#S*..#
#SH..#
######
""",
    """
######
#....#
#*...#
#SSH.#
######
""",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snake ASCII scene renderer")
    parser.add_argument("--width", type=int, default=800, help="Initial window width")
    parser.add_argument("--height", type=int, default=600, help="Initial window height")
    parser.add_argument("--fps", type=int, default=30, help="Render FPS")
    parser.add_argument(
        "--sim-fps",
        type=float,
        default=2.0,
        help="Backend simulation updates per second",
    )
    parser.add_argument(
        "--assets-dir",
        type=str,
        default=str(Path(__file__).parent / "assets"),
        help="Directory containing bolderTile.png, groundTile.png, Snack.png",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pygame.init()
    pygame.display.set_caption("Snake Render Viewer")

    surface = pygame.display.set_mode((args.width, args.height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    initial_state = parse_scene_map(DEMO_FRAMES[0])
    state_service = SceneStateService(initial_state)
    grid = Grid(initial_state.rows, initial_state.cols, (args.width, args.height))
    renderer = SnakeRenderHandler(args.assets_dir, grid)

    stop_event = threading.Event()
    sim_thread = threading.Thread(
        target=run_simulation_frames,
        args=(state_service, stop_event, DEMO_FRAMES),
        kwargs={"frame_interval_s": 1.0 / max(args.sim_fps, 0.1)},
        daemon=True,
    )
    sim_thread.start()

    running = True
    last_version = -1
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    grid.resize((event.w, event.h))
                    renderer.reload_scaled_assets()

            state, version = state_service.get_current_state()
            if version != last_version:
                renderer.draw(surface, state)
                pygame.display.flip()
                last_version = version

            clock.tick(args.fps)
    finally:
        stop_event.set()
        sim_thread.join(timeout=1.0)
        pygame.quit()


if __name__ == "__main__":
    main()
