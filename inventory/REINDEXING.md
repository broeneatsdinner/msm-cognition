# Screenshot re-indexing checklist

Use this checklist when updating `inventory/islands/*.yaml` from a dated
screenshot batch. The goal is to preserve screenshot evidence, separate visible
facts from inference, and leave the generated inventory reproducible.

## Inputs

- Confirm the island folder name and screenshot batch date.
- Confirm that screenshots are already sorted by island.
- Ignore `.DS_Store` and other Finder metadata.
- Treat empty island folders as intentional unless the user says otherwise.

## Evidence pass

For each island folder, identify the screenshot groups before editing YAML:

- `overview`: island-wide screenshots showing castle, placed monsters,
  structures, and visible pending state.
- `book`: Book of Monsters screenshots showing discovered totals and locked or
  unlocked entries.
- `market`: Market screenshots showing current owned counts.
- `breeding`: Breeding Structure, Nursery, or result screens showing pending
  parents, timers, eggs, or incubating monsters.
- `other`: screenshots that are useful context but do not directly update
  inventory state.

Record only the filenames, not absolute paths, under the island's `evidence`
section. Keep `evidence.screenshot_directory` relative to the repo root.

## Interpretation rules

- Prefer Market owned counts over visual island counts when the Market clearly
  shows a current count.
- Use overview screenshots for structures, castle tier, visible monsters, and
  counts that the Market cannot confirm.
- Use Book screenshots for `discovered` status and discovered totals.
- Do not count eggs still breeding or incubating as `owned`.
- Record breeding, incubation, and castle upgrades under `pending`.
- Use `confidence` when a count is visually inferred or partially obstructed.
- Add a `notes` entry when a zero-owned discovered monster, boxed monster,
  hotel state, or other exception explains an otherwise surprising value.
- Do not silently infer island identity. Require the folder name, visible UI,
  distinctive terrain, or user confirmation.

## YAML update pass

For an existing island file:

1. Update `observed_at` to the screenshot batch date.
2. Update `evidence.screenshot_directory`.
3. Replace the `evidence` filename lists with the current screenshot groups.
4. Update `book` discovered totals.
5. Update monster `discovered` and `owned` values.
6. Update `pending` for active breeding, incubation, castle upgrades, or other
   state that is not yet owned inventory.
7. Refresh `notes` so exceptions and uncertainties are explicit.

For a new island file:

1. Start from the closest existing island YAML with a similar inventory shape.
2. Keep `schema_version: 1`.
3. Include all known Common, Rare, Epic, Seasonal, Dipster, Werdo, Mythical,
   Ethereal, Supernatural, Legendary, Magical, Fire, Celestial, Wublin, Workshop,
   or island-specific rows represented by that island's Book and references.
4. Set unknown-but-not-discovered entries to `discovered: false` and `owned: 0`.
5. Use `owned: null` only when discovery is proven but the current count is not
   reliable.

## Validation

After editing YAML:

```bash
bin/inventory
python3 -m unittest tests/test_inventory.py
```

If the generator fails because breedability data is missing, add or correct the
island entry in `reference/breeding/island-breedability.json` before accepting
the inventory update.

## Review discipline

Before finalizing:

- Compare the generated `inventory/README.md` summary against the screenshot
  evidence.
- Call out any low-confidence counts or missing Market views.
- Keep screenshot-derived observations honest: observed visible facts,
  uncertain readings, interpreted game mechanics, and proposed state updates are
  different things.
- Do not update planning docs from inventory screenshots unless the user asked
  for planning changes too.
