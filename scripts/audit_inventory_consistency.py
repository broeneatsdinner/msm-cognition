#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from msm_cognition.inventory import bed_usage, load_json, load_yaml  # noqa: E402


INVENTORY_DIR = REPO_ROOT / "inventory/islands"
PLAYER_MAP_PATH = REPO_ROOT / "reference/islands/player-map-2026-08-23.json"
MONSTER_BEDS_PATH = REPO_ROOT / "reference/monsters/bed-requirements.json"


def flatten_player_map(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    islands: dict[str, dict[str, Any]] = {}
    for page in data.get("pages", []):
        for island in page.get("islands", []):
            islands[island["name"]] = island | {"page": page.get("page")}
    return islands


def book_total(island: dict[str, Any]) -> tuple[int, int]:
    discovered = 0
    total = 0
    for values in island.get("book", {}).values():
        if not isinstance(values, dict):
            continue
        discovered += int(values.get("discovered", 0))
        total += int(values.get("total", 0))
        seasonal = values.get("seasonal", {})
        if isinstance(seasonal, dict):
            discovered += int(seasonal.get("discovered", 0))
            total += int(seasonal.get("total", 0))
    return discovered, total


def evidence_paths(island: dict[str, Any]) -> list[Path]:
    evidence = island.get("evidence", {})
    if not isinstance(evidence, dict):
        return []
    directory = evidence.get("screenshot_directory")
    if not directory:
        return []
    base = REPO_ROOT / directory
    paths: list[Path] = []
    for key, values in evidence.items():
        if key == "screenshot_directory" or not isinstance(values, list):
            continue
        paths.extend(base / value for value in values)
    return paths


def island_rows() -> list[tuple[Path, dict[str, Any]]]:
    return [
        (path, load_yaml(path))
        for path in sorted(INVENTORY_DIR.glob("*.yaml"))
    ]


def audit() -> str:
    player_map = flatten_player_map(PLAYER_MAP_PATH)
    monster_beds = load_json(MONSTER_BEDS_PATH)
    lines = [
        "# Inventory consistency audit",
        "",
        "Generated from local inventory YAML, player map snapshot, screenshot evidence paths, and bed reference data.",
        "",
        "## Summary",
        "",
    ]

    problems: list[str] = []
    islands = island_rows()
    for path, island in islands:
        name = island["island"]
        map_row = player_map.get(name)
        book_discovered, book_available = book_total(island)

        if map_row and "map_progress" in map_row:
            progress = map_row["map_progress"]
            if (
                int(progress["current"]) != book_discovered
                or int(progress["total"]) != book_available
            ):
                problems.append(
                    f"{name}: map progress {progress['current']}/{progress['total']} "
                    f"does not match Book+Seasonal {book_discovered}/{book_available}"
                )

        castle = island.get("castle", {})
        if isinstance(castle, dict) and castle.get("observed_beds_occupied") is not None:
            usage = bed_usage(island, monster_beds)
            delta = int(castle["observed_beds_occupied"]) - usage["used"]
            if delta:
                problems.append(f"{name}: Castle bed audit delta {delta:+d}")

        for monster in island.get("monsters", []):
            owned = monster.get("owned")
            checked_in = monster.get("checked_in", 0)
            label = f"{name} {monster.get('variant')} {monster.get('name')}"
            if not isinstance(owned, int) or owned < 0:
                problems.append(f"{label}: invalid owned value {owned!r}")
            if not isinstance(checked_in, int) or checked_in < 0:
                problems.append(f"{label}: invalid checked_in value {checked_in!r}")
            if isinstance(owned, int) and isinstance(checked_in, int) and checked_in > owned:
                problems.append(f"{label}: checked_in exceeds owned")

        missing = [p for p in evidence_paths(island) if not p.exists()]
        if missing:
            problems.append(f"{name}: {len(missing)} referenced screenshot(s) missing")

    if problems:
        lines.extend(f"- {problem}" for problem in problems)
    else:
        lines.append("- No consistency problems found.")

    lines.extend(["", "## Island Details", ""])
    for path, island in islands:
        name = island["island"]
        map_row = player_map.get(name)
        book_discovered, book_available = book_total(island)
        lines.extend([f"### {name}", ""])
        lines.append(f"- File: `{path.relative_to(REPO_ROOT)}`")
        if map_row:
            lines.append(f"- Player map order: `{map_row['order']}`")
            if "map_progress" in map_row:
                progress = map_row["map_progress"]
                lines.append(
                    f"- Map progress: `{progress['current']}/{progress['total']}` "
                    f"({progress['interpretation']}, {progress['confidence']} confidence)"
                )
        lines.append(f"- Book plus Seasonal total: `{book_discovered}/{book_available}`")

        castle = island.get("castle", {})
        if isinstance(castle, dict) and castle.get("observed_beds_occupied") is not None:
            usage = bed_usage(island, monster_beds)
            delta = int(castle["observed_beds_occupied"]) - usage["used"]
            lines.append(
                f"- Castle beds: indexed `{usage['used']}`, panel "
                f"`{castle['observed_beds_occupied']}/"
                f"{castle.get('observed_beds_available', 'unknown')}`, delta `{delta:+d}`"
            )
            if usage["checked_in_beds"]:
                hotel_delta = int(castle["observed_beds_occupied"]) - usage["owned_beds"]
                lines.append(
                    f"- Hotel alternate: total owned beds `{usage['owned_beds']}`, "
                    f"panel-minus-owned delta `{hotel_delta:+d}`"
                )

        low_confidence = [
            monster
            for monster in island.get("monsters", [])
            if monster.get("confidence") in {"low", "medium"}
        ]
        if low_confidence:
            labels = [
                f"{monster['variant']} {monster['name']} owned {monster['owned']}"
                for monster in low_confidence
            ]
            lines.append(f"- Low/medium confidence rows: {', '.join(labels)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit inventory consistency across islands.")
    parser.add_argument("--out", type=Path, help="Optional Markdown output path.")
    args = parser.parse_args()

    report = audit()
    if args.out:
        output = args.out if args.out.is_absolute() else REPO_ROOT / args.out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
