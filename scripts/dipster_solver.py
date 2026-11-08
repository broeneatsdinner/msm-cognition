#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from fractions import Fraction


Tile = tuple[int, int]
Shape = tuple[int, int]

# Tile values besides a number: a found single Dipster, a flagged dirt mound
# (a dug square of a big Dipster not yet complete), and a square of a big
# Dipster already found.
DIPSTER, MOUND, BIG = "D", "M", "B"

# Big Dipster shapes tried when none is given: every rectangle up to 3x3.
ANY_SHAPES: tuple[Shape, ...] = ((1, 2), (2, 1), (1, 3), (3, 1), (2, 2), (2, 3), (3, 2), (3, 3))


def parse_tile(text: str) -> tuple[Tile, str]:
    position, value = text.split("=")
    row, column = (int(part) for part in position.split(","))
    return (row, column), value.strip().upper()


def parse_shapes(text: str) -> list[Shape]:
    """Parse "any" or a comma list of ROWSxCOLUMNS shapes, such as "2x2,3x3"."""
    if text.strip().lower() == "any":
        return list(ANY_SHAPES)
    shapes = []
    for part in text.split(","):
        rows, _, columns = part.strip().lower().partition("x")
        if not (rows.isdigit() and columns.isdigit()):
            raise ValueError(
                f"--big {text}: shapes look like 3x3; a bare --big must not come right before a tile"
            )
        shapes.append((int(rows), int(columns)))
    return shapes


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
    # Every Dipster on the board, big ones included, as the found bar counts them.
    dipsters: int
    known: dict[Tile, str] = field(default_factory=dict)
    # Digs a rock tile still needs before a further dig reveals it.
    rocks: dict[Tile, int] = field(default_factory=dict)
    # One entry per big Dipster: the shapes it may have.
    bigs: list[list[Shape]] = field(default_factory=list)

    def __post_init__(self) -> None:
        for tile, value in self.known.items():
            if not self.on_board(tile):
                raise ValueError(f"{tile_name(tile)} is off the board")
            if value not in (DIPSTER, MOUND, BIG) and not (value.isdigit() and int(value) <= 8):
                raise ValueError(f"{tile_name(tile)}={value} is not a number, D, M or B")
        for tile, digs in self.rocks.items():
            if not self.on_board(tile):
                raise ValueError(f"rock {tile_name(tile)} is off the board")
            if tile in self.known:
                raise ValueError(f"rock {tile_name(tile)} is also listed as revealed")
            if digs < 0:
                raise ValueError(f"rock {tile_name(tile)} needs a dig count of 0 or more")
        if len(self.bigs) > self.dipsters:
            raise ValueError("more big Dipsters than Dipsters")
        for shapes in self.bigs:
            if not shapes:
                raise ValueError("a big Dipster needs at least one shape")
            for height, width in shapes:
                if height < 1 or width < 1 or height * width < 2:
                    raise ValueError(f"{height}x{width} is not a big Dipster shape")

    def on_board(self, tile: Tile) -> bool:
        return 0 <= tile[0] < self.rows and 0 <= tile[1] < self.columns

    def neighbors(self, tile: Tile) -> list[Tile]:
        return neighbors(*tile, self.rows, self.columns)

    @property
    def found(self) -> set[Tile]:
        """Found single Dipsters."""
        return {tile for tile, value in self.known.items() if value == DIPSTER}

    @property
    def numbers(self) -> dict[Tile, int]:
        return {tile: int(value) for tile, value in self.known.items() if value.isdigit()}

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


def _placements(board: Board, shapes: list[Shape]) -> list[frozenset[Tile]]:
    """Every spot a big Dipster of one of these shapes could fill on the board.

    It cannot cover a number or a single Dipster. A spot with any B square is
    a found big Dipster, so all its squares must be B. Otherwise it must still
    have an undug square: were all its squares mounds, it would be found.
    """
    result = []
    for height, width in dict.fromkeys(shapes):
        for top in range(board.rows - height + 1):
            for left in range(board.columns - width + 1):
                squares = frozenset(
                    (top + row, left + column) for row in range(height) for column in range(width)
                )
                marks = [board.known.get(tile) for tile in squares]
                if any(mark not in (None, MOUND, BIG) for mark in marks):
                    continue
                if BIG in marks:
                    if all(mark == BIG for mark in marks):
                        result.append(squares)
                elif None in marks:
                    result.append(squares)
    return result


def _big_combos(board: Board) -> list[tuple[frozenset[Tile], ...]]:
    """Every way to place all the big Dipsters, apart from each other, covering every M and B."""
    options = [_placements(board, shapes) for shapes in board.bigs]
    marked = {tile for tile, value in board.known.items() if value in (MOUND, BIG)}
    seen: set[frozenset[frozenset[Tile]]] = set()
    result = []

    def extend(index: int, picked: list[frozenset[Tile]], used: frozenset[Tile]) -> None:
        if index == len(options):
            key = frozenset(picked)
            if marked <= used and key not in seen:
                seen.add(key)
                result.append(tuple(picked))
            return
        for squares in options[index]:
            if not squares & used:
                extend(index + 1, picked + [squares], used | squares)

    extend(0, [], frozenset())
    return result


def _singles_board(board: Board, combo: tuple[frozenset[Tile], ...]) -> Board | None:
    """The board left for the single Dipsters once the big ones sit at these spots.

    A number counts a big Dipster once however many of its squares it
    touches, so each number drops by the big Dipsters next to it. Their
    squares are blocked as B.
    """
    singles = board.dipsters - len(combo)
    if singles < 0:
        return None
    squares = frozenset().union(*combo)
    known: dict[Tile, str] = {}
    for tile, value in board.known.items():
        if value == DIPSTER:
            known[tile] = value
        elif value.isdigit():
            around = board.neighbors(tile)
            left = int(value) - sum(1 for big in combo if any(other in big for other in around))
            if left < 0:
                return None
            known[tile] = str(left)
    for tile in squares:
        known[tile] = BIG
    rocks = {tile: digs for tile, digs in board.rocks.items() if tile not in squares}
    return Board(board.rows, board.columns, singles, known, rocks)


