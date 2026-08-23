from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

import yaml


RECIPE_PATH = Path("reference/breeding/rare-epic-breeding.json")
BREEDABILITY_PATH = Path("reference/breeding/island-breedability.json")
CASTLE_BEDS_PATH = Path("reference/castles/bed-capacities.json")
MONSTER_BEDS_PATH = Path("reference/monsters/bed-requirements.json")
INVENTORY_DIRECTORY = Path("inventory/islands")
OUTPUT_PATH = Path("inventory/README.md")


def normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.replace("’", "'").replace("‘", "'"))
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(unaccented.strip().casefold().split())


def markdown(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {path}")
    return data


def inventory_index(island: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for monster in island.get("monsters", []):
        index.setdefault(normalize_name(monster["name"]), []).append(monster)
    return index


def owned_breedable_records(
    index: dict[str, list[dict[str, Any]]], name: str
) -> list[dict[str, Any]]:
    return [
        record
        for record in index.get(normalize_name(name), [])
        if (record.get("owned") or 0) > 0 and record.get("variant") != "epic"
    ]


def target_owned(
    index: dict[str, list[dict[str, Any]]], name: str, variant: str
) -> int:
    return sum(
        record.get("owned") or 0
        for record in index.get(normalize_name(name), [])
        if record.get("variant") == variant
    )


def is_breedable(
    island_breedability: dict[str, Any], name: str, variant: str
) -> bool:
    variant_rules = island_breedability.get(variant)
    if not isinstance(variant_rules, dict):
        raise ValueError(f"Missing breedability rules for variant {variant}")

    normalized = normalize_name(name)
    yes = {normalize_name(value) for value in variant_rules.get("breedable", [])}
    no = {normalize_name(value) for value in variant_rules.get("not_breedable", [])}
    classifications = int(normalized in yes) + int(normalized in no)
    if classifications != 1:
        raise ValueError(
            f"Expected exactly one breedability classification for {variant} {name}"
        )
    return normalized in yes


def parent_display(index: dict[str, list[dict[str, Any]]], name: str) -> str:
    records = owned_breedable_records(index, name)
    common = next((record for record in records if record.get("variant") == "common"), None)
    chosen = common or (records[0] if records else None)
    if not chosen:
        return name
    display = chosen.get("display_name", name)
    if chosen.get("variant") == "rare":
        return f"{display} (Rare)"
    return display


def explicit_plan(
    index: dict[str, list[dict[str, Any]]], parents: list[str]
) -> tuple[str, str]:
    combination = " + ".join(parent_display(index, parent) for parent in parents)
    missing = [parent for parent in parents if not owned_breedable_records(index, parent)]
    if not missing:
        return combination, "Ready"
    if len(missing) == 1:
        return combination, f"Blocked: missing {missing[0]}"
    return combination, f"Blocked: missing {', '.join(missing)}"


def pattern_plan(
    index: dict[str, list[dict[str, Any]]], pattern: dict[str, Any]
) -> tuple[str, str]:
    if pattern.get("kind") != "two_distinct_triples":
        raise ValueError(f"Unknown parent pattern: {pattern.get('kind')}")

    candidates = pattern["candidates"]
    owned = [name for name in candidates if owned_breedable_records(index, name)]
    element = pattern["element"]
    if len(owned) >= 2:
        pair = owned[:2]
        return " + ".join(parent_display(index, name) for name in pair), "Ready"

    generic = f"Any two distinct {element} triples"
    missing_candidates = [name for name in candidates if name not in owned]
    if len(owned) == 1:
        choices = " or ".join(missing_candidates)
        return generic, f"Blocked: pair {owned[0]} with {choices}"
    return generic, f"Blocked: need two of {', '.join(candidates)}"


def planner_row(
    index: dict[str, list[dict[str, Any]]], recipe: dict[str, Any], variant: str
) -> list[str]:
    name = recipe.get("display_name", recipe["name"])
    target = f"{variant.title()} {name}"
    owned = target_owned(index, recipe["name"], variant)

    if recipe.get("acquisition") == "not_breedable":
        combination = recipe["instruction"]
        plan = f"Owned ({owned})" if owned else "Not breedable"
        return [target, combination, "—", "—", plan, "Special acquisition"]

    if "parents" in recipe:
        combination, plan = explicit_plan(index, recipe["parents"])
    else:
        combination, plan = pattern_plan(index, recipe["pattern"])

    if owned:
        plan = f"Owned ({owned})"

    availability = "Seasonal offer" if recipe.get("seasonal") else "When offered"
    return [
        target,
        combination,
        recipe.get("time", "—"),
        recipe.get("enhanced_time", "—"),
        plan,
        availability,
    ]


def render_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(markdown(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(markdown(cell) for cell in row) + " |" for row in rows)
    return lines


def render_summary(island: dict[str, Any]) -> list[str]:
    rows: list[list[Any]] = []
    unresolved = island.get("unresolved_discoveries", {})
    for variant in ("common", "rare", "epic"):
        book = island.get("book", {}).get(variant, {})
        records = [m for m in island.get("monsters", []) if m.get("variant") == variant]
        owned_species = sum(1 for monster in records if (monster.get("owned") or 0) > 0)
        owned_monsters = sum(monster.get("owned") or 0 for monster in records)
        book_count = f"{book.get('discovered', '?')}/{book.get('total', '?')}"
        unresolved_count = "—"
        if isinstance(unresolved, dict):
            unresolved_entry = unresolved.get(variant, {})
            if isinstance(unresolved_entry, dict):
                unresolved_count = unresolved_entry.get("count", 0) or "—"
        rows.append(
            [variant.title(), book_count, unresolved_count, owned_species, owned_monsters]
        )
    return render_table(
        [
            "Variant",
            "Book discovered",
            "Unresolved Book IDs",
            "Owned species",
            "Owned monsters",
        ],
        rows,
    )


def render_unresolved_discoveries(island: dict[str, Any]) -> list[str]:
    unresolved = island.get("unresolved_discoveries", {})
    if not isinstance(unresolved, dict) or not unresolved:
        return ["None recorded."]
    rows = []
    for variant in ("common", "rare", "epic"):
        entry = unresolved.get(variant)
        if not isinstance(entry, dict) or not entry.get("count"):
            continue
        rows.append([variant.title(), entry["count"], entry.get("evidence", "—")])
    if not rows:
        return ["None recorded."]
    return render_table(["Variant", "Count", "Evidence"], rows)


def bed_requirement(monster: dict[str, Any], monster_beds: dict[str, Any]) -> int:
    name = normalize_name(monster["name"])
    variant = monster["variant"]
    monster_class = monster["class"]

    variant_overrides = monster_beds.get("variant_overrides", {}).get(variant, {})
    for override_name, beds in variant_overrides.items():
        if normalize_name(override_name) == name:
            return int(beds)

    for requirement_name, beds in monster_beds.get("requirements", {}).items():
        if normalize_name(requirement_name) == name:
            return int(beds)

    class_defaults = monster_beds.get("class_defaults", {})
    if monster_class in class_defaults:
        return int(class_defaults[monster_class])

    raise ValueError(
        f"Missing bed requirement for {variant} {monster['name']} ({monster_class})"
    )


def bed_usage(island: dict[str, Any], monster_beds: dict[str, Any]) -> dict[str, int]:
    owned_beds = 0
    checked_in_beds = 0
    for monster in island.get("monsters", []):
        owned = monster.get("owned")
        if owned is None:
            raise ValueError(
                f"{island['island']} has nullable owned count for "
                f"{monster['variant']} {monster['name']}"
            )
        checked_in = int(monster.get("checked_in", 0))
        if checked_in < 0:
            raise ValueError(
                f"{island['island']} has negative checked-in count for "
                f"{monster['variant']} {monster['name']}"
            )
        if checked_in > owned:
            raise ValueError(
                f"{island['island']} has checked-in count greater than owned count for "
                f"{monster['variant']} {monster['name']}"
            )
        if owned <= 0:
            continue
        beds = bed_requirement(monster, monster_beds)
        owned_beds += int(owned) * beds
        checked_in_beds += checked_in * beds
    return {
        "used": owned_beds - checked_in_beds,
        "owned_beds": owned_beds,
        "checked_in_beds": checked_in_beds,
    }


def render_castle(
    island: dict[str, Any], castle_beds: dict[str, Any], monster_beds: dict[str, Any]
) -> list[str]:
    castle = island.get("castle")
    if not isinstance(castle, dict):
        return ["None recorded."]
    capacity = castle_beds.get("capacities", {}).get(castle.get("name"))
    usage = bed_usage(island, monster_beds)
    rows = [[castle.get("name", "—"), castle.get("confidence", "—").title()]]
    headers = ["Current castle", "Confidence"]
    if capacity is not None:
        rows[0].extend(
            [
                usage["used"],
                capacity,
                int(capacity) - usage["used"],
                usage["checked_in_beds"],
                usage["owned_beds"],
            ]
        )
        headers.extend(
            [
                "Castle beds used",
                "Beds capacity",
                "Castle beds free",
                "Checked-in beds",
                "Total owned beds",
            ]
        )
    if castle.get("observed_beds_occupied") is not None:
        observed_occupied = int(castle["observed_beds_occupied"])
        observed_capacity = castle.get("observed_beds_available", capacity)
        rows[0].extend(
            [
                observed_occupied,
                observed_capacity,
                observed_occupied - usage["used"],
            ]
        )
        headers.extend(["Panel occupied", "Panel capacity", "Bed audit delta"])
    if castle.get("upgrade_target"):
        rows[0].append(castle["upgrade_target"])
        rows[0].append(castle.get("displayed_time_remaining", "—"))
        headers.extend(["Upgrade target", "Time remaining"])
    return render_table(headers, rows)


def render_inventory(
    island: dict[str, Any], island_breedability: dict[str, Any]
) -> list[str]:
    rows = []
    for monster in island.get("monsters", []):
        rows.append(
            [
                monster.get("display_name", monster["name"]),
                monster["variant"].title(),
                monster["class"].title(),
                "Yes"
                if is_breedable(island_breedability, monster["name"], monster["variant"])
                else "No",
                "Yes" if monster.get("discovered") else "No",
                monster.get("owned", 0),
                monster.get("checked_in", 0),
                monster.get("confidence", "—").title(),
            ]
        )
    return render_table(
        [
            "Monster",
            "Variant",
            "Class",
            "Breedable?",
            "Discovered",
            "Owned",
            "Checked in",
            "Confidence",
        ],
        rows,
    )


def render_pending(island: dict[str, Any]) -> list[str]:
    pending = island.get("pending", [])
    if not pending:
        return ["None recorded."]
    rows = []
    for item in pending:
        item_type = str(item.get("type", "—")).replace("_", " ").title()
        rows.append(
            [
                item_type,
                " + ".join(item.get("parents", [])) or "—",
                item.get("displayed_time")
                or item.get("displayed_time_remaining", "—"),
                item.get("predicted_result", "—"),
                item.get("confidence", "—").title(),
            ]
        )
    return render_table(["Type", "Parents", "Time", "Prediction", "Confidence"], rows)


def render_planner(
    island: dict[str, Any], island_recipes: dict[str, Any], variant: str
) -> list[str]:
    index = inventory_index(island)
    rows = [planner_row(index, recipe, variant) for recipe in island_recipes.get(variant, [])]
    if not rows:
        return ["No recipes recorded yet."]
    return render_table(
        [
            "Target",
            "Best first-copy combination / acquisition",
            "Standard",
            "Enhanced",
            "Plan",
            "Availability",
        ],
        rows,
    )


def island_sort_key(island: dict[str, Any]) -> tuple[int, str]:
    name = island["island"]
    return (0 if name == "Plant Island" else 1, name)


def generate_document(repo_root: Path) -> str:
    recipes = load_json(repo_root / RECIPE_PATH)
    breedability = load_json(repo_root / BREEDABILITY_PATH)
    castle_beds = load_json(repo_root / CASTLE_BEDS_PATH)
    monster_beds = load_json(repo_root / MONSTER_BEDS_PATH)
    islands = sorted(
        (load_yaml(path) for path in (repo_root / INVENTORY_DIRECTORY).glob("*.yaml")),
        key=island_sort_key,
    )

    lines = [
        "# Island inventory",
        "",
        "> Generated by `bin/inventory`. Edit `inventory/islands/*.yaml` or the breeding",
        "> reference data, then regenerate this file. See `inventory/SCHEMA.md`.",
        "",
        "Rare, Epic, and Seasonal recipes are planning references only: the target must",
        "also be available in the game. Parent readiness accepts owned Common or Rare",
        "parents because Rare variants may substitute for Common parents.",
        "",
    ]

    for island in islands:
        name = island["island"]
        island_recipes = recipes.get("islands", {}).get(name, {})
        island_breedability = breedability.get("islands", {}).get(name)
        if not isinstance(island_breedability, dict):
            raise ValueError(f"Missing island breedability data for {name}")
        lines.extend([f"## {name}", "", f"Observed: `{island.get('observed_at', 'unknown')}`", ""])
        lines.extend(["### Castle", ""])
        lines.extend(render_castle(island, castle_beds, monster_beds))
        lines.extend(["", "### Summary", ""])
        lines.extend(render_summary(island))
        lines.extend(["", "### Unresolved discoveries", ""])
        lines.extend(render_unresolved_discoveries(island))
        lines.extend(["", "### Current monsters", ""])
        lines.extend(render_inventory(island, island_breedability))
        lines.extend(["", "### Pending", ""])
        lines.extend(render_pending(island))
        lines.extend(["", "### Rare breeding planner", ""])
        lines.extend(render_planner(island, island_recipes, "rare"))
        lines.extend(["", "### Epic breeding planner", ""])
        lines.extend(render_planner(island, island_recipes, "epic"))
        if island.get("notes"):
            lines.extend(["", "### Notes", ""])
            lines.extend(f"- {markdown(note)}" for note in island["notes"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the player island inventory README.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stdout", action="store_true", help="Print instead of writing")
    mode.add_argument("--check", action="store_true", help="Fail if README is stale")
    args = parser.parse_args(argv)

    root = repo_root or Path(__file__).resolve().parents[2]
    document = generate_document(root)
    output = root / OUTPUT_PATH

    if args.stdout:
        print(document, end="")
        return 0
    if args.check:
        current = output.read_text(encoding="utf-8") if output.exists() else ""
        if current != document:
            print(f"Stale generated inventory: {output}")
            return 1
        print(f"Inventory is current: {output}")
        return 0

    output.write_text(document, encoding="utf-8")
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
