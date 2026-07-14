# Inventory data and generator contract

The canonical player inventory is stored as one YAML file per island under
`inventory/islands/`. Screenshot evidence and Git history therefore remain
island-scoped, while `inventory/README.md` provides one generated human view.

## Field semantics

- `discovered` mirrors whether the monster is unlocked in the Book of Monsters.
- `owned` is the current island count shown by the Market or supported by the
  island overview. Eggs still breeding or incubating are not included.
- A monster may have `discovered: true` and `owned: 0` after being sold or boxed.
- `confidence` records visually inferred counts.
- `pending` records breeding or incubation state separately from owned monsters.

## Island file shape

```yaml
schema_version: 1
island: Island Name
observed_at: YYYY-MM-DD
evidence: {}
book: {}
monsters:
  - name: Monster
    variant: common
    class: natural
    discovered: true
    owned: 1
pending: []
notes: []
```

`variant` is `common`, `rare`, or `epic`. `owned` is a non-negative integer
when known and `null` only when evidence proves discovery without supporting a
reliable current count.

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

## Regenerating the README

```bash
bin/inventory
```

Use `bin/inventory --check` in automation to fail when the generated README is
stale, or `bin/inventory --stdout` to preview without writing.
