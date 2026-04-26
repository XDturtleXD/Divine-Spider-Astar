"""Thread-safe scene state service and simulation loop."""

from __future__ import annotations

import threading
import time
from dataclasses import replace

from snake_scene import SceneState, parse_scene_map


class SceneStateService:
    """Shared state holder used by backend simulation and renderer."""

    def __init__(self, initial_state: SceneState) -> None:
        self._lock = threading.Lock()
        self._state = initial_state
        self._version = 0

    def set_state_from_text(self, scene_text: str) -> None:
        new_state = parse_scene_map(scene_text)
        with self._lock:
            self._state = new_state
            self._version += 1

    def get_current_state(self) -> tuple[SceneState, int]:
        with self._lock:
            # SceneState is immutable, but we still return a copy-like object
            # to keep a stable public contract.
            return replace(self._state), self._version


def run_simulation_frames(
    state_service: SceneStateService,
    stop_event: threading.Event,
    frames: list[str],
    frame_interval_s: float = 0.45,
) -> None:
    """Simulation thread: periodically writes current scene snapshots."""
    idx = 0
    if not frames:
        return

    while not stop_event.is_set():
        state_service.set_state_from_text(frames[idx])
        idx = (idx + 1) % len(frames)
        time.sleep(frame_interval_s)
