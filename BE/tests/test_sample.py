from pathlib import Path
from backend import get_Astar_result, mst_heuristic, remaining_color_index
from maze import Maze
import pytest

BIG_MAZE = str(Path(__file__).parent / "bigMaze.txt")

# ── Maze fixtures ─────────────────────────────────────────────────────────────

SINGLE = """\
#########
#H......#
#.......#
#......*#
#########
"""
# Start: (1,1)  Objective: (3,7)  Dimensions: (5,9)

MULTI = """\
#####
#H.*#
#####
"""
# Start: (1,1)  Objective: (1,3)  Single goal

MULTI_GOAL = """\
#######
#H.*.*#
#######
"""
# Start: (1,1)  Objectives: (1,3) and (1,5)  Two goals

UNREACHABLE = """\
#####
#H#*#
#####
"""
# Start: (1,1)  Objective: (1,3)  Wall at (1,2) — no path exists

# ── Helpers ───────────────────────────────────────────────────────────────────

def bfs(maze):
    """BFS for single-goal mazes only. Returns path excluding start."""
    queue = []
    queue.append(maze.getStart())
    start = maze.getStart()
    goal = maze.getObjectives()
    parents = {}
    parents[start] = (-1, -1)

    while queue:
        node = queue.pop(0)
        if node == goal[0]:
            path = []
            while node != start:
                path.append(node)
                node = parents[node]
            path.reverse()
            return path

        neighbors = maze.getNeighbors(node[0], node[1])
        for n in neighbors:
            if n in parents:
                continue
            parents[n] = node
            queue.append(n)
    return []


def make_maze(text: str) -> Maze:
    return Maze(text)


def get_astar_path(maze):
    """Drain the A* generator and return the final path (or None if unreachable)."""
    gen = get_Astar_result(maze)
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def collect_steps(maze):
    """Collect all yielded dicts from the A* generator (discards final path)."""
    gen = get_Astar_result(maze)
    steps = []
    try:
        while True:
            steps.append(next(gen))
    except StopIteration:
        pass
    return steps


# ── Single-goal correctness ───────────────────────────────────────────────────

