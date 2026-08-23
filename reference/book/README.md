# Book of Monsters reference

This directory describes canonical Book of Monsters reference images used to
compare against account screenshots.

The goal is to avoid turning ambiguous Book silhouettes into canonical inventory
rows. Screenshot reads should compare against stable Book page references first,
then update inventory only when the identity is confidently supported.

## Files

```text
book-reference-manifest.json  Source manifest for reference Book images
images/                       Local downloaded image cache, gitignored
```

## Source policy

- Prefer official Big Blue Bubble sources when they provide the needed data.
- When official sources do not expose Book page images, use stable wiki file
  pages as reference evidence and record the source title and fetched URL.
- Do not commit downloaded reference images by default. They may be regenerated
  from the manifest, and image licensing may differ from page text licensing.
- Keep source metadata in git; keep generated image caches out of git unless the
  project deliberately decides to vendor a small reviewed subset.

## Workflow

Download reference images into the local cache:

```bash
python3 scripts/fetch_book_references.py
```

Use these references to compare:

- canonical island + variant Book layout
- exact visible silhouette positions
- account Book screenshot discovered slots
- unresolved discovery counts in `inventory/islands/*.yaml`

Ambiguous or unmatched slots should stay in `unresolved_discoveries` until a
Market card, clearer Book comparison, overview evidence, or user confirmation
identifies the monster.

## Current manifest scope

The first manifest covers Natural Island Book pages because those are the
currently indexed islands with Castle bed audits:

- Plant Island
- Cold Island
- Air Island
- Water Island
- Earth Island

Expand the manifest island by island as inventory indexing reaches the rest of
the player map.
