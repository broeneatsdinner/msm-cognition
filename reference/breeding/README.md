# Breeding Reference

This directory contains structured breeding-reference data for My Singing Monsters.

The purpose is to prevent the workbench from inferring breedability from monster
elements alone. Breedability is island-scoped:

```text
island -> available Book of Monsters -> valid parent pair -> possible child
```

## Data scope

- `common-natural-breeding.json` records source-listed best combinations for
  Common Natural monsters.
- `rare-epic-breeding.json` records island-scoped first-copy planning recipes
  for every Rare and Epic represented by the current Plant Island and Magical
  Sanctum inventories, including their Seasonal slots.
- `island-breedability.json` explicitly classifies every currently inventoried
  monster variant as breedable or not breedable on that island.
- `guaranteed-breeding-rules.json` records verified guarantees.
- `breeding-rules.md` explains the rule patterns and evidence boundaries.

The Rare/Epic data supports either an explicit parent pair or a constrained
parent pattern. Rare single-element monsters use the pattern “two distinct
triple-element monsters sharing the target element”; the inventory generator
selects an owned pair when possible.

Non-breedable targets such as Rare and Epic Wubbox are represented with an
acquisition instruction instead of a false breeding recipe.

Breedability is not the same as island obtainability. Market purchases, Dipster
Key placement, Werdo purchases, boxing, evolution, and teleport-only acquisition
can all place a monster on an island without making it breedable there.

## Planner behavior

`bin/inventory` joins the Rare/Epic reference to `inventory/islands/*.yaml` and
reports whether the player owns suitable parents. Common and Rare parents both
count; Epic monsters cannot breed.

Limited-time availability is intentionally not inferred from static data. The
generated README says `When offered` or `Seasonal offer`, and the player should
confirm the current in-game Market before attempting a recipe.

## Sources

The structured records were checked against the My Singing Monsters Wiki pages
for Breeding Combinations, Epic Breeding Combinations, Plant Island, Magical
Sanctum, and the individual special-monster pages linked from them.

## Core rule

Do not answer “can I breed X on island Y?” from elements alone. Answer from
island-scoped data.
