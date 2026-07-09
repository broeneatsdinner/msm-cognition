#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "raw"


def load_json(name: str) -> list[dict[str, Any]]:
	path = DATA_DIR / name
	with path.open(encoding="utf-8") as f:
		data = json.load(f)

	if not isinstance(data, list):
		raise TypeError(f"{path} did not contain a JSON list")

	return data


def load_islands() -> list[dict[str, Any]]:
	return load_json("islands_msm.json")


def load_monsters() -> list[dict[str, Any]]:
	return load_json("monsters_msm.json")


def load_wublin_blueprints() -> list[dict[str, Any]]:
	return load_json("wublin_blueprints_msm.json")


def main() -> None:
	islands = load_islands()
	monsters = load_monsters()
	wublins = load_wublin_blueprints()

	print(f"Islands:           {len(islands)}")
	print(f"Monsters:          {len(monsters)}")
	print(f"Wublin blueprints: {len(wublins)}")


if __name__ == "__main__":
	main()