class TestPathfinding:

    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, BIG_MAZE])
    def test_path_length_consistency(self, maze_text):
        """A* path length must match BFS (optimal) for single-goal mazes."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        bfs_path = bfs(maze)

        assert len(astar_path) == len(bfs_path), \
            f"A* length {len(astar_path)} != BFS length {len(bfs_path)}"

    @pytest.mark.parametrize("maze_text", [SINGLE, MULTI, BIG_MAZE])
    def test_astar_reaches_goal(self, maze_text):
        """A* path must be physically valid and end at a goal."""
        maze = make_maze(maze_text)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert maze.isValidPath(astar_path) == "Valid", \
            "The path returned by A* is invalid according to maze rules."
        assert len(astar_path) > 0, "A* failed to find a path."
        assert astar_path[-1] in goals, \
            f"Path ended at {astar_path[-1]}, which is not a goal {goals}."


# ── Multi-goal correctness ────────────────────────────────────────────────────

class TestMultiGoal:

    def test_all_objectives_collected(self):
        """A* must visit every objective in a multi-goal maze."""
        maze = make_maze(MULTI_GOAL)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert len(goals) > 1, "Fixture must have more than one goal"
        assert maze.isValidPath(astar_path) == "Valid"
        for goal in goals:
            assert goal in astar_path, f"Objective {goal} was not visited"

    def test_multi_goal_ends_at_a_goal(self):
        """The final position in a multi-goal path must be one of the objectives."""
        maze = make_maze(MULTI_GOAL)
        astar_path = get_astar_path(maze)
        goals = maze.getObjectives()

        assert astar_path[-1] in goals


# ── Unreachable goal ──────────────────────────────────────────────────────────

class TestUnreachable:

    def test_unreachable_goal_returns_empty(self):
        """A* must return an empty list when no path to the goal exists."""
        maze = make_maze(UNREACHABLE)
        assert get_astar_path(maze) == []


# ── Maze parsing ──────────────────────────────────────────────────────────────

class TestMaze:

    def test_start_parsed_correctly(self):
        assert make_maze(SINGLE).getStart() == (1, 1)

    def test_objective_parsed_correctly(self):
        assert make_maze(SINGLE).getObjectives() == [(3, 7)]

    def test_dimensions_parsed_correctly(self):
        assert make_maze(SINGLE).getDimensions() == (5, 9)

    def test_multi_goal_objective_count(self):
        assert len(make_maze(MULTI_GOAL).getObjectives()) == 2

    def test_string_and_file_give_same_result(self):
        """Maze loaded from a file and from its string content must be equivalent."""
        maze_from_file = Maze(BIG_MAZE)
        with open(BIG_MAZE) as f:
            content = f.read()
        maze_from_string = Maze(content)

        assert maze_from_file.getStart() == maze_from_string.getStart()
        assert maze_from_file.getObjectives() == maze_from_string.getObjectives()
        assert maze_from_file.getDimensions() == maze_from_string.getDimensions()

    def test_neighbors_interior_cell(self):
        """An interior open cell should have 4 neighbors."""
        maze = make_maze(SINGLE)
        assert len(maze.getNeighbors(2, 4)) == 4

    def test_neighbors_corner_cell(self):
        """The start cell (1,1) is bounded by walls on two sides — 2 neighbors only."""
        maze = make_maze(SINGLE)
        assert len(maze.getNeighbors(1, 1)) == 2


# ── isValidPath edge cases ────────────────────────────────────────────────────

class TestIsValidPath:

    def test_empty_path_invalid(self):
        assert make_maze(SINGLE).isValidPath([]) != "Valid"

    def test_astar_path_is_valid(self):
        maze = make_maze(SINGLE)
        assert maze.isValidPath(get_astar_path(maze)) == "Valid"

    def test_path_through_wall(self):
        maze = make_maze(SINGLE)
        # (0,1) is a wall; single hop from start (1,1) -> (0,1)
        assert maze.isValidPath([(1, 1), (0, 1)]) != "Valid"

    def test_path_misses_goal(self):
        maze = make_maze(SINGLE)
        # Valid moves but goal (3,7) never reached
        assert maze.isValidPath([(1, 2), (1, 3), (1, 4)]) != "Valid"

    def test_path_visits_goal_but_does_not_end_there(self):
        maze = make_maze(SINGLE)
        # Passes through (3,7) but continues to (2,7)
        path = [(1,2),(2,2),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(2,7)]
        assert maze.isValidPath(path) != "Valid"

    def test_non_consecutive_steps(self):
        maze = make_maze(SINGLE)
        # Teleports from start directly to goal — Manhattan distance 8
        assert maze.isValidPath([(1, 1), (3, 7)]) != "Valid"

    def test_path_not_a_list(self):
        assert make_maze(SINGLE).isValidPath("not a list") != "Valid"

    def test_path_position_not_tuple(self):
        assert make_maze(SINGLE).isValidPath([1, 2]) != "Valid"

    def test_path_position_wrong_length(self):
        assert make_maze(SINGLE).isValidPath([(1,)]) != "Valid"

    def test_path_with_unnecessary_revisit(self):
        maze = make_maze(SINGLE)
        # Revisits (1,2) with no objective collected between the two visits
        path = [(1,2), (1,1), (1,2), (1,3), (1,4), (1,5), (1,6), (1,7), (2,7), (3,7)]
        assert maze.isValidPath(path) != "Valid"


# ── Maze constructor input validation ─────────────────────────────────────────

class TestMazeValidation:

    def test_empty_input(self):
        with pytest.raises(ValueError, match="empty"):
            Maze("")

    def test_jagged_rows(self):
        with pytest.raises(ValueError, match="same length"):
            Maze("#####\n#H.*##\n#####\n")

    def test_too_many_rows(self):
        # 101 rows: border + H-row + *-row + 98 more border rows
        body = "###\n" + "#H#\n" + "#*#\n" + "###\n" * 98
        with pytest.raises(ValueError, match="row limit"):
            Maze(body)

    def test_too_many_cols(self):
        # 101-column maze — one column over MAX_COLS
        wide = "#" * 101
        inner = "#H" + "." * 97 + "*#"   # 2 + 97 + 2 = 101 chars
        with pytest.raises(ValueError, match="column limit"):
            Maze(f"{wide}\n{inner}\n{wide}\n")

    def test_invalid_char(self):
        with pytest.raises(ValueError, match="Invalid character"):
            Maze("#####\n#HX*#\n#####\n")

    def test_no_start(self):
        with pytest.raises(ValueError, match="no start"):
            Maze("#####\n#..*#\n#####\n")

    def test_multiple_starts(self):
        with pytest.raises(ValueError, match="start positions"):
            Maze("#####\n#HH*#\n#####\n")

    def test_no_objective(self):
        with pytest.raises(ValueError, match="no objectives"):
            Maze("#####\n#H..#\n#####\n")

    def test_too_many_objectives(self):
        # 4 objectives — one over MAX_OBJECTIVES (3)
        inner = "#H" + "*" * 4 + "#"   # 7 chars
        border = "#" * 7
        with pytest.raises(ValueError, match="objective limit"):
            Maze(f"{border}\n{inner}\n{border}\n")


# ── Yield format ──────────────────────────────────────────────────────────────

from backend import PQ_SNAPSHOT_K

class TestYieldFormat:

    def test_each_step_is_dict(self):
        steps = collect_steps(make_maze(SINGLE))
        assert all(isinstance(s, dict) for s in steps)

    def test_dict_keys(self):
        steps = collect_steps(make_maze(SINGLE))
        for s in steps:
            assert set(s.keys()) == {"pos", "remaining", "color", "cost", "pq_top"}

    def test_pos_is_two_int_tuple(self):
        steps = collect_steps(make_maze(SINGLE))
        for s in steps:
            pos = s["pos"]
            assert isinstance(pos, tuple) and len(pos) == 2
            assert all(isinstance(x, int) for x in pos)

    def test_remaining_is_frozenset(self):
        steps = collect_steps(make_maze(SINGLE))
        for s in steps:
            assert isinstance(s["remaining"], frozenset)

    def test_cost_keys_and_nonnegative(self):
        steps = collect_steps(make_maze(SINGLE))
        for s in steps:
            cost = s["cost"]
            assert set(cost.keys()) == {"g", "h"}
            assert cost["g"] >= 0
            assert cost["h"] >= 0

    def test_pq_top_is_tuple_of_entries(self):
        """Each pq_top entry must be (int, 2-tuple, frozenset)."""
        steps = collect_steps(make_maze(SINGLE))
        for s in steps:
            assert isinstance(s["pq_top"], tuple)
            for f, pos, rem in s["pq_top"]:
                assert isinstance(f, int)
                assert isinstance(pos, tuple) and len(pos) == 2
                assert isinstance(rem, frozenset)

    def test_pq_top_length_bounded(self):
        steps = collect_steps(make_maze(SINGLE))
        assert all(len(s["pq_top"]) <= PQ_SNAPSHOT_K for s in steps)

    def test_terminal_step_remaining_empty_and_h_zero(self):
        """The last yielded step must have empty remaining and h == 0."""
        steps = collect_steps(make_maze(SINGLE))
        last = steps[-1]
        assert last["remaining"] == frozenset()
        assert last["cost"]["h"] == 0

    def test_multi_goal_remaining_shrinks_monotonically(self):
        """Across a two-goal maze, len(remaining) never increases between steps."""
        steps = collect_steps(make_maze(MULTI_GOAL))
        sizes = [len(s["remaining"]) for s in steps]
        assert sizes == sorted(sizes, reverse=True)


# ── Yield semantics: g/h correctness ──────────────────────────────────────────

class TestYieldCosts:

    def test_initial_step_g_zero(self):
        """First yielded step is the start state — g must be 0."""
        steps = collect_steps(make_maze(SINGLE))
        assert steps[0]["cost"]["g"] == 0

    def test_initial_step_pos_is_start(self):
        """First yielded step's pos must equal maze start."""
        maze = make_maze(SINGLE)
        steps = collect_steps(maze)
        assert steps[0]["pos"] == maze.getStart()

    def test_initial_step_h_matches_mst(self):
        """First yielded step's h must equal mst_heuristic(start, all_objectives)."""
        maze = make_maze(MULTI_GOAL)
        steps = collect_steps(maze)
        expected_h = mst_heuristic(maze.getStart(), frozenset(maze.getObjectives()))
        assert steps[0]["cost"]["h"] == expected_h

    def test_terminal_g_equals_path_length(self):
        """Terminal step's g (steps from start) must equal returned path length."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            maze = make_maze(fixture)
            gen = get_Astar_result(maze)
            last_step = None
            try:
                while True:
                    last_step = next(gen)
            except StopIteration as e:
                path = e.value
            assert last_step is not None
            assert last_step["cost"]["g"] == len(path), \
                f"Fixture {fixture!r}: terminal g={last_step['cost']['g']} but path len={len(path)}"

    def test_cost_h_matches_mst_heuristic_each_step(self):
        """Cached h must equal a fresh mst_heuristic call for every yielded state."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            steps = collect_steps(make_maze(fixture))
            for s in steps:
                expected = mst_heuristic(s["pos"], s["remaining"])
                assert s["cost"]["h"] == expected, \
                    f"h mismatch at pos={s['pos']} remaining={s['remaining']}: cached={s['cost']['h']} fresh={expected}"

    def test_step_count_equals_states_explored(self):
        """One yield per A* expansion: step count must equal Maze.getStatesExplored()."""
        maze = make_maze(SINGLE)
        steps = collect_steps(maze)
        assert len(steps) == maze.getStatesExplored()


