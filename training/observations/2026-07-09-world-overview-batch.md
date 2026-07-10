# World Overview Screenshot Batch

## Screenshot batch

This observation records a 21-image My Singing Monsters world overview batch from 2026-07-09.

The batch contains:

- 18 island overview screenshots
- 3 map / island inventory screenshots

## Screenshot files

```text
training/screenshots/2026-07-09-world-overview-plant-island.png
training/screenshots/2026-07-09-world-overview-cold-island.png
training/screenshots/2026-07-09-world-overview-mirror-plant-island.png
training/screenshots/2026-07-09-world-overview-mirror-cold-island.png
training/screenshots/2026-07-09-world-overview-air-island.png
training/screenshots/2026-07-09-world-overview-water-island.png
training/screenshots/2026-07-09-world-overview-earth-island.png
training/screenshots/2026-07-09-world-overview-shugabush-island.png
training/screenshots/2026-07-09-world-overview-ethereal-island.png
training/screenshots/2026-07-09-world-overview-ethereal-workshop.png
training/screenshots/2026-07-09-world-overview-magical-sanctum.png
training/screenshots/2026-07-09-world-overview-fire-haven.png
training/screenshots/2026-07-09-world-overview-fire-oasis.png
training/screenshots/2026-07-09-world-overview-mythical-island.png
training/screenshots/2026-07-09-world-overview-light-island.png
training/screenshots/2026-07-09-world-overview-psychic-island.png
training/screenshots/2026-07-09-world-overview-faerie-island.png
training/screenshots/2026-07-09-world-overview-bone-island.png
training/screenshots/2026-07-09-world-overview-map-inventory-1-of-3.png
training/screenshots/2026-07-09-world-overview-map-inventory-2-of-3.png
training/screenshots/2026-07-09-world-overview-map-inventory-3-of-3.png
```

## User context

The user provided this batch while auditing whether required eggs were already started on existing islands.

Immediate egg targets:

```yaml
needed_eggs:
  Congle: 2
  Drumpler: 2
  Maw: 1
  Pango: 1
```

The user described the batch as:

> Here are the islands, along with 3 images of the island inventories in order

The user later placed the local image set under:

```text
msm-worlds-2026-07-09/
```

and then copied the images into `training/screenshots/` using normalized training filenames.

## Observed account state

Common visible UI state across the batch:

```yaml
account:
  level: 28
  diamonds: 8
  treats: 105448
  top_left_meter: "64/325"
  top_left_timer: "1d 15h"
  top_left_meter_classification: visible_but_unmodeled
```

Coins vary by island screenshot because coin totals changed while navigating and collecting.

## Map inventory counts

These counts were read from the three map / island inventory screenshots.

```yaml
island_inventory_counts:
  Plant Island: "29/67"
  Cold Island: "19/67"
  Air Island: "25/69"
  Water Island: "17/67"
  Earth Island: "26/66"
  Shugabush Island: "4/32"
  Ethereal Island: "13/58"
  Ethereal Workshop: "10/26"
  Magical Sanctum: "6/44"
  Fire Haven: "13/65"
  Fire Oasis: "12/67"
  Mythical Island: "6/43"
  Light Island: "11/60"
  Psychic Island: "9/59"
  Faerie Island: "13/59"
  Bone Island: "10/59"
```

## Relevant islands for the immediate egg audit

The immediate breeding audit concerns:

- Congle
- Drumpler
- Maw
- Pango

Most relevant visible islands:

```yaml
egg_audit_relevant_islands:
  primary:
    - Cold Island
    - Air Island
    - Water Island
    - Earth Island
    - Plant Island
  secondary:
    - Fire Oasis
    - Fire Haven
  not_primary_for_this_egg_list:
    - Shugabush Island
    - Ethereal Island
    - Ethereal Workshop
    - Magical Sanctum
    - Mythical Island
    - Light Island
    - Psychic Island
    - Faerie Island
    - Bone Island
```

## Visible breeding / nursery states

Overview screenshots are useful for identifying that structures may be active or ready, but they are not always enough to identify exact breeding results.

```yaml
visible_structure_states:
  Cold Island:
    breeding_structure: heart_icon_visible
    interpretation: successful_breed_ready
    priority: inspect_first

  Plant Island:
    breeding_or_nursery_activity: visible_but_exact_result_unknown
    priority: inspect_for_drumpler_or_maw

  Air Island:
    breeding_or_nursery_activity: visible_but_exact_result_unknown
    priority: inspect_for_congle_or_pango

  Water Island:
    breeding_or_nursery_activity: visible_but_exact_result_unknown
    priority: inspect_for_congle_or_maw

  Earth Island:
    breeding_or_nursery_activity: visible_but_exact_result_unknown
    priority: inspect_for_drumpler
```

## Recommended audit order

```text
1. Cold Island — inspect the heart over the Breeding Structure first.
2. Cold Island — inspect Nursery / Bonus Nursery if occupied.
3. Air Island — inspect Breeding Structure and Nursery.
4. Water Island — inspect Breeding Structure and Nursery.
5. Earth Island — inspect Breeding Structure and Nursery.
6. Plant Island — inspect active structures for Drumpler / Maw cleanup.
```

## Recognition lessons

This batch teaches several important rules:

1. Treat a multi-island screenshot batch as a world/account snapshot.
2. Use map inventory screenshots to anchor island population counts.
3. Do not infer exact breeding results from overview screenshots unless the result is visibly labeled or the user confirms it.
4. Use visible action icons to prioritize manual inspection.
5. Preserve the difference between account-wide state, island state, and immediate breeding-task state.
6. For breeding audits, identify relevant islands first, then inspect active structures in priority order.

## Proposed state patch

```yaml
observed_at: manual_screenshot_batch
source: world_overview_batch_2026_07_09

account:
  level: 28
  diamonds: 8
  treats: 105448
  top_left_meter: "64/325"
  top_left_timer: "1d 15h"
  top_left_meter_classification: visible_but_unmodeled

inventory_counts:
  Plant Island: "29/67"
  Cold Island: "19/67"
  Air Island: "25/69"
  Water Island: "17/67"
  Earth Island: "26/66"
  Shugabush Island: "4/32"
  Ethereal Island: "13/58"
  Ethereal Workshop: "10/26"
  Magical Sanctum: "6/44"
  Fire Haven: "13/65"
  Fire Oasis: "12/67"
  Mythical Island: "6/43"
  Light Island: "11/60"
  Psychic Island: "9/59"
  Faerie Island: "13/59"
  Bone Island: "10/59"

breeding_audit:
  target_eggs:
    Congle: 2
    Drumpler: 2
    Maw: 1
    Pango: 1
  inspect_first:
    - Cold Island breeding_structure
    - Cold Island nursery
    - Air Island breeding_structure
    - Air Island nursery
    - Water Island breeding_structure
    - Water Island nursery
    - Earth Island breeding_structure
    - Earth Island nursery
    - Plant Island breeding_structure
    - Plant Island nursery
```

## Mirror island addendum

The initial world overview batch missed Mirror Plant Island and Mirror Cold Island. The user caught this and added both screenshots afterward.

Additional screenshot files:

```text
training/screenshots/2026-07-09-world-overview-mirror-plant-island.png
training/screenshots/2026-07-09-world-overview-mirror-cold-island.png
```

These images extend the batch from 16 island overviews to 18 island overviews.

The map inventory counts recorded above were read from the three map / island inventory screenshots already present in the batch. Mirror island population counts should not be inferred here unless they are visible in a map inventory screenshot or confirmed by the user.
