# Water Island bed audit handoff, 2026-08-23

This is where the Water Island inventory audit paused on 2026-08-23.

## Current recorded state

- Inventory source: `inventory/islands/water-island.yaml`
- Screenshot batch:
  `training/screenshots/My Singing Monsters Island Inventories 2026-08-22/05 Water Island`
- Castle: Paradise Castle
- Castle info panel, user-confirmed: `90/90` beds occupied
- Hotel: one Humble Hotel with one occupant, Blaise, a level 1 Cybop
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
If the Castle panel includes Hotel occupants, the delta would be +2.
```

Under the current model, where checked-in Hotel occupants do not count against
the Castle panel, the smallest single-card reconciliations are:

```text
Common Shellbeat +1
Rare Shellbeat +1
```

The Water Island screenshots and OCR pass both support the existing values:

```text
Common Shellbeat = 5
Rare Shellbeat = 4
```

So the current `+4` mismatch is not resolved by the obvious Shellbeat counts.

## Alternate Hotel interpretation

It is still unproven whether the in-game Castle info panel includes monsters
checked into a Hotel. To test that alternate interpretation, run:

```bash
python3 scripts/audit_inventory_beds.py --island "Water Island" --assume-panel-includes-hotels
```

Current result:

```text
Bed audit delta, treating Hotel occupants as panel-counted: +2
```

Under that interpretation, the smallest one-card reconciliations are:

```text
Common Dandidoo +1
Common Cybop +1
Common Quibble +1
Common Shrubb +1
Common Oaktopus +1
Common Fwog +1
```

This does not mean one of those counts is wrong. It means those are the only
single count changes that would explain the remaining `+2` if the Castle panel
includes the checked-in Cybop.

## What to test next

When resuming in-game, do these in order:

1. Confirm whether the Castle info panel on Water Island still says `90/90`.
2. Confirm the Humble Hotel still has exactly one occupant: Blaise, level 1
   Cybop.
3. Determine the Hotel accounting rule if possible:
   - note the Water Island Castle panel while Blaise is checked in
   - temporarily check Blaise out or compare before/after if the game allows
     that safely
   - if the Castle occupied number changes by 2, Hotel occupants were excluded
     from the panel
   - if it does not change, Hotel occupants may already be included in the panel
4. If the panel excludes Hotel occupants, re-check only:
   - Common Shellbeat
   - Rare Shellbeat
5. If the panel includes Hotel occupants, re-check only:
   - Common Dandidoo
   - Common Cybop
   - Common Quibble
   - Common Shrubb
   - Common Oaktopus
   - Common Fwog

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
- Once the Hotel accounting rule is confirmed, encode it in
  `src/msm_cognition/inventory.py` and update the audit script wording.

## Validation status at pause

The repo validated after adding the audit helper:

```bash
bin/inventory --check
python3 -m unittest tests/test_inventory.py
```

Both passed.