# ── Yield semantics: pq_top ──────────────────────────────────────────────────

class TestPqTop:

    def test_pq_top_sorted_by_f_ascending(self):
        """pq_top entries must be ordered by f_cost ascending."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            steps = collect_steps(make_maze(fixture))
            for s in steps:
                f_values = [entry[0] for entry in s["pq_top"]]
                assert f_values == sorted(f_values), \
                    f"pq_top not sorted at pos={s['pos']}: f_values={f_values}"

    def test_pq_top_entries_not_in_visited(self):
        """pq_top must never re-list the just-expanded state itself."""
        steps = collect_steps(make_maze(MULTI_GOAL))
        for s in steps:
            current_state = (s["pos"], s["remaining"])
            for _f, p, rem in s["pq_top"]:
                assert (p, rem) != current_state, \
                    f"pq_top re-lists just-expanded state {current_state}"

    def test_pq_top_empty_on_terminal_step(self):
        """Terminal step expands no neighbors and has no live frontier left for the goal layer.
        The heap may still contain unexplored layers; allow ≤ K, but the cell just expanded
        (with remaining=∅) must not reappear."""
        steps = collect_steps(make_maze(SINGLE))
        last = steps[-1]
        for _f, p, rem in last["pq_top"]:
            assert not (p == last["pos"] and rem == last["remaining"])


# ── Yield semantics: unreachable ──────────────────────────────────────────────

class TestUnreachableYield:

    def test_unreachable_yields_at_least_start(self):
        """Unreachable maze must still yield the start expansion before returning []."""
        steps = collect_steps(make_maze(UNREACHABLE))
        assert len(steps) >= 1

    def test_unreachable_no_terminal_step(self):
        """No yielded step on an unreachable maze should have empty remaining."""
        steps = collect_steps(make_maze(UNREACHABLE))
        for s in steps:
            assert s["remaining"] != frozenset(), \
                "Unreachable maze yielded a terminal (remaining=∅) step"

    def test_unreachable_returns_empty_path(self):
        """Sanity: generator return value on unreachable is []."""
        gen = get_Astar_result(make_maze(UNREACHABLE))
        try:
            while True:
                next(gen)
        except StopIteration as e:
            assert e.value == []


# ── Color index for remaining ─────────────────────────────────────────────────

class TestRemainingColorIndex:
    """Direct tests of the helper. Bitmask + 1 over a sorted objective tuple."""

    def test_empty_remaining_is_one(self):
        objs = ((1, 1), (2, 2), (3, 3))
        assert remaining_color_index(frozenset(), objs) == 1

    def test_all_remaining_is_full_bitmask(self):
        objs = ((1, 1), (2, 2), (3, 3))
        # All three set: 0b111 + 1 = 8
        assert remaining_color_index(frozenset(objs), objs) == 8

    def test_single_bit_set(self):
        objs = ((1, 1), (2, 2), (3, 3))
        # Only the second objective remaining → 0b010 + 1 = 3
        assert remaining_color_index(frozenset({(2, 2)}), objs) == 3

    def test_distinct_subsets_distinct_indices(self):
        """All 2**N subsets must produce distinct indices."""
        objs = ((0, 0), (0, 1), (0, 2))
        seen = set()
        # Iterate every subset via the bitmask itself
        for mask in range(1 << len(objs)):
            subset = frozenset(o for i, o in enumerate(objs) if mask & (1 << i))
            seen.add(remaining_color_index(subset, objs))
        assert seen == set(range(1, 1 << len(objs) | 1))  # {1..8}

    def test_range_bounded_1_to_8_for_3_objectives(self):
        objs = ((0, 0), (1, 1), (2, 2))
        for mask in range(1 << len(objs)):
            subset = frozenset(o for i, o in enumerate(objs) if mask & (1 << i))
            c = remaining_color_index(subset, objs)
            assert 1 <= c <= 8

    def test_stable_across_calls(self):
        objs = ((0, 0), (1, 1), (2, 2))
        s = frozenset({(0, 0), (2, 2)})
        assert remaining_color_index(s, objs) == remaining_color_index(s, objs)


# ── Color in yielded steps ────────────────────────────────────────────────────

class TestYieldColor:

    def test_initial_step_color_is_full_bitmask(self):
        """First yield has all objectives remaining → color = 2**N."""
        maze = make_maze(MULTI_GOAL)
        steps = collect_steps(maze)
        n_obj = len(maze.getObjectives())
        assert steps[0]["color"] == (1 << n_obj)

    def test_terminal_step_color_is_one(self):
        """Last yield has empty remaining → color = 1."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            steps = collect_steps(make_maze(fixture))
            assert steps[-1]["color"] == 1

    def test_color_in_range_1_to_8(self):
        """With MAX_OBJECTIVES = 3, color must always fall in 1..8."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            steps = collect_steps(make_maze(fixture))
            for s in steps:
                assert 1 <= s["color"] <= 8

    def test_color_matches_helper(self):
        """Yielded color must equal remaining_color_index over the maze's original objectives."""
        for fixture in (SINGLE, MULTI, MULTI_GOAL):
            maze = make_maze(fixture)
            objs = tuple(sorted(maze.getObjectives()))
            for s in collect_steps(maze):
                assert s["color"] == remaining_color_index(s["remaining"], objs)

    def test_same_remaining_same_color_across_steps(self):
        """Two yields with the same remaining must share the same color."""
        steps = collect_steps(make_maze(MULTI_GOAL))
        by_remaining: dict[frozenset, int] = {}
        for s in steps:
            r = s["remaining"]
            if r in by_remaining:
                assert by_remaining[r] == s["color"]
            else:
                by_remaining[r] = s["color"]

    def test_color_nonincreasing_along_run(self):
        """color = bitmask(remaining)+1, and remaining shrinks monotonically — color must be non-increasing."""
        steps = collect_steps(make_maze(MULTI_GOAL))
        colors = [s["color"] for s in steps]
        assert colors == sorted(colors, reverse=True)
