"""CLI preview for deterministic frontend simulation backend outputs."""

from __future__ import annotations

import argparse

from simulation_backend_adapter import SimulationBackendAdapter, SimulationScenario


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview simulation backend output")
    parser.add_argument(
        "--scenario",
        choices=[s.value for s in SimulationScenario],
        default=SimulationScenario.VALID.value,
        help="Simulation scenario to print",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    adapter = SimulationBackendAdapter(SimulationScenario(args.scenario))

    spider = (1, 1)
    snacks = {(2, 7), (7, 5), (8, 2)}
    result = adapter.solve(rows=10, cols=10, spider=spider, snacks=snacks)

    print("Scenario :", args.scenario)
    print("Explored :", len(result.explored_positions), "states")
    print("Path len :", len(result.path))
    print("Path     :", result.path)
    print("Valid?   :", result.validation_result)


if __name__ == "__main__":
    main()
