# Water Island bed audit handoff, 2026-08-23

This is where the Water Island inventory audit paused on 2026-08-23.

## Current recorded state

- Inventory source: `inventory/islands/water-island.yaml`
- Screenshot batch:
  `training/screenshots/My Singing Monsters Island Inventories 2026-08-22/05 Water Island`
- Castle: Paradise Castle
- Castle info panel, user-confirmed: `90/90` beds occupied
- Hotel: one Humble Hotel with one occupant, Blaise, a level 1 Cybop
- Hotel mechanic confirmed by in-game constraint: Blaise cannot be checked out
  while Water Island has `90/90` occupied Castle beds, so the Hotel is keeping
  Blaise on Water Island without occupying Castle beds.
- Buyback: `Walden`, a Fwog, ignored for current inventory

The Water Island Cybop row is recorded as owned and checked in:

```yaml
- {name: Cybop, variant: common, class: natural, discovered: true, owned: 1, checked_in: 1}
```

`checked_in` means the monster is owned inventory but is excluded from placed
Castle bed usage under the current model.

## Current bed math

Run:

```bash
python3 scripts/audit_inventory_beds.py --island "Water Island"
```

Current result:

```text
Indexed Castle beds used: 86
Checked-in Hotel beds: 2
Total owned beds: 88
Panel: 90/90
Bed audit delta: +4
```

Checked-in Hotel occupants do not count against the Castle panel. The smallest
single-card reconciliations were:

```text
Common Shellbeat +1
Rare Shellbeat +1
```

The Water Island screenshots, OCR pass, and user re-check all support the
existing values:

```text
Common Shellbeat = 5
Rare Shellbeat = 4
```

So the current `+4` mismatch is not resolved by Shellbeat counts or Hotel
accounting.

## Disproved zero-owned candidates

The user checked these Water Island rows directly:

```text
Rare Toe Jammer = 0
Rare Anglow = 0 and undiscovered
Epic Wubbox = 0 and undiscovered
```

This corrected two bad Book silhouette identifications in
`inventory/islands/water-island.yaml`:

- Rare Anglow is now `discovered: false`.
- Epic Wubbox is now `discovered: false`.
- Rare Scups is the current low-confidence row preserving the Book's `4/19`
  Rare count.
- Epic Blabbit is the current medium-confidence row preserving the Book's
  `1/19` Epic count.

These corrections did not change the Castle bed delta, because the corrected
rows all remain owned `0`.

## Market sequence re-read

The Water Island Market screenshots were re-read as a scrolling sequence, with
the rule that there is only one card per monster/variant in a Market section and
overlapping screenshots must not be counted as duplicate inventory.

Visible unique Market cards and counts:

| Screenshot | Cards |
| --- | --- |
| `IMG_0917.jpg` | Spunge 5, Rare Shellbeat 4, Rare Toe Jammer 0 |
| `IMG_0918.jpg` | Rare Tweedle 2, T-Pirainha 0, Maggpi 0 |
| `IMG_0919.jpg` | Parlsona 0, Do 0, Re 0 |
| `IMG_0920.jpg` | Mi 0, Fa 0, Sol 0 |
| `IMG_0921.jpg` | La 0, Ti 0, Wubbox 0 |
| `IMG_0922.jpg` | Epic Wubbox 0, Tweedle 1, Potbelly 1 |
| `IMG_0923.jpg` | Noggin 1, Toe Jammer 1, Dandidoo 1 |
| `IMG_0924.jpg` | Cybop 1, Quibble 1, Shrubb 2 |
| `IMG_0925.jpg` | Oaktopus 1, Fwog 1, Reedling 1 |
| `IMG_0926.jpg` | Scups 1, Pummel 1, Shellbeat 5 |
| `IMG_0927.jpg` | Jeeode 1, Anglow 1, Buyback Walden ignored |

This re-read found no duplicated same-monster Market cards that explain the
`+4` Castle bed delta. The current Water Island inventory rows match the visible
unique Market cards above.

## What to test next

When resuming in-game, do these in order:

1. Keep Castle panel as `90/90` and Hotel as Blaise checked in unless the game
   state changes.
2. Do not re-check Common Shellbeat or Rare Shellbeat unless new evidence
   contradicts the confirmed counts.
3. Check the next smallest `+4` explanations:
   - two 2-bed common monsters off by one each
   - one 3-bed monster plus one 1-bed monster off by one each
   - one other 4-bed monster row not represented by Shellbeat or Rare Shellbeat
4. Prioritize any Water Island rows that were not directly visible in the Market
   screenshots or were visually inferred from Book totals.

Do not re-check the whole Water Island Market unless the narrowed checks still
fail to reconcile the audit.

## Automation ideas

- Add a Market-card OCR report that crops each visible card slot, runs OCR, and
  emits `{screenshot, slot, name, owned_count, buyback}` candidates for review.
- Store screenshot-derived card observations separately from canonical inventory
  YAML, then generate a diff between observed cards and inventory rows.
- Add a review contact sheet that highlights only cards related to a bed audit
  delta, such as 4-bed or 2-bed suspects.
- Add a dedicated Hotel evidence model so the repo can distinguish owned,
  placed, checked-in, boxed, and pending monsters without overloading notes.
- Add confirmed-count exclusions to `scripts/audit_inventory_beds.py`, so
  re-checks like Shellbeat and Rare Shellbeat can be removed from the next
  candidate pass.

## Validation status at pause

The repo validated after adding the audit helper:

```bash
bin/inventory --check
python3 -m unittest tests/test_inventory.py
```

Both passed.
