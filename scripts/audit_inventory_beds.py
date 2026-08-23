#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from msm_cognition.inventory import (  # noqa: E402
    bed_requirement,
    bed_usage,
    load_json,
    load_yaml,
    normalize_name,
)


ISLANDS_DIR = REPO_ROOT / "inventory/islands"
CASTLE_BEDS_PATH = REPO_ROOT / "reference/castles/bed-capacities.json"
MONSTER_BEDS_PATH = REPO_ROOT / "reference/monsters/bed-requirements.json"


def load_island(name: str) -> tuple[Path, dict[str, Any]]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(ISLANDS_DIR.glob("*.yaml")):
        island = load_yaml(path)
        if island.get("island") == name:
            matches.append((path, island))
    if not matches:
        known = ", ".join(
            load_yaml(path).get("island", path.stem)
            for path in sorted(ISLANDS_DIR.glob("*.yaml"))
        )
        raise SystemExit(f"Unknown island {name!r}. Known islands: {known}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple inventory files matched {name!r}")
    return matches[0]


def placed_delta(island: dict[str, Any], monster_beds: dict[str, Any]) -> int | None:
    castle = island.get("castle", {})
    if not isinstance(castle, dict) or castle.get("observed_beds_occupied") is None:
        return None
    return int(castle["observed_beds_occupied"]) - bed_usage(island, monster_beds)["used"]


def row_label(monster: dict[str, Any], beds: int) -> str:
    variant = str(monster["variant"]).title()
    checked_in = int(monster.get("checked_in", 0))
    suffix = f", checked in {checked_in}" if checked_in else ""
    return (
        f"{variant} {monster['name']} "
        f"(owned {monster.get('owned', 0)}, {beds} beds each{suffix})"
    )


def candidate_rows(
    island: dict[str, Any],
    monster_beds: dict[str, Any],
    *,
    include_zero_owned: bool,
    excludes: set[str],
) -> list[tuple[dict[str, Any], int]]:
    rows = []
    for monster in island.get("monsters", []):
        key = normalize_name(f"{monster.get('variant')} {monster.get('name')}")
        if key in excludes:
            continue
        owned = int(monster.get("owned", 0))
        if owned <= 0 and not (include_zero_owned and monster.get("discovered")):
            continue
        beds = bed_requirement(monster, monster_beds)
        if beds <= 0:
            continue
        rows.append((monster, beds))
    return rows


def correction_combinations(
    rows: list[tuple[dict[str, Any], int]], delta: int, max_changes: int
) -> list[list[tuple[dict[str, Any], int]]]:
    if delta <= 0:
        return []
    found: list[list[tuple[dict[str, Any], int]]] = []
    for change_count in range(1, max_changes + 1):
        for combo in itertools.combinations_with_replacement(rows, change_count):
            if sum(beds for _, beds in combo) == delta:
                found.append(list(combo))
        if found:
            return found
    return found


def print_audit(
    island_path: Path,
    island: dict[str, Any],
    castle_beds: dict[str, Any],
    monster_beds: dict[str, Any],
    *,
    include_zero_owned: bool,
    assume_panel_includes_hotels: bool,
    excludes: set[str],
    max_changes: int,
) -> None:
    castle = island.get("castle", {})
    usage = bed_usage(island, monster_beds)
    capacity = None
    if isinstance(castle, dict):
        capacity = castle_beds.get("capacities", {}).get(castle.get("name"))

    print(f"Island: {island['island']}")
    print(f"File: {island_path.relative_to(REPO_ROOT)}")
    if isinstance(castle, dict):
        print(f"Castle: {castle.get('name', 'unknown')}")
        if castle.get("observed_beds_occupied") is not None:
            print(
                "Panel: "
                f"{castle['observed_beds_occupied']}/"
                f"{castle.get('observed_beds_available', capacity or 'unknown')}"
            )
    print(f"Indexed Castle beds used: {usage['used']}")
    print(f"Checked-in Hotel beds: {usage['checked_in_beds']}")
    print(f"Total owned beds: {usage['owned_beds']}")

    delta = placed_delta(island, monster_beds)
    if (
        assume_panel_includes_hotels
        and isinstance(castle, dict)
        and castle.get("observed_beds_occupied") is not None
    ):
        delta = int(castle["observed_beds_occupied"]) - usage["owned_beds"]
    if delta is None:
        print("Bed audit delta: no castle panel value recorded")
        return

    if assume_panel_includes_hotels:
        print(f"Bed audit delta, treating Hotel occupants as panel-counted: {delta:+d}")
    else:
        print(f"Bed audit delta: {delta:+d}")
    if assume_panel_includes_hotels and usage["checked_in_beds"]:
        print("Note: this debug mode is not the normal Hotel accounting model.")

    if delta == 0:
        print("Status: reconciled")
        return
    if delta < 0:
        print("Status: indexed inventory exceeds the Castle panel; look for overcounts.")
        return

    rows = candidate_rows(
        island,
        monster_beds,
        include_zero_owned=include_zero_owned,
        excludes=excludes,
    )
    combos = correction_combinations(rows, delta, max_changes)
    if not combos:
        print(f"No +{delta} reconciliation found within {max_changes} count changes.")
        return

    print(f"Smallest +{delta} reconciliation candidates:")
    for combo in combos[:20]:
        print("- " + " + ".join(row_label(monster, beds) for monster, beds in combo))
    if len(combos) > 20:
        print(f"...and {len(combos) - 20} more")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit an island inventory against its Castle bed panel."
    )
    parser.add_argument("--island", required=True, help='Full island name, such as "Water Island".')
    parser.add_argument(
        "--include-zero-owned",
        action="store_true",
        help="Include discovered zero-owned rows as possible missing-count candidates.",
    )
    parser.add_argument(
        "--assume-panel-includes-hotels",
        action="store_true",
        help="Debug mode: compare the Castle panel to total owned beds instead of placed Castle beds.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="VARIANT NAME",
        help='Exclude a confirmed row from candidate output, such as "common Shellbeat".',
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        default=2,
        help="Maximum number of +1 count changes to combine when explaining a positive delta.",
    )
    args = parser.parse_args()

    island_path, island = load_island(args.island)
    castle_beds = load_json(CASTLE_BEDS_PATH)
    monster_beds = load_json(MONSTER_BEDS_PATH)
    print_audit(
        island_path,
        island,
        castle_beds,
        monster_beds,
        include_zero_owned=args.include_zero_owned,
        assume_panel_includes_hotels=args.assume_panel_includes_hotels,
        excludes={normalize_name(value) for value in args.exclude},
        max_changes=args.max_changes,
    )


if __name__ == "__main__":
    main()
