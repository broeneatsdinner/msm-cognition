from __future__ import annotations

import contextlib
import io
import itertools
import math
import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dipster_solver import Board, advise, layouts, main, plan, solve


def naive_hits(board: Board) -> tuple[int, dict]:
    """Try every placement of the remaining Dipsters; the reference for solve()."""
    hidden = board.hidden
    found = board.found
    numbers = board.numbers
    count = 0
    hits = {tile: 0 for tile in hidden}
    for combo in itertools.combinations(hidden, board.dipsters - len(found)):
        dipsters = set(combo) | found
        if all(
            sum(1 for other in board.neighbors(tile) if other in dipsters) == number
            for tile, number in numbers.items()
        ):
            count += 1
            for tile in combo:
                hits[tile] += 1
    return count, hits


def naive_plan(board: Board, layout_list: list[frozenset]) -> Fraction:
    """Expected tokens to finish with no pruning and no merging of tiles; the reference for plan()."""
    memo: dict = {}

    def go(members: tuple[int, ...], dug: frozenset) -> Fraction:
        key = (members, dug)
        if key in memo:
            return memo[key]
        if len(members) == 1:
            value = Fraction(sum(board.cost(tile) for tile in layout_list[members[0]] - dug))
        else:
            value = None
            for tile in board.hidden:
                groups: dict[int, list[int]] = {}
                for index in members:
                    layout = layout_list[index]
                    result = -1 if tile in layout else sum(
                        1 for other in board.neighbors(tile) if other in layout or other in board.found
                    )
                    groups.setdefault(result, []).append(index)
                if len(groups) < 2:
                    continue
                expected = Fraction(board.cost(tile))
                for result, group in groups.items():
                    child_dug = dug | {tile} if result == -1 else dug
                    expected += Fraction(len(group), len(members)) * go(tuple(group), child_dug)
                if value is None or expected < value:
                    value = expected
        memo[key] = value
        return value

    return go(tuple(range(len(layout_list))), frozenset())


def random_board(rng: random.Random, rows: int, columns: int, dipsters: int, reveals: int) -> Board:
    """A board whose revealed tiles come from one real hidden layout."""
    tiles = [(row, column) for row in range(rows) for column in range(columns)]
    truth = set(rng.sample(tiles, dipsters))
    known = {}
    for tile in rng.sample(tiles, reveals):
        if tile in truth:
            known[tile] = "D"
        else:
            around = [
                (tile[0] + d_row, tile[1] + d_column)
                for d_row in (-1, 0, 1)
                for d_column in (-1, 0, 1)
                if d_row or d_column
            ]
            known[tile] = str(sum(1 for other in around if other in truth))
    rocks = {tile: rng.randint(1, 2) for tile in tiles if tile not in known and rng.random() < 0.15}
    return Board(rows, columns, dipsters, known, rocks)


class SolveTests(unittest.TestCase):
    def test_counts_match_trying_every_placement(self) -> None:
        rng = random.Random(7)
        for _ in range(60):
            rows, columns = rng.choice([(4, 4), (5, 5), (4, 5), (5, 4)])
            board = random_board(rng, rows, columns, rng.randint(2, 5), rng.randint(1, 8))
            count, hits = naive_hits(board)
            solution = solve(board)
            self.assertEqual(solution.layouts, count, board)
            self.assertEqual(solution.hits, hits, board)

    def test_untouched_board_is_spread_evenly(self) -> None:
        board = Board(6, 5, 7)
        solution = solve(board)
        self.assertEqual(solution.layouts, math.comb(30, 7))
        for tile in board.hidden:
            self.assertEqual(solution.chance(tile), Fraction(7, 30))

    def test_impossible_board_has_no_layouts(self) -> None:
        board = Board(3, 3, 1, {(1, 1): "2"})
        self.assertEqual(solve(board).layouts, 0)
        self.assertEqual(layouts(board), [])

    def test_layouts_lists_what_solve_counts(self) -> None:
        rng = random.Random(11)
        for _ in range(20):
            board = random_board(rng, 4, 5, 4, rng.randint(2, 7))
            listed = layouts(board)
            solution = solve(board)
            self.assertEqual(len(listed), solution.layouts)
            self.assertEqual(len(set(listed)), len(listed))
            for tile in board.hidden:
                self.assertEqual(sum(1 for layout in listed if tile in layout), solution.hits[tile])

    def test_rejects_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            Board(5, 5, 7, {(5, 0): "1"})
        with self.assertRaises(ValueError):
            Board(5, 5, 7, {(0, 0): "9"})
        with self.assertRaises(ValueError):
            Board(5, 5, 7, {(0, 0): "1"}, {(0, 0): 1})


class PlanTests(unittest.TestCase):
    def test_lookahead_matches_exhaustive_search(self) -> None:
        rng = random.Random(3)
        checked = 0
        while checked < 25:
            board = random_board(rng, 4, 4, rng.randint(2, 4), rng.randint(3, 8))
            layout_list = layouts(board)
            if not 2 <= len(layout_list) <= 30:
                continue
            expected, tile = plan(board, layout_list)
            self.assertEqual(expected, naive_plan(board, layout_list), board)
            self.assertIn(tile, board.hidden)
            checked += 1

    def test_one_layout_needs_only_its_dipsters(self) -> None:
        board = Board(1, 3, 1, {(0, 0): "0", (0, 1): "1"}, {(0, 2): 1})
        self.assertEqual(plan(board, layouts(board)), (Fraction(2), None))

    def test_cheaper_tile_goes_first_when_chances_tie(self) -> None:
        # One Dipster, on r0 c0 or on the rock at r0 c2, and digging tells nothing more.
        board = Board(1, 3, 1, {(0, 1): "1"}, {(0, 2): 1})
        expected, tile = plan(board, layouts(board))
        self.assertEqual(tile, (0, 0))
        self.assertEqual(expected, Fraction(2))


class AdviceTests(unittest.TestCase):
    def test_certain_dipster_is_named_and_dug(self) -> None:
        board = Board(1, 3, 1, {(0, 0): "0", (0, 1): "1"})
        advice = advise(board, solve(board))
        self.assertEqual(advice.certain, [(0, 2)])
        self.assertEqual(advice.tile, (0, 2))
        self.assertEqual(advice.expected, 1)

    def test_without_lookahead_best_chance_per_token_wins(self) -> None:
        # Center 3 on an open board: rocks halve the value of their tiles.
        rocks = {(1, 1): 1, (1, 2): 1, (1, 3): 1, (2, 1): 1, (2, 3): 1, (3, 1): 1, (3, 2): 1}
        board = Board(5, 5, 7, {(2, 2): "3"}, rocks)
        solution = solve(board)
        advice = advise(board, solution, lookahead_limit=0)
        self.assertIsNone(advice.expected)
        self.assertEqual(advice.tile, (3, 3))

    def test_finished_level_has_nothing_to_dig(self) -> None:
        board = Board(2, 2, 1, {(0, 0): "D"})
        self.assertIsNone(advise(board, solve(board)).tile)


class CommandLineTests(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(args))
        return code, output.getvalue()

    def test_prints_grid_and_next_dig(self) -> None:
        code, output = self.run_main(
            "--rows", "1", "--columns", "3", "--dipsters", "1", "--rock", "0,2", "0,1=1"
        )
        self.assertEqual(code, 0)
        self.assertIn("Layouts: 2", output)
        self.assertIn("0.50    1 0.50", output)
        self.assertIn("Next dig: r0 c0", output)

    def test_impossible_board_fails(self) -> None:
        code, _ = self.run_main("--size", "3", "--dipsters", "1", "1,1=2")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
