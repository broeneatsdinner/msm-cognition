# Island inventories

This directory stores the canonical, machine-readable player inventory for each
island. Each island has its own YAML file so that screenshots, updates, and Git
history remain island-scoped.

## Files

- `islands/plant-island.yaml`
- `islands/magical-sanctum.yaml`

## Field semantics

- `discovered` mirrors whether the monster is unlocked in the Book of Monsters.
- `owned` is the current island count shown by the Market, or a count supported
  by the island overview. Eggs still breeding or incubating are not included.
- A monster may have `discovered: true` and `owned: 0` after being sold or boxed.
- `confidence` is included when a count comes from visual inspection rather
  than a directly displayed Market number.
- `pending` records breeding or incubation state separately from owned monsters.

The dated screenshot directories under `training/screenshots/inventory/` are
the evidence snapshots. These YAML files are the current structured state that
future inventory tooling should read.

## Generator contract

All island files use this top-level shape:

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

`variant` is one of `common`, `rare`, or `epic`. `owned` is a non-negative
integer when known and `null` only when the screenshots prove discovery but do
not support a reliable current count.
