#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "reference" / "breeding" / "common-natural-breeding.json"


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).lower()


def load_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_island(data: dict, island: str) -> tuple[str, str | None]:
    aliases = data.get("mirror_aliases", {})
    normalized = normalize_name(island)

    for alias, original in aliases.items():
        if normalize_name(alias) == normalized:
            return original, alias

    return island, None


def find_monster(data: dict, monster: str) -> tuple[str, dict] | None:
    normalized = normalize_name(monster)

    for name, record in data.get("monsters", {}).items():
        if normalize_name(name) == normalized:
            return name, record

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up island-scoped MSM breeding data."
    )
    parser.add_argument("--monster", required=True, help="Monster to look up")
    parser.add_argument("--island", help="Optional island to test")
    args = parser.parse_args()

    data = load_data()
    found = find_monster(data, args.monster)

    if not found:
        print(f"Unknown monster in current breeding data: {args.monster}")
        return 1

    monster_name, record = found
    parents = " + ".join(record["parents"])

    print(f"{monster_name}")
    print(f"  best parents:   {parents}")
    print(f"  time:           {record['time']}")
    print(f"  enhanced time:  {record['enhanced_time']}")
    print(f"  listed islands: {', '.join(record['islands'])}")

    if args.island:
        canonical, alias = canonical_island(data, args.island)
        valid = any(
            normalize_name(island) == normalize_name(canonical)
            for island in record["islands"]
        )

        if alias:
            print(f"  island alias:   {alias} -> {canonical}")

        if valid:
            print(f"  result:         YES, {monster_name} is listed for {args.island}.")
            return 0

        print(f"  result:         NO, {monster_name} is not listed for {args.island}.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
