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

A recipe may also record a preferred explicit `parents` pair alongside its
valid `pattern`; the inventory planner displays the explicit pair. Optional
`common_failure_outcomes` records Common parent failures and their breeding
times. These outcomes are reference metadata, not an exhaustive outcome list
or probability model.

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

## Plant Island: Rare Noggin

Preferred combination: **T-Rox + Clamble**. Both parents are owned in the
2026-10-29 Plant Island inventory. This recommendation favors shorter failed
attempts; no reliable per-pair success percentages have been established.

| Outcome | Normal Breeding Structure | Enhanced Breeding Structure |
| --- | --- | --- |
| **Rare Noggin (success)** | **6h** | 4h 30m |
| Common T-Rox (failure) | 8h | 6h |
| Common Clamble (failure) | 12h | 9h |

Times cover breeding only, before incubation, and exclude island skin boosts.
Rare Noggin then takes another 6h in a normal Nursery.

T-Rox + Clamble keeps the shorter T-Rox failure and avoids the possible G'joob
outcome from T-Rox + Pummel (18h normally). Pummel + Clamble has 12h Common
failures for either parent. See the [Rare Noggin breeding rules](https://mysingingmonsters.fandom.com/wiki/Rare_Noggin),
[T-Rox outcomes and times](https://mysingingmonsters.fandom.com/wiki/T-Rox),
[Clamble times](https://mysingingmonsters.fandom.com/wiki/Clamble), and
[Pummel times](https://mysingingmonsters.fandom.com/wiki/Pummel).

Rare Noggin must be available to breed. Other offered Rares can also occur:
in particular, Rare Mammott can result from T-Rox + Clamble with the same 6h
normal timer, so confirm the egg rather than identifying it by time alone.
The table lists the usual Common failures, not every event-dependent outcome.

The structured recipe and its source links are in
`rare-epic-breeding.json`; the generated Plant Island planner uses this
preferred pair.

## Sources

The structured records were checked against the My Singing Monsters Wiki pages
for Breeding Combinations, Epic Breeding Combinations, Plant Island, Magical
Sanctum, and the individual special-monster pages linked from them.

## Core rule

Do not answer “can I breed X on island Y?” from elements alone. Answer from
island-scoped data.
