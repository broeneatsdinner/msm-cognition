# Inventory data and generator contract

The canonical player inventory is stored as one YAML file per island under
`inventory/islands/`. Screenshot evidence and Git history therefore remain
island-scoped, while `inventory/README.md` provides one generated human view.

For the repeatable workflow used to re-evaluate islands from a dated screenshot
batch, see `inventory/REINDEXING.md`.

## Field semantics

- `discovered` mirrors whether the monster is unlocked in the Book of Monsters.
- `owned` is the current island count shown by the Market or supported by the
  island overview. Eggs still breeding or incubating are not included.
- A monster may have `discovered: true` and `owned: 0` after being sold or boxed.
- `unresolved_discoveries` records Book-discovered slots whose exact monster
  identity is not confidently known.
- `confidence` records visually inferred counts.
- `checked_in` records how many owned copies of that row are checked into a
  Hotel and therefore do not occupy Castle beds.
- `pending` records breeding or incubation state separately from owned monsters.
- `castle` records the current visible castle tier and optional upgrade state.
- Castle bed capacity is derived from `reference/castles/bed-capacities.json`.
- Monster bed usage is derived from `reference/monsters/bed-requirements.json`.
  Every monster row must use a non-negative integer `owned` count.

## Island file shape

```yaml
schema_version: 1
island: Island Name
observed_at: YYYY-MM-DD
evidence: {}
castle:
  name: Castle Name
  confidence: high
  observed_beds_occupied: 117
  observed_beds_available: 120
book: {}
unresolved_discoveries:
  rare:
    count: 1
    evidence: Book shows one more Rare discovery than confidently identified rows.
monsters:
  - name: Monster
    variant: common
    class: natural
    discovered: true
    owned: 1
    checked_in: 0
pending: []
notes: []
```

`variant` is `common`, `rare`, or `epic`. `owned` is always a non-negative
integer. Do not use `owned: null`; unresolved evidence belongs in `notes`, a
non-zero bed audit delta, or a separate review task.

`checked_in` is optional and defaults to `0`. It must be a non-negative integer
no greater than `owned`.

Keep count provenance strict. A visible Market card can set `owned` for that
monster and variant. A missing Market card does not set `owned: 0` for a
Book-discovered monster, because the card may be unavailable during that
screenshot window. A castle bed audit can prove that some count is still wrong
or hidden, but it should not be used to choose a specific monster count without
screenshot evidence, user confirmation, or an explicit low-confidence note.

Do not force ambiguous Book silhouettes into named monster rows. If the Book
count proves a discovery exists but the monster identity is not confidently
identified, record it under `unresolved_discoveries` for that variant. A
low-confidence named row is acceptable for a current owned count only when there
is additional Market, overview, bed-audit, or user evidence supporting that
specific monster. Zero-owned low-confidence Book guesses are not canonical
inventory.

## Breeding-plan join

Rare and Epic first-copy recipes live in
`reference/breeding/rare-epic-breeding.json`. The inventory generator joins
those island-scoped rules to owned monsters by canonical name. A Common or Rare
parent can satisfy a recipe; an Epic cannot breed.

Exact island-and-variant breedability lives in
`reference/breeding/island-breedability.json`. Every monster row must appear in
exactly one of that variant's `breedable` or `not_breedable` lists. Generation
fails on missing or contradictory classifications instead of silently guessing.

`Breedable?` means the exact variant can be produced in a Breeding Structure on
that island while available. A monster may still be obtainable on an island
when this field is `No`, such as a Dipster placed with a Key, a Werdo purchased
with Relics, or a Wubbox acquired through purchase, boxing, or evolution.

Availability is deliberately reported as `When offered`. The static inventory
does not claim that a limited-time target is currently available in the game.

## Bed usage join

The generated Castle table reports known beds used, castle capacity, known beds
free, checked-in Hotel beds, total owned beds, and any difference from the
in-game castle panel. Dipsters use 0 beds. Rare Wubbox and Epic Wubbox use
variant-specific bed requirements rather than the Common Wubbox requirement.

When the in-game castle info panel is checked, record
`observed_beds_occupied` and `observed_beds_available` under `castle`. These
panel values audit the inventory rows. A non-zero bed audit delta means the
monster owned counts need further review; it should not be solved by inventing
monster counts without screenshot or user confirmation.

If an audit delta remains after all visible Market pages are transcribed, keep
the generated delta visible and explain it in `notes`. Use a low-confidence
integer only when the note explains that the value is an intentional bed-audit
inference. Do not introduce nullable or unknown owned rows.

## Regenerating the README

```bash
bin/inventory
```

Use `bin/inventory --check` in automation to fail when the generated README is
stale, or `bin/inventory --stdout` to preview without writing.
