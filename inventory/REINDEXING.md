# Screenshot re-indexing checklist

Use this checklist when updating `inventory/islands/*.yaml` from a dated
screenshot batch. The goal is to preserve screenshot evidence, separate visible
facts from inference, and leave the generated inventory reproducible.

For the broader planner architecture, including roster, availability, inventory,
and breeding recipe indexes, see `planning/README.md`.

## Inputs

- Confirm the island folder name and screenshot batch date.
- Confirm that screenshots are already sorted by island.
- Check the latest `reference/islands/player-map-YYYY-MM-DD.json` snapshot for
  the player's map order and locked/unlocked island state.
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

Use full island names in notes, review comments, and search terms, such as
`Earth Island` instead of `Earth`, so natural islands are not confused with
Mirror islands.

## Island roster sources

Do not build an island inventory from a global monster list. Each island has its
own roster.

- The island's Book screenshots are authoritative for this account's discovered
  and locked entries at the observation date.
- Reference rosters for monsters that can ever appear on an island should be
  derived from canonical or stable sources, such as the official
  *My Singing Monsters* pages, the *My Singing Monsters* wiki, or checked-in
  reference exports.
- When reference rosters disagree with the user's Book screenshots, keep the
  screenshot-derived account state and record the roster uncertainty for review.
- Limited-time availability is not the same as island eligibility. Do not infer
  current promotions from static roster data or screenshots unless the offer is
  visible in the screenshot.
- Current availability should be recorded separately as a dated availability
  snapshot from an external lookup when the user asks for planning or next-step
  inference. That snapshot should include the source, lookup time, availability
  start if known, availability end or remaining duration, and the islands or
  variants affected. Do not collapse this to a simple available/unavailable
  flag.
- Planning should consider availability windows alongside breeding timers,
  enhanced timers, likely failure-result timers, Nursery availability, and retry
  count. A monster that is available for a short window may outrank a more
  desirable target with a longer window, while a long failure timer may make a
  late attempt poor even when the target is technically available.
- Breeding targets may have multiple valid parent combinations. Store those as
  candidate recipes rather than a single preferred combo. A planner can then rank
  recipes by owned parent readiness, target success timer, enhanced timer,
  possible failure results and their timers, expected retry cadence, parent
  levels, and any user preference. The best combo is contextual, not intrinsic.

## Interpretation rules

- Screenshot reads produce evidence first, not canonical inventory. Do not let a
  low-confidence visual guess directly mutate `inventory/islands/*.yaml` as
  fact.
- Treat Book pages as the stronger source for island roster and discovery
  state. Market pages can supply current owned counts, prices, and visible
  availability, but Market visibility does not remove or undiscover a monster
  shown in the Book.
- Book totals can prove that some discovery exists without proving which monster
  it is. If a Book silhouette is ambiguous, record the count under
  `unresolved_discoveries` rather than assigning `discovered: true` to a guessed
  monster row.
- Prefer Market owned counts over visual island counts when the Market clearly
  shows a current count for a Book-confirmed monster.
- Transcribe Market pages page by page before reconciling beds. For each visible
  card, check the monster name, variant, and owned count as a single unit; do
  not carry a count forward from a neighboring card or from a previous island.
- A Market card that is absent because the monster is not currently available
  does not prove `owned: 0`. Only set a Book-discovered monster to `owned: 0`
  when a visible Market card, user confirmation, or another direct source shows
  a zero current count.
- Ignore Buyback entries when recording current inventory. A Buyback card proves
  historical ownership only; it does not add to `owned` and does not need a note
  unless the user asks to audit sold or teleported monsters separately.
- Use overview screenshots for structures, castle tier, visible monsters, and
  counts that the Market cannot confirm.
- Record Hotel occupants with `checked_in` on the matching monster row. Checked-in
  monsters remain owned inventory but do not occupy Castle beds.
- Record the visible castle tier in `castle.name`; generated inventory joins it
  to `reference/castles/bed-capacities.json` for bed capacity.
- Use Book screenshots for `discovered` status and discovered totals.
- Do not count eggs still breeding or incubating as `owned`.
- Keep discovered monsters with a current count of zero in the regular
  `monsters` list as `discovered: true` and `owned: 0`. This means the monster
  was discovered but is not currently present as owned inventory on that island.
- Record breeding, incubation, and castle upgrades under `pending`.
- Use `confidence` when a count is visually inferred or partially obstructed.
- Treat the castle bed panel as an audit, not a primary monster counter. If
  visible counts do not explain the panel, leave a non-zero bed audit delta and
  explain it in notes rather than silently inventing counts.
- Add a `notes` entry when a boxed monster, hotel state, uncertain count, or
  other exception explains an otherwise surprising value.
- Do not silently infer island identity. Require the folder name, visible UI,
  distinctive terrain, or user confirmation.

## YAML update pass

For an existing island file:

1. Update `observed_at` to the screenshot batch date.
2. Update `evidence.screenshot_directory`.
3. Replace the `evidence` filename lists with the current screenshot groups.
4. Update `book` discovered totals.
5. Update monster `discovered` and `owned` values only from direct evidence.
   Put ambiguous Book discoveries in `unresolved_discoveries`.
6. Update `pending` for active breeding, incubation, castle upgrades, or other
   state that is not yet owned inventory.
7. Refresh `notes` so exceptions and uncertainties are explicit.
8. Confirm every monster row has a non-negative integer `owned` count, and any
   `checked_in` count is a non-negative integer no greater than `owned`.
9. Regenerate the README and review the Castle table's beds used and beds free
   before treating an island as placement-ready.
10. If the Castle table has a non-zero bed audit delta, record whether the
   remaining difference is screenshot-supported, user-confirmed, or unresolved.
   Do not force the delta to zero only because the arithmetic permits it.

For a new island file:

1. Start from the closest existing island YAML with a similar inventory shape.
2. Keep `schema_version: 1`.
3. Include all known Common, Rare, Epic, Seasonal, Dipster, Werdo, Mythical,
   Ethereal, Supernatural, Legendary, Magical, Fire, Celestial, Wublin, Workshop,
   or island-specific rows represented by that island's Book and references.
4. Set unknown-but-not-discovered entries to `discovered: false` and `owned: 0`.
5. Do not use nullable owned counts. If discovery is proven but the monster
   identity is not reliable, use `unresolved_discoveries`. If the identity is
   proven but the owned count is not reliable, choose the best explicit integer
   count, mark `confidence: low`, and explain the evidence gap in `notes`.

## Validation

After editing YAML:

```bash
bin/inventory
python3 -m unittest tests/test_inventory.py
```

If the generator fails because breedability data is missing, add or correct the
island entry in `reference/breeding/island-breedability.json` before accepting
the inventory update.

For a non-zero Castle bed audit delta, use the bed audit helper before asking
for more manual in-game checks:

```bash
python3 scripts/audit_inventory_beds.py --island "Water Island"
python3 scripts/audit_inventory_beds.py --island "Water Island" --assume-panel-includes-hotels
```

Use the full island name so natural islands and Mirror islands cannot be mixed.
The `--assume-panel-includes-hotels` mode is experimental until the in-game
Castle panel behavior around Hotel occupants is confirmed.

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
