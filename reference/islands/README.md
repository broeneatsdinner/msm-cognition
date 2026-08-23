# Islands reference

This directory contains island reference material.

## Files

```text
islands.csv       Spreadsheet-derived CSV snapshot
islands.json      Spreadsheet-shaped JSON values
islands.md        Curated human-readable island status page
player-map-*.json Account-specific player map order and lock state snapshots
player-map-*.md   Human-readable player map snapshots
raw-export.md     Raw Markdown export preview
```

## Player map snapshots

`player-map-YYYY-MM-DD.*` files record the user's in-game map order and
locked/unlocked state at a point in time. These are account-specific and should
not be treated as the canonical global island list.

Use player map snapshots when creating dated screenshot inventory batches, so
locked islands are not mistaken for missing evidence and Mirror islands are not
confused with their natural counterparts.

When the map UI shows an island progress fraction, record it on that island as
`map_progress.current` and `map_progress.total`, with an `interpretation` and
`confidence`. Keep this separate from Book variant totals and current owned
monster counts. Big Blue Bubble support describes this sidebar fraction as how
many Monsters have been collected on that Island. In the 2026-08-23 map
snapshot, visible Natural Island fractions also match the inventory Book totals
plus Seasonal totals.

## Human-facing page

`islands.md` is the page intended for normal reading.

It is generated from `islands.csv` by:

```bash
python3 scripts/build_curated_docs.py
```

The curated page is organized as compact status cards rather than preserving the spreadsheet's side-by-side layout.
