#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from fractions import Fraction


Tile = tuple[int, int]


def parse_tile(text: str) -> tuple[Tile, str]:
    position, value = text.split("=")
    row, column = (int(part) for part in position.split(","))
    return (row, column), value.strip().upper()


def parse_rock(text: str) -> tuple[Tile, int]:
    position, _, digs = text.partition("=")
    row, column = (int(part) for part in position.split(","))
    return (row, column), int(digs) if digs else 1


def neighbors(row: int, column: int, rows: int, columns: int) -> list[Tile]:
    return [
        (row + d_row, column + d_column)
        for d_row in (-1, 0, 1)
        for d_column in (-1, 0, 1)
        if (d_row or d_column)
        and 0 <= row + d_row < rows
        and 0 <= column + d_column < columns
    ]


def tile_name(tile: Tile) -> str:
    return f"r{tile[0]} c{tile[1]}"


@dataclass
class Board:
    rows: int
    columns: int
    dipsters: int
    known: dict[Tile, str] = field(default_factory=dict)
    # Digs a rock tile still needs before a further dig reveals it.
    rocks: dict[Tile, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for tile, value in self.known.items():
            if not self.on_board(tile):
                raise ValueError(f"{tile_name(tile)} is off the board")
            if value != "D" and not (value.isdigit() and int(value) <= 8):
                raise ValueError(f"{tile_name(tile)}={value} is not a number or D")
        for tile, digs in self.rocks.items():
            if not self.on_board(tile):
                raise ValueError(f"rock {tile_name(tile)} is off the board")
            if tile in self.known:
                raise ValueError(f"rock {tile_name(tile)} is also listed as revealed")
            if digs < 0:
                raise ValueError(f"rock {tile_name(tile)} needs a dig count of 0 or more")

    def on_board(self, tile: Tile) -> bool:
        return 0 <= tile[0] < self.rows and 0 <= tile[1] < self.columns

    def neighbors(self, tile: Tile) -> list[Tile]:
        return neighbors(*tile, self.rows, self.columns)

    @property
    def found(self) -> set[Tile]:
        return {tile for tile, value in self.known.items() if value == "D"}

    @property
    def numbers(self) -> dict[Tile, int]:
        return {tile: int(value) for tile, value in self.known.items() if value != "D"}

    @property
    def hidden(self) -> list[Tile]:
        return [
            (row, column)
            for row in range(self.rows)
            for column in range(self.columns)
            if (row, column) not in self.known
        ]

    def cost(self, tile: Tile) -> int:
        return self.rocks.get(tile, 0) + 1


@dataclass
class Solution:
    layouts: int
    hits: dict[Tile, int]

    def chance(self, tile: Tile) -> Fraction:
        return Fraction(self.hits[tile], self.layouts)


@dataclass
class _Split:
    """Hidden tiles split into groups tied together by numbers, plus the free rest."""

    remaining: int
    groups: list[tuple[list[Tile], list[tuple[list[int], int]]]]
    unconstrained: list[Tile]


def _split(board: Board) -> _Split | None:
    remaining = board.dipsters - len(board.found)
    if remaining < 0:
        return None
    hidden = set(board.hidden)
    found = board.found
    constraints = []
    for tile, count in board.numbers.items():
        around = board.neighbors(tile)
        need = count - sum(1 for other in around if other in found)
        open_tiles = [other for other in around if other in hidden]
        if need < 0 or need > len(open_tiles):
            return None
        if open_tiles:
            constraints.append((open_tiles, need))

    parent = {tile: tile for tiles, _ in constraints for tile in tiles}

    def root(tile: Tile) -> Tile:
        while parent[tile] != tile:
            parent[tile] = parent[parent[tile]]
            tile = parent[tile]
        return tile

    for tiles, _ in constraints:
        for tile in tiles[1:]:
            parent[root(tile)] = root(tiles[0])

    grouped: dict[Tile, tuple[list[Tile], list[tuple[list[Tile], int]]]] = {}
    for tile in sorted(parent):
        grouped.setdefault(root(tile), ([], []))[0].append(tile)
    for tiles, need in constraints:
        grouped[root(tiles[0])][1].append((tiles, need))

    groups = []
    for tiles, group_constraints in grouped.values():
        index = {tile: position for position, tile in enumerate(tiles)}
        groups.append(
            (tiles, [([index[tile] for tile in members], need) for members, need in group_constraints])
        )
    unconstrained = [tile for tile in board.hidden if tile not in parent]
    return _Split(remaining, groups, unconstrained)


def _assignments(tiles: list[Tile], constraints: list[tuple[list[int], int]]):
    """Yield each set of tile positions that satisfies every constraint in a group."""
    by_tile: list[list[int]] = [[] for _ in tiles]
    for number, (members, _) in enumerate(constraints):
        for position in members:
            by_tile[position].append(number)
    needs = [need for _, need in constraints]
    placed = [0] * len(constraints)
    open_counts = [len(members) for members, _ in constraints]
    chosen: list[int] = []

    def visit(position: int):
        if position == len(tiles):
            yield chosen
            return
        for value in (0, 1):
            if any(
                placed[number] + value > needs[number]
                or placed[number] + value + open_counts[number] - 1 < needs[number]
                for number in by_tile[position]
            ):
                continue
            for number in by_tile[position]:
                placed[number] += value
                open_counts[number] -= 1
            if value:
                chosen.append(position)
            yield from visit(position + 1)
            if value:
                chosen.pop()
            for number in by_tile[position]:
                placed[number] -= value
                open_counts[number] += 1

    yield from visit(0)


def _convolve(left: dict[int, int], right: dict[int, int]) -> dict[int, int]:
    result: dict[int, int] = {}
    for left_count, left_ways in left.items():
        for right_count, right_ways in right.items():
            total = left_count + right_count
            result[total] = result.get(total, 0) + left_ways * right_ways
    return result


def solve(board: Board) -> Solution:
    """Count every Dipster layout that fits the board, and how many put one on each tile.

    Only tiles next to a revealed number are enumerated, group by group; tiles
    no number touches are counted with binomials, so large boards stay fast.
    """
    split = _split(board)
    if split is None:
        return Solution(0, {})

    # For each group: ways to place k Dipsters in it, and per-tile hits for each k.
    summaries = []
    for tiles, constraints in split.groups:
        ways: dict[int, int] = {}
        hits: dict[int, list[int]] = {}
        for chosen in _assignments(tiles, constraints):
            count = len(chosen)
            ways[count] = ways.get(count, 0) + 1
            tile_hits = hits.setdefault(count, [0] * len(tiles))
            for position in chosen:
                tile_hits[position] += 1
        summaries.append((tiles, ways, hits))

    free = len(split.unconstrained)

    def weight(grouped_count: int) -> int:
        rest = split.remaining - grouped_count
        return math.comb(free, rest) if 0 <= rest <= free else 0

    totals: dict[int, int] = {0: 1}
    for _, ways, _ in summaries:
        totals = _convolve(totals, ways)
    layout_count = sum(ways * weight(count) for count, ways in totals.items())
    if not layout_count:
        return Solution(0, {})

    result = {tile: 0 for tile in board.hidden}
    for index, (tiles, _, hits) in enumerate(summaries):
        others: dict[int, int] = {0: 1}
        for other_index, (_, ways, _) in enumerate(summaries):
            if other_index != index:
                others = _convolve(others, ways)
        for count, tile_hits in hits.items():
            factor = sum(ways * weight(count + other) for other, ways in others.items())
            for tile, tile_hit in zip(tiles, tile_hits):
                result[tile] += tile_hit * factor
    for tile in split.unconstrained:
        result[tile] = sum(
            ways * math.comb(free - 1, split.remaining - count - 1)
            for count, ways in totals.items()
            if 0 < split.remaining - count <= free
        )
    return Solution(layout_count, result)


def layouts(board: Board) -> list[frozenset[Tile]]:
    """List every layout that fits the board, as the set of its hidden Dipster tiles."""
    split = _split(board)
    if split is None:
        return []
    group_options = [
        [[tiles[position] for position in chosen] for chosen in _assignments(tiles, constraints)]
        for tiles, constraints in split.groups
    ]
    result: list[frozenset[Tile]] = []

    def extend(index: int, picked: list[Tile]) -> None:
        if index == len(group_options):
            rest = split.remaining - len(picked)
            if 0 <= rest <= len(split.unconstrained):
                for extra in _combinations(split.unconstrained, rest):
                    result.append(frozenset(picked + extra))
            return
        for option in group_options[index]:
            if len(picked) + len(option) <= split.remaining:
                extend(index + 1, picked + option)

    extend(0, [])
    return result


def _combinations(tiles: list[Tile], count: int):
    if count == 0:
        yield []
        return
    for position in range(len(tiles) - count + 1):
        for rest in _combinations(tiles[position + 1 :], count - 1):
            yield [tiles[position], *rest]


def plan(board: Board, layout_list: list[frozenset[Tile]]) -> tuple[Fraction, Tile | None]:
    """Find the dig that keeps the expected token cost to finish the level lowest.

    Each fitting layout is taken as equally likely. A dig either finds a
    Dipster or shows a number, and each result narrows the layouts; once one
    layout is left, its remaining Dipsters are dug at their known cost. Returns
    the expected cost and the tile to dig, or no tile when one layout is left.
    """
    found = board.found
    # For each tile, which layouts give each result: -1 for a Dipster, else the number shown.
    splits: dict[Tile, dict[int, int]] = {}
    for tile in board.hidden:
        around = board.neighbors(tile)
        masks: dict[int, int] = {}
        for index, layout in enumerate(layout_list):
            result = -1 if tile in layout else sum(
                1 for other in around if other in layout or other in found
            )
            masks[result] = masks.get(result, 0) | (1 << index)
        if len(masks) > 1:
            splits[tile] = masks
    layout_costs = [sum(board.cost(tile) for tile in layout) for layout in layout_list]
    # Try likely Dipsters first so a good choice is found early and prunes the rest.
    order = sorted(
        splits,
        key=lambda tile: -splits[tile].get(-1, 0).bit_count() / board.cost(tile),
    )
    memo: dict[int, tuple[int, Tile | None]] = {}
    floors: dict[int, int] = {}

    def floor(mask: int) -> int:
        """The total over the mask's layouts of each one's cheapest finish."""
        if mask not in floors:
            total, rest = 0, mask
            while rest:
                low = rest & -rest
                total += layout_costs[low.bit_length() - 1]
                rest ^= low
            floors[mask] = total
        return floors[mask]

    # best(mask) is the total over the mask's layouts of the cost to finish,
    # counting every Dipster of each layout whether dug yet or not. Dipsters
    # already dug lie in every layout of the mask, so this differs from the real
    # remaining cost by a constant per layout, and a dig that finds a Dipster
    # costs nothing beyond what its layouts already count. Totals keep the
    # arithmetic in integers; dividing by the layout count gives the expectation.
    def best(mask: int) -> tuple[int, Tile | None]:
        if mask in memo:
            return memo[mask]
        if mask.bit_count() == 1:
            memo[mask] = (layout_costs[mask.bit_length() - 1], None)
            return memo[mask]
        choice: tuple[int, Tile | None] = (10**18, None)
        seen: set[tuple[int, tuple[tuple[int, bool], ...]]] = set()
        for tile in order:
            groups = [
                (result, group)
                for result, layouts_with in splits[tile].items()
                if (group := layouts_with & mask)
            ]
            if len(groups) < 2:
                # Learns nothing: a sure Dipster is dug at the end, a sure blank never.
                continue
            cost = board.cost(tile)
            # Tiles that split the layouts the same way, with the same part being a
            # Dipster, at the same cost are interchangeable.
            signature = (cost, tuple(sorted((group, result == -1) for result, group in groups)))
            if signature in seen:
                continue
            seen.add(signature)
            # Only a dig that shows a number is an extra cost.
            total = cost * sum(group.bit_count() for result, group in groups if result != -1)
            if total + sum(floor(group) for _, group in groups) >= choice[0]:
                continue
            for _, group in groups:
                total += best(group)[0]
                if total >= choice[0]:
                    break
            if total < choice[0]:
                choice = (total, tile)
        memo[mask] = choice
        return choice

    total, tile = best((1 << len(layout_list)) - 1)
    return Fraction(total, len(layout_list)), tile


@dataclass
class Advice:
    certain: list[Tile]
    tile: Tile | None
    chance: Fraction
    # Expected tokens to find every remaining Dipster, when the lookahead ran.
    expected: Fraction | None


def advise(board: Board, solution: Solution, lookahead_limit: int = 200) -> Advice:
    if board.dipsters == len(board.found):
        return Advice([], None, Fraction(0), Fraction(0))
    hidden = board.hidden
    certain = [tile for tile in hidden if solution.hits[tile] == solution.layouts]

    if solution.layouts <= lookahead_limit:
        expected, tile = plan(board, layouts(board))
        if tile is None:
            # One layout is left: dig its Dipsters, cheapest first.
            tile = min(certain, key=board.cost)
        return Advice(certain, tile, solution.chance(tile), expected)

    def open_neighbors(tile: Tile) -> int:
        return sum(
            1
            for other in board.neighbors(tile)
            if other not in board.known and 0 < solution.hits[other] < solution.layouts
        )

    tile = max(
        hidden,
        key=lambda tile: (solution.chance(tile) / board.cost(tile), open_neighbors(tile)),
    )
    return Advice(certain, tile, solution.chance(tile), None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count the Dipster layouts that fit every revealed number, print each "
            "hidden tile's chance of holding a Dipster, and suggest the next dig."
        )
    )
    parser.add_argument("--size", type=int, help="Rows and columns of a square board, e.g. 5")
    parser.add_argument("--rows", type=int, help="Rows of a non-square board")
    parser.add_argument("--columns", type=int, help="Columns of a non-square board")
    parser.add_argument("--dipsters", type=int, required=True, help="Total Dipsters on the board")
    parser.add_argument(
        "--rock",
        action="append",
        default=[],
        metavar="ROW,COLUMN[=DIGS]",
        help=(
            "A rock tile and the digs it still needs before a further dig reveals it "
            "(default 1). Repeat for each rock."
        ),
    )
    parser.add_argument(
        "--lookahead-limit",
        type=int,
        default=200,
        help=(
            "Plan the lowest expected token cost when at most this many layouts fit "
            "(default 200); above it, suggest the best chance per token"
        ),
    )
    parser.add_argument(
        "tiles",
        nargs="*",
        help="Revealed tiles as row,column=value, with value a number or D for a found Dipster",
    )
    args = parser.parse_args(argv)
    rows = args.rows or args.size
    columns = args.columns or args.size
    if not rows or not columns:
        parser.error("give --size, or both --rows and --columns")

    try:
        board = Board(
            rows,
            columns,
            args.dipsters,
            dict(parse_tile(text) for text in args.tiles),
            dict(parse_rock(text) for text in args.rock),
        )
    except ValueError as error:
        parser.error(str(error))

    solution = solve(board)
    if not solution.layouts:
        print("No layout fits these tiles; recheck the board.", file=sys.stderr)
        return 1

    print(f"Layouts: {solution.layouts}")
    for row in range(rows):
        cells = []
        for column in range(columns):
            tile = (row, column)
            value = board.known.get(tile)
            cells.append(f"{value:>4}" if value else f"{float(solution.chance(tile)):4.2f}")
        print(" ".join(cells))

    advice = advise(board, solution, args.lookahead_limit)
    if advice.tile is None:
        print("Every Dipster is found.")
        return 0
    if advice.certain:
        print("Certain Dipsters: " + ", ".join(tile_name(tile) for tile in advice.certain))
    cost = board.cost(advice.tile)
    detail = f"chance {float(advice.chance):.2f}, costs {cost} token{'s' if cost > 1 else ''}"
    if advice.expected is not None:
        detail += f"; about {float(advice.expected):.2f} tokens expected to finish"
    else:
        detail += "; best chance per token"
    print(f"Next dig: {tile_name(advice.tile)} ({detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
