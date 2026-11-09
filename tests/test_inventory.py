from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from msm_cognition.inventory import (
    GAME_ISLAND_ORDER,
    bed_usage,
    generate_document,
    inventory_index,
    is_breedable,
    island_sort_key,
    load_json,
    load_yaml,
    load_islands,
    planner_row,
)


class InventoryGeneratorTests(unittest.TestCase):
    def test_islands_follow_custom_order(self) -> None:
        names = [island["island"] for _, island in load_islands(REPO_ROOT)]
        known = [name for name in names if name in GAME_ISLAND_ORDER]
        self.assertEqual(sorted(known, key=GAME_ISLAND_ORDER.index), known)
        self.assertEqual(names[: len(known)], known)

    def test_unknown_island_sorts_after_game_islands(self) -> None:
        last = island_sort_key({"island": GAME_ISLAND_ORDER[-1]})
        self.assertLess(last, island_sort_key({"island": "Zzz Unlisted Island"}))

    def test_document_contains_both_islands_and_planners(self) -> None:
        document = generate_document(REPO_ROOT)
        self.assertIn("## Plant Island", document)
        self.assertIn("## Magical Sanctum", document)
        self.assertIn("### Castle", document)
        self.assertIn("### Unresolved discoveries", document)
        self.assertIn("| Rare | 4/19 | 1 |", document)
        self.assertIn("| Epic | 1/19 | 1 |", document)
        self.assertIn("Vegidian Castle | High |", document)
        self.assertIn(
            "| Paradise Castle | High | 86 | 90 | 4 | 2 | 88 | 90 | 90 | 4 |",
            document,
        )
        self.assertIn("### Rare breeding planner", document)
        self.assertIn("### Epic breeding planner", document)
        self.assertIn("| Monster | Variant | Class | Breedable? |", document)

    def test_every_inventory_row_has_one_breedability_classification(self) -> None:
        rules = load_json(
            REPO_ROOT / "reference/breeding/island-breedability.json"
        )["islands"]
        for path in (REPO_ROOT / "inventory/islands").glob("*.yaml"):
            island = load_yaml(path)
            island_rules = rules[island["island"]]
            for monster in island["monsters"]:
                result = is_breedable(
                    island_rules, monster["name"], monster["variant"]
                )
                self.assertIsInstance(result, bool)

    def test_breedability_is_variant_and_island_specific(self) -> None:
        rules = load_json(
            REPO_ROOT / "reference/breeding/island-breedability.json"
        )["islands"]
        plant = rules["Plant Island"]
        sanctum = rules["Magical Sanctum"]
        self.assertFalse(is_breedable(plant, "Potbelly", "common"))
        self.assertTrue(is_breedable(plant, "Potbelly", "rare"))
        self.assertTrue(is_breedable(plant, "Shrubb", "common"))
        self.assertFalse(is_breedable(plant, "Wubbox", "rare"))
        self.assertFalse(is_breedable(sanctum, "Theremind", "common"))
        self.assertTrue(is_breedable(sanctum, "Theremind", "rare"))

    def test_rare_parent_can_satisfy_epic_recipe(self) -> None:
        island = load_yaml(REPO_ROOT / "inventory/islands/plant-island.yaml")
        for monster in island["monsters"]:
            if monster["name"] == "Entbrat" and monster["variant"] == "common":
                monster["owned"] = 0
        index = inventory_index(island)
        row = planner_row(
            index,
            {"name": "G'joob", "parents": ["Entbrat", "Maw"], "time": "x"},
            "epic",
        )
        self.assertEqual("Ready", row[4])
        self.assertIn("Entbrat (Rare)", row[1])

    def test_plant_bed_usage_counts_known_owned_monsters(self) -> None:
        island = load_yaml(REPO_ROOT / "inventory/islands/plant-island.yaml")
        monster_beds = load_json(
            REPO_ROOT / "reference/monsters/bed-requirements.json"
        )
        usage = bed_usage(island, monster_beds)
        self.assertGreater(usage["used"], 0)
        self.assertEqual(usage["owned_beds"], usage["used"] + usage["checked_in_beds"])

    def test_owned_counts_are_never_nullable(self) -> None:
        for path in (REPO_ROOT / "inventory/islands").glob("*.yaml"):
            island = load_yaml(path)
            for monster in island["monsters"]:
                self.assertIsNotNone(
                    monster.get("owned"),
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )
                self.assertIsInstance(
                    monster["owned"],
                    int,
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )
                self.assertGreaterEqual(
                    monster["owned"],
                    0,
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )
                self.assertIsInstance(
                    monster.get("checked_in", 0),
                    int,
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )
                self.assertGreaterEqual(
                    monster.get("checked_in", 0),
                    0,
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )
                self.assertLessEqual(
                    monster.get("checked_in", 0),
                    monster["owned"],
                    f"{island['island']} {monster['variant']} {monster['name']}",
                )

    def test_low_confidence_zero_owned_discoveries_stay_unresolved(self) -> None:
        for path in (REPO_ROOT / "inventory/islands").glob("*.yaml"):
            island = load_yaml(path)
            for monster in island["monsters"]:
                with self.subTest(
                    island=island["island"],
                    variant=monster["variant"],
                    monster=monster["name"],
                ):
                    self.assertFalse(
                        monster.get("discovered")
                        and monster["owned"] == 0
                        and monster.get("confidence") in {"low", "medium"},
                        "Ambiguous zero-owned Book IDs belong in unresolved_discoveries",
                    )

    def test_rare_single_pattern_reports_missing_path(self) -> None:
        island = copy.deepcopy(
            load_yaml(REPO_ROOT / "inventory/islands/magical-sanctum.yaml")
        )
        candidates = ["G'day", "Larvaluss", "Frondley"]
        for monster in island["monsters"]:
            if monster["variant"] == "common" and monster["name"] in candidates:
                monster["owned"] = 1 if monster["name"] == "Frondley" else 0
        index = inventory_index(island)
        row = planner_row(
            index,
            {
                "name": "Theremind",
                "pattern": {
                    "kind": "two_distinct_triples",
                    "element": "Psychic",
                    "candidates": candidates,
                },
                "time": "8h",
            },
            "rare",
        )
        self.assertIn("Blocked", row[4])
        self.assertIn("Frondley", row[4])


if __name__ == "__main__":
    unittest.main()
