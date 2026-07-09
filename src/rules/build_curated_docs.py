#!/usr/bin/env python3

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
DOCS_DIR = REPO_ROOT / "docs" / "data"


@dataclass
class IslandBlock:
	name: str
	rows: list[list[str]] = field(default_factory=list)


def clean_cell(value: str | None) -> str:
	if value is None:
		return ""

	return str(value).replace("\n", "<br>").strip()


def markdown_cell(value: str) -> str:
	value = value.replace("|", "\\|")
	return value if value else ""


def read_csv(path: Path) -> list[list[str]]:
	with path.open(newline="", encoding="utf-8-sig") as f:
		return list(csv.reader(f))


def parse_island_blocks(rows: list[list[str]]) -> list[IslandBlock]:
	"""
	Parse the Islands sheet's visual layout.

	The sheet contains repeated table regions:
	- left region:  columns B:H, represented here as indexes 1:8
	- right region: columns J:P, represented here as indexes 9:16

	Each region has the same logical columns:

	Island | Item | Structures | Cost to Upgrade | Currency to Upgrade | Current Capacity | Total Capacity
	"""

	blocks: list[IslandBlock] = []

	for start in (1, 9):
		current: IslandBlock | None = None

		for raw_row in rows:
			row = raw_row + [""] * 16
			region = [clean_cell(cell) for cell in row[start : start + 7]]

			first, item, structures, cost, currency, current_capacity, total_capacity = region

			if first == "Island" and item == "Item":
				continue

			if not any(region):
				continue

			if first and not any([item, structures, cost, currency, current_capacity, total_capacity]):
				current = IslandBlock(name=first)
				blocks.append(current)
				continue

			if current is None:
				continue

			if any([first, item, structures, cost, currency, current_capacity, total_capacity]):
				current.rows.append([
					first,
					item,
					structures,
					cost,
					currency,
					current_capacity,
					total_capacity,
				])

	return blocks


def render_table(headers: list[str], rows: list[list[str]]) -> str:
	lines = []
	lines.append("| " + " | ".join(headers) + " |")
	lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

	for row in rows:
		lines.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")

	return "\n".join(lines)


def render_islands_doc(blocks: list[IslandBlock]) -> str:
	out: list[str] = [
		"# Islands",
		"",
		"Curated island-status view generated from `data/raw/islands_msm.csv`.",
		"",
		"This page is organized for reading. It does not preserve the spreadsheet's side-by-side layout.",
		"",
	]

	headers = [
		"Notes",
		"Item",
		"Structures",
		"Cost to Upgrade",
		"Currency",
		"Current Capacity",
		"Total Capacity",
	]

	for block in blocks:
		out.append(f"## {block.name}")
		out.append("")

		if block.rows:
			out.append(render_table(headers, block.rows))
		else:
			out.append("_No rows captured._")

		out.append("")

	return "\n".join(out).rstrip() + "\n"


def main() -> None:
	DOCS_DIR.mkdir(parents=True, exist_ok=True)

	island_rows = read_csv(RAW_DIR / "islands_msm.csv")
	island_blocks = parse_island_blocks(island_rows)

	(DOCS_DIR / "islands.md").write_text(
		render_islands_doc(island_blocks),
		encoding="utf-8",
	)

	print(f"Wrote {DOCS_DIR / 'islands.md'}")
	print(f"Island blocks: {len(island_blocks)}")


if __name__ == "__main__":
	main()
