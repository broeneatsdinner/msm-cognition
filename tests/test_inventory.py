from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from msm_cognition.inventory import generate_document, inventory_index, load_yaml, planner_row


class InventoryGeneratorTests(unittest.TestCase):
    def test_document_contains_both_islands_and_planners(self) -> None:
        document = generate_document(REPO_ROOT)
        self.assertIn("## Plant Island", document)
        self.assertIn("## Magical Sanctum", document)
        self.assertIn("### Rare breeding planner", document)
        self.assertIn("### Epic breeding planner", document)

    def test_rare_parent_can_satisfy_epic_recipe(self) -> None:
        island = load_yaml(REPO_ROOT / "inventory/islands/plant-island.yaml")
        index = inventory_index(island)
        row = planner_row(
            index,
            {"name": "G'joob", "parents": ["Entbrat", "Maw"], "time": "x"},
            "epic",
        )
        self.assertEqual("Ready", row[4])
        self.assertIn("Entbrat (Rare)", row[1])

    def test_rare_single_pattern_reports_missing_path(self) -> None:
        island = load_yaml(REPO_ROOT / "inventory/islands/magical-sanctum.yaml")
        index = inventory_index(island)
        row = planner_row(
            index,
            {
                "name": "Theremind",
                "pattern": {
                    "kind": "two_distinct_triples",
                    "element": "Psychic",
                    "candidates": ["G'day", "Larvaluss", "Frondley"],
                },
                "time": "8h",
            },
            "rare",
        )
        self.assertIn("Blocked", row[4])
        self.assertIn("Frondley", row[4])


if __name__ == "__main__":
    unittest.main()
