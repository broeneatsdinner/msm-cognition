#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "raw"


SheetRows = list[list[Any]]


def load_sheet_values(name: str, *, drop_blank_rows: bool = True) -> SheetRows:
	path = DATA_DIR / name

	with path.open(encoding="utf-8") as f:
		data = json.load(f)

	if not isinstance(data, dict):
		raise TypeError(f"{path} contained {type(data).__name__}, expected object")

	values = data.get("values")
	if not isinstance(values, list):
		raise TypeError(f"{path} did not contain a list at key 'values'")

	rows: SheetRows = []

	for row in values:
		if not isinstance(row, list):
			raise TypeError(f"{path} contained a non-list row: {row!r}")

		if drop_blank_rows and is_blank_row(row):
			continue

		rows.append(row)

	return rows


def is_blank_row(row: list[Any]) -> bool:
	return all(cell is None or str(cell).strip() == "" for cell in row)


def load_islands() -> SheetRows:
	return load_sheet_values("islands_msm.json")


def load_monsters() -> SheetRows:
	return load_sheet_values("monsters_msm.json")


def load_wublin_blueprints() -> SheetRows:
	return load_sheet_values("wublin_blueprints_msm.json")


def describe_sheet(label: str, rows: SheetRows) -> None:
	width = max((len(row) for row in rows), default=0)

	print(f"{label}:")
	print(f"  rows:    {len(rows)}")
	print(f"  columns: {width}")

	if rows:
		print(f"  first:   {rows[0]}")


def main() -> None:
	describe_sheet("Islands", load_islands())
	describe_sheet("Monsters", load_monsters())
	describe_sheet("Wublin blueprints", load_wublin_blueprints())


if __name__ == "__main__":
	main()
