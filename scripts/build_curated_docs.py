#!/usr/bin/env python3

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = REPO_ROOT / "reference"
ISLANDS_DIR = REFERENCE_DIR / "islands"


@dataclass
class IslandBlock:
	name: str
	rows: list[list[str]] = field(default_factory=list)


def clean_cell(value: str | None) -> str:
	if value is None:
		return ""

	return str(value).replace("\n", " ").strip()


def markdown_cell(value: str) -> str:
	value = value.replace("|", "\\|")
	return value if value else "—"


def format_number(value: str) -> str:
	clean = value.strip()

	if not clean:
		return ""

	negative = clean.startswith("-")
	digits = clean[1:] if negative else clean

	if digits.isdigit():
		return f"{int(digits):,}"

	return clean


def format_cost(cost: str, currency: str) -> str:
	cost = cost.strip()
	currency = currency.strip()

	if not cost and not currency:
		return ""

	if cost.startswith("-") and cost[1:].isdigit():
		cost = format_number(cost)

	return " ".join(part for part in [cost, currency] if part)


def display_field_name(item: str, occurrence: int) -> str:
	if item == "Breeding Structure" and occurrence == 2:
		return "Bonus Breeding Structure"

	if item == "Nursery" and occurrence == 2:
		return "Bonus Nursery"

	if occurrence > 1:
		return f"{item} {occurrence}"

	return item


def read_csv(path: Path) -> list[list[str]]:
	with path.open(newline="", encoding="utf-8-sig") as f:
		return list(csv.reader(f))


def parse_island_blocks(rows: list[list[str]]) -> list[IslandBlock]:
	"""
	Parse the Islands sheet's visual layout.

	The sheet contains repeated table regions:
	- left region:  columns B:H, represented here as indexes 1:8
	- right region: columns J:P, represented here as indexes 9:16
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

			# Island heading row.
			if first and not any([item, structures, cost, currency, current_capacity, total_capacity]):
				current = IslandBlock(name=first)
				blocks.append(current)
				continue

			if current is None:
				continue

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


def render_key_value_table(rows: list[tuple[str, str]]) -> str:
	lines = [
		"| Field | Value |",
		"|---|---|",
	]

	for key, value in rows:
		lines.append(f"| {markdown_cell(key)} | {markdown_cell(value)} |")

	return "\n".join(lines)


def summarize_island(block: IslandBlock) -> list[tuple[str, str]]:
	summary: list[tuple[str, str]] = []
	notes: list[str] = []
	field_counts: dict[str, int] = {}

	for note, item, structures, cost, currency, current_capacity, total_capacity in block.rows:
		if note and not item:
			notes.append(note)
			continue

		if not item:
			continue

		value_parts: list[str] = []

		if structures:
			value_parts.append(structures)

		if current_capacity or total_capacity:
			value_parts.append(f"{format_number(current_capacity) or '—'} / {format_number(total_capacity) or '—'}")

		cost_text = format_cost(cost, currency)
		if cost_text:
			value_parts.append(f"upgrade: {cost_text}")

		# Drop empty placeholder rows from the curated human page.
		if not value_parts:
			continue

		field_counts[item] = field_counts.get(item, 0) + 1
		field_name = display_field_name(item, field_counts[item])

		value = "; ".join(value_parts)
		summary.append((field_name, value))

	if notes:
		summary.append(("Notes", "; ".join(notes)))

	return summary


def render_islands_doc(blocks: list[IslandBlock]) -> str:
	out: list[str] = [
		"# Islands",
		"",
		"Curated island-status view generated from `reference/islands/islands.csv`.",
		"",
		"This page is organized as one compact status card per island. It is meant for quick reading, not for preserving the original spreadsheet layout.",
		"",
		"## At a glance",
		"",
		"| Island | Rows captured |",
		"|---|---:|",
	]

	for block in blocks:
		out.append(f"| [{markdown_cell(block.name)}](#{slugify(block.name)}) | {len(summarize_island(block))} |")

	out.append("")

	for block in blocks:
		out.append(f"## {block.name}")
		out.append("")

		summary = summarize_island(block)

		if summary:
			out.append(render_key_value_table(summary))
		else:
			out.append("_No rows captured._")

		out.append("")

	return "\n".join(out).rstrip() + "\n"


def slugify(value: str) -> str:
	return (
		value.lower()
		.replace("&", "")
		.replace("'", "")
		.replace("/", "")
		.replace(" ", "-")
	)


def main() -> None:
	ISLANDS_DIR.mkdir(parents=True, exist_ok=True)

	island_rows = read_csv(ISLANDS_DIR / "islands.csv")
	island_blocks = parse_island_blocks(island_rows)

	(ISLANDS_DIR / "islands.md").write_text(
		render_islands_doc(island_blocks),
		encoding="utf-8",
	)

	print(f"Wrote {ISLANDS_DIR / 'islands.md'}")
	print(f"Island blocks: {len(island_blocks)}")


if __name__ == "__main__":
	main()