def solve(board: Board) -> Solution:
    """Count every Dipster layout that fits the board, and how many put one on each tile.

    A tile's hits count a single Dipster or an undug square of a big one. With
    big Dipsters, each way to place them is solved for the singles in turn,
    and every fitting layout counts once.
    """
    if not board.bigs:
        return _solve_singles(board)
    layout_count = 0
    hits = {tile: 0 for tile in board.hidden}
    for combo in _big_combos(board):
        singles_board = _singles_board(board, combo)
        if singles_board is None:
            continue
        solution = _solve_singles(singles_board)
        if not solution.layouts:
            continue
        layout_count += solution.layouts
        for tile, tile_hits in solution.hits.items():
            hits[tile] += tile_hits
        for squares in combo:
            for tile in squares:
                if tile in hits:
                    hits[tile] += solution.layouts
    if not layout_count:
        return Solution(0, {})
    return Solution(layout_count, hits)


def _solve_singles(board: Board) -> Solution:
    """Count the layouts of single Dipsters only.

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


@dataclass(frozen=True)
class Layout:
    """One way the hidden Dipsters could lie.

    `tiles` holds every hidden tile with a Dipster on it: single Dipsters and
    the undug squares of big ones. `bigs` holds every square of each big
    Dipster, dug or not.
    """

    tiles: frozenset[Tile]
    bigs: tuple[frozenset[Tile], ...] = ()

    def __contains__(self, tile: object) -> bool:
        return tile in self.tiles

    def __iter__(self):
        return iter(self.tiles)

    def __len__(self) -> int:
        return len(self.tiles)

    def __sub__(self, other: frozenset[Tile]) -> frozenset[Tile]:
        return self.tiles - other

    def shows(self, board: Board, tile: Tile) -> int:
        """What digging the tile would show: -1 a single Dipster, -2 a big Dipster's square, else the number."""
        if tile in self.tiles:
            return -2 if any(tile in big for big in self.bigs) else -1
        around = board.neighbors(tile)
        singles = sum(
            1
            for other in around
            if other in board.found
            or (other in self.tiles and not any(other in big for big in self.bigs))
        )
        return singles + sum(1 for big in self.bigs if any(other in big for other in around))


def layouts(board: Board) -> list[Layout]:
    """List every layout that fits the board."""
    if not board.bigs:
        return [Layout(tiles) for tiles in _singles_layouts(board)]
    result = []
    hidden = set(board.hidden)
    for combo in _big_combos(board):
        singles_board = _singles_board(board, combo)
        if singles_board is None:
            continue
        undug = frozenset(tile for squares in combo for tile in squares if tile in hidden)
        for tiles in _singles_layouts(singles_board):
            result.append(Layout(tiles | undug, combo))
    return result


def _singles_layouts(board: Board) -> list[frozenset[Tile]]:
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


def plan(board: Board, layout_list: list[Layout]) -> tuple[Fraction, Tile | None]:
    """Find the dig that keeps the expected token cost to finish the level lowest.

    Each fitting layout is taken as equally likely. A dig finds a single
    Dipster, finds a big Dipster's square (a flagged mound), or shows a number,
    and each result narrows the layouts; once one layout is left, its remaining
    Dipster squares are dug at their known cost. Returns the expected cost and
    the tile to dig, or no tile when one layout is left.
    """
    # For each tile, which layouts give each result (see Layout.shows).
    splits: dict[Tile, dict[int, int]] = {}
    for tile in board.hidden:
        masks: dict[int, int] = {}
        for index, layout in enumerate(layout_list):
            result = layout.shows(board, tile)
            masks[result] = masks.get(result, 0) | (1 << index)
        if len(masks) > 1:
            splits[tile] = masks
    layout_costs = [sum(board.cost(tile) for tile in layout) for layout in layout_list]
    # Try likely Dipsters first so a good choice is found early and prunes the rest.
    order = sorted(
        splits,
        key=lambda tile: -(splits[tile].get(-1, 0) | splits[tile].get(-2, 0)).bit_count()
        / board.cost(tile),
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
            signature = (cost, tuple(sorted((group, result < 0) for result, group in groups)))
            if signature in seen:
                continue
            seen.add(signature)
            # Only a dig that shows a number is an extra cost.
            total = cost * sum(group.bit_count() for result, group in groups if result >= 0)
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
    if not any(solution.hits.values()):
        # No hidden tile holds a Dipster or an undug big Dipster square.
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
        "--big",
        action="append",
        default=[],
        nargs="?",
        const="any",
        metavar="SHAPES",
        help=(
            "One big Dipster, counted in --dipsters, with its possible shapes as "
            "ROWSxCOLUMNS, comma separated (default any: every rectangle up to 3x3). "
            "Repeat for each big Dipster."
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
        help=(
            "Revealed tiles as row,column=value: a number, D for a found Dipster, "
            "M for a flagged mound (a dug square of an unfinished big Dipster), "
            "or B for a square of a found big Dipster"
        ),
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
            [parse_shapes(text) for text in args.big],
        )
    except ValueError as error:
        parser.error(str(error))
    if not board.bigs and any(value in (MOUND, BIG) for value in board.known.values()):
        parser.error("M and B tiles need --big")

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
