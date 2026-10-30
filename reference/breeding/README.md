# Breeding

Rare Noggin - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;T-Rox + Clamble (6h)

Rare Noggin - **Air Island**  
&nbsp;&nbsp;&nbsp;&nbsp;T-Rox + PomPom (6h)

Rare Noggin - **Water Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Reedling + Scups (6h)

Rare Noggin - **Earth Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Reedling + Clamble (6h)

Rare Noggin - **Fire Haven**  
&nbsp;&nbsp;&nbsp;&nbsp;Reedling + Repatillo (6h)

Rare Noggin - **Faerie Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Cantorell + Bridg-it (6h)

Rare Noggin - **Bone Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Withur + Uuduk (6h)

Rare Noggin - **Mirror Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;T-Rox + Clamble (6h)

Rare Noggin - **Mirror Air Island**  
&nbsp;&nbsp;&nbsp;&nbsp;T-Rox + PomPom (6h)

Rare Noggin - **Mirror Water Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Reedling + Scups (6h)

Rare Noggin - **Mirror Earth Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Reedling + Clamble (6h)

Rare Noggin - **Mirror Faerie Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Cantorell + Bridg-it (6h)

Rare Noggin - **Mirror Bone Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Withur + Uuduk (6h)

Rare Drumpler - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Noggin + Mammott (1h 7m 30s)

Rare Maw - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Toe Jammer + Mammott (1h 7m 30s)

Rare Pummel - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Noggin + Oaktopus (15h 30m)

Rare Clamble - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Noggin + Furcorn (15h 30m)

Rare Bowgart - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Toe Jammer + Furcorn (15h 30m)

Rare Ghazt - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Entbrat + T-Rox (1d 21h 30m)

Rare G'joob - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Pummel + T-Rox (22h 30m)

Rare Punkleton - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Bowgart + T-Rox (1d 7h 45m)

Rare Wubbox - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Purchase from the StarShop, then box the required Rare Naturals; cannot be bred.

Vitreous Ti (Rare Ti) - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Cannot be bred; no breeding time.

Waxen La (Rare La) - **Plant Island**  
&nbsp;&nbsp;&nbsp;&nbsp;Cannot be bred; no breeding time.

Times in parentheses are successful breeding times in a normal Breeding
Structure, without an island skin boost; incubation is separate. Each
breedable Rare must be available in a breeding promotion. A StarShop offer
alone does not establish breeding availability. All parents listed here are
owned in the recorded inventory; their levels and current availability for
breeding have not been checked.

These first-copy combinations follow the breeding reference and favor short
retries where applicable; no verified success percentages are recorded. The
single + double combinations for Rare Pummel, Rare Clamble, and Rare Bowgart
allow quick Single-element failures. Entbrat + the corresponding Common
triple is another option for those three, but can also produce a Ghazt with
a longer wait. Rare Dipster acquisition offers still need to be checked in
game.

Sources: [Plant Island inventory](../../inventory/islands/plant-island.yaml),
[first-copy recipes and times](rare-epic-breeding.json),
[Rare breeding combinations](https://mysingingmonsters.fandom.com/wiki/Breeding_Combinations),
[Rare Clamble rules](https://mysingingmonsters.fandom.com/wiki/Rare_Clamble),
[Rare Ghazt](https://mysingingmonsters.fandom.com/wiki/Rare_Ghazt),
[Rare G'joob](https://mysingingmonsters.fandom.com/wiki/Rare_G%27joob),
[Rare Punkleton](https://mysingingmonsters.fandom.com/wiki/Rare_Punkleton),
[Rare Wubbox](https://mysingingmonsters.fandom.com/wiki/Rare_Wubbox),
and [island breedability classifications](island-breedability.json).

### Breeding Reference

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
~~~~
