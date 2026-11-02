#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import sys


def parse_tile(text: str) -> tuple[tuple[int, int], str]:
    position, value = text.split("=")
    row, column = (int(part) for part in position.split(","))
    return (row, column), value.strip().upper()


def neighbors(row: int, column: int, rows: int, columns: int) -> list[tuple[int, int]]:
    return [
        (row + d_row, column + d_column)
        for d_row in (-1, 0, 1)
        for d_column in (-1, 0, 1)
        if (d_row or d_column)
        and 0 <= row + d_row < rows
        and 0 <= column + d_column < columns
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count the Dipster layouts that fit every revealed number and print "
            "each hidden tile's chance of holding a Dipster."
        )
    )
    parser.add_argument("--size", type=int, help="Rows and columns of a square board, e.g. 5")
    parser.add_argument("--rows", type=int, help="Rows of a non-square board")
    parser.add_argument("--columns", type=int, help="Columns of a non-square board")
    parser.add_argument("--dipsters", type=int, required=True, help="Total Dipsters on the board")
    parser.add_argument(
        "tiles",
        nargs="*",
        help="Revealed tiles as row,column=value, with value a number or D for a found Dipster",
    )
    args = parser.parse_args()
    rows = args.rows or args.size
    columns = args.columns or args.size
    if not rows or not columns:
        parser.error("give --size, or both --rows and --columns")

    known = dict(parse_tile(text) for text in args.tiles)
    found = [tile for tile, value in known.items() if value == "D"]
    numbers = {tile: int(value) for tile, value in known.items() if value != "D"}
    hidden = [
        (row, column)
        for row in range(rows)
        for column in range(columns)
        if (row, column) not in known
    ]

    layouts = 0
    hits = {tile: 0 for tile in hidden}
    for combo in itertools.combinations(hidden, args.dipsters - len(found)):
        dipsters = set(combo) | set(found)
        if all(
            sum(1 for tile in neighbors(*position, rows, columns) if tile in dipsters) == count
            for position, count in numbers.items()
        ):
            layouts += 1
            for tile in combo:
                hits[tile] += 1

    if not layouts:
        print("No layout fits these tiles; recheck the board.", file=sys.stderr)
        return 1

    print(f"Layouts: {layouts}")
    for row in range(rows):
        cells = []
        for column in range(columns):
            value = known.get((row, column))
            cells.append(f"{value:>4}" if value else f"{hits[(row, column)] / layouts:4.2f}")
        print(" ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
