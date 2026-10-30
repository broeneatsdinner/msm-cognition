#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import sys


def parse_tile(text: str) -> tuple[tuple[int, int], str]:
    position, value = text.split("=")
    row, column = (int(part) for part in position.split(","))
    return (row, column), value.strip().upper()


def neighbors(row: int, column: int, size: int) -> list[tuple[int, int]]:
    return [
        (row + d_row, column + d_column)
        for d_row in (-1, 0, 1)
        for d_column in (-1, 0, 1)
        if (d_row or d_column)
        and 0 <= row + d_row < size
        and 0 <= column + d_column < size
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count the Dipster layouts that fit every revealed number and print "
            "each hidden tile's chance of holding a Dipster."
        )
    )
    parser.add_argument("--size", type=int, required=True, help="Board width, e.g. 5")
    parser.add_argument("--dipsters", type=int, required=True, help="Total Dipsters on the board")
    parser.add_argument(
        "tiles",
        nargs="*",
        help="Revealed tiles as row,column=value, with value a number or D for a found Dipster",
    )
    args = parser.parse_args()

    known = dict(parse_tile(text) for text in args.tiles)
    found = [tile for tile, value in known.items() if value == "D"]
    numbers = {tile: int(value) for tile, value in known.items() if value != "D"}
    hidden = [
        (row, column)
        for row in range(args.size)
        for column in range(args.size)
        if (row, column) not in known
    ]

    layouts = 0
    hits = {tile: 0 for tile in hidden}
    for combo in itertools.combinations(hidden, args.dipsters - len(found)):
        dipsters = set(combo) | set(found)
        if all(
            sum(1 for tile in neighbors(*position, args.size) if tile in dipsters) == count
            for position, count in numbers.items()
        ):
            layouts += 1
            for tile in combo:
                hits[tile] += 1

    if not layouts:
        print("No layout fits these tiles; recheck the board.", file=sys.stderr)
        return 1

    print(f"Layouts: {layouts}")
    for row in range(args.size):
        cells = []
        for column in range(args.size):
            value = known.get((row, column))
            cells.append(f"{value:>4}" if value else f"{hits[(row, column)] / layouts:4.2f}")
        print(" ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
