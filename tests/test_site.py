from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml

from msm_cognition.inventory import generate_outputs, write_outputs
from msm_cognition.site.edits import EditError, plan_edit
from msm_cognition.site.render import render_markdown

PAGE = "inventory/islands/plant-island.md"


class SiteEditTests(unittest.TestCase):
    def setUp(self) -> None:
        # Work on a copy, so the tests never touch the real inventory.
        self.tmp = Path(tempfile.mkdtemp())
        for rel in ("inventory", "reference/breeding", "reference/castles", "reference/monsters"):
            shutil.copytree(REPO_ROOT / rel, self.tmp / rel)
        write_outputs(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def line_of(self, text: str, start_heading: str = "### Rare") -> tuple[int, str]:
        lines = (self.tmp / PAGE).read_text(encoding="utf-8").split("\n")
        start = lines.index(start_heading)
        for index in range(start, len(lines)):
            if lines[index].startswith(f"- [") and lines[index][6:].split(" (")[0].split(" x")[0] == text:
                return index + 1, lines[index]
        raise AssertionError(f"{text} not found")

    def apply(self, name: str, action: str) -> str:
        line_no, line = self.line_of(name)
        edit = plan_edit(self.tmp, PAGE, line_no, line, action)
        edit.path.write_text(edit.text, encoding="utf-8")
        write_outputs(self.tmp)
        return edit.message

    def row(self, name: str, variant: str = "rare") -> dict:
        island = yaml.safe_load((self.tmp / "inventory/islands/plant-island.yaml").read_text())
        return next(m for m in island["monsters"] if m["name"] == name and m["variant"] == variant)

    def book_count(self) -> int:
        island = yaml.safe_load((self.tmp / "inventory/islands/plant-island.yaml").read_text())
        return island["book"]["rare"]["discovered"]

    def test_checking_a_new_rare_marks_it_discovered_and_counts_the_book(self) -> None:
        island = yaml.safe_load((self.tmp / "inventory/islands/plant-island.yaml").read_text())
        name = next(
            m["name"] for m in island["monsters"]
            if m["variant"] == "rare" and m["class"] == "natural" and not m["discovered"]
        )
        before = self.book_count()
        message = self.apply(name, "check")
        self.assertEqual(f"Mark Rare {name} owned on Plant Island", message)
        self.assertEqual({"owned": 1, "discovered": True}, {k: self.row(name)[k] for k in ("owned", "discovered")})
        self.assertEqual(before + 1, self.book_count())
        self.assertIn(f"- [x] {name}", (self.tmp / PAGE).read_text())

    def test_counts_go_up_and_down_but_uncheck_stops_above_one(self) -> None:
        before = self.row("Entbrat")["owned"]
        self.apply("Entbrat", "increment")
        self.apply("Entbrat", "increment")
        self.assertEqual(before + 2, self.row("Entbrat")["owned"])
        with self.assertRaises(EditError):
            self.apply("Entbrat", "uncheck")
        self.apply("Entbrat", "decrement")
        self.assertEqual(before + 1, self.row("Entbrat")["owned"])

    def test_a_click_settles_a_less_certain_count(self) -> None:
        self.apply("Wubbox", "uncheck")
        self.assertNotIn("confidence", self.row("Wubbox"))
        self.assertEqual(0, self.row("Wubbox")["owned"])

    def test_a_stale_page_changes_nothing(self) -> None:
        line_no, line = self.line_of("Potbelly")
        before = (self.tmp / "inventory/islands/plant-island.yaml").read_text()
        with self.assertRaises(EditError):
            plan_edit(self.tmp, PAGE, line_no, line + " x9", "uncheck")
        self.assertEqual(before, (self.tmp / "inventory/islands/plant-island.yaml").read_text())

    def test_plain_markdown_flips_the_box(self) -> None:
        note = self.tmp / "note.md"
        note.write_text("# Note\n\n- [ ] First\n- [x] Second\n", encoding="utf-8")
        edit = plan_edit(self.tmp, "note.md", 3, "- [ ] First", "check")
        self.assertEqual("# Note\n\n- [x] First\n- [x] Second\n", edit.text)
        with self.assertRaises(EditError):
            plan_edit(self.tmp, "note.md", 4, "- [x] Second", "increment")

    def test_generated_pages_round_trip(self) -> None:
        for rel, document in generate_outputs(self.tmp).items():
            self.assertEqual(document, (self.tmp / rel).read_text(encoding="utf-8"), rel)


class RenderTests(unittest.TestCase):
    def test_task_items_carry_their_path_and_line(self) -> None:
        page = render_markdown(REPO_ROOT, "x.md", "# T\n\n- [ ] One\n- [x] Two\n")
        self.assertIn('data-path="x.md" data-line="3" data-text="- [ ] One">', page)
        self.assertIn('data-line="4" data-text="- [x] Two" checked>', page)

    def test_code_spans_naming_repo_files_link_to_them(self) -> None:
        page = render_markdown(REPO_ROOT, "README.md", "See `inventory/SCHEMA.md` and `nope.md`.")
        self.assertIn('<a href="/inventory/SCHEMA.md"><code>inventory/SCHEMA.md</code></a>', page)
        self.assertIn("<code>nope.md</code>", page)


if __name__ == "__main__":
    unittest.main()
