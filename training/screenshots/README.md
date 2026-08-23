# Screenshots

This directory stores screenshot files used as training examples.

## Naming convention

Use descriptive, dated names:

```text
2026-07-09-plant-island-01.jpeg
2026-07-09-plant-island-02.jpeg
```

For full island inventory batches, use one dated parent directory with numbered
full island-name folders, for example:

```text
My Singing Monsters Island Inventories 2026-08-22/
  02 Plant Island/
  03 Cold Island/
```

Use full island names in folders and notes so natural islands are not confused
with Mirror islands.

Use the latest `reference/islands/player-map-YYYY-MM-DD.json` snapshot for map
order and lock state when creating inventory batch folders. Locked islands do
not need screenshot folders unless the user explicitly captures their locked
state.

## Workflow

1. Save the screenshot locally.
2. Copy it into this directory.
3. If the screenshots are an inventory batch, sort them into the island folder
   before editing `inventory/islands/*.yaml`.
4. Add a matching observation file under `training/observations/` when the
   screenshot is training evidence rather than inventory evidence.
5. Add a correction file under `training/corrections/` if the screenshot
   produced a useful mistake or terminology clarification.

Screenshots are training material, not just evidence. They help document how the interface is learned.

For inventory batches, follow `inventory/REINDEXING.md`: Book pages drive
discovery state, visible Market cards drive current owned counts, Buyback cards
are ignored for current inventory, pending eggs or breeding are not counted as
owned, and castle bed panels are audits rather than primary monster counters.
