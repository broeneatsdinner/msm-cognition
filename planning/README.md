# Planning architecture

Planning should be generated from separate indexes, not handwritten as a list of
favorite targets.

## Indexes

### Island roster index

The roster index answers: what monsters can ever appear on each island?

Store this under `reference/rosters/`. It should be derived from stable sources
such as official *My Singing Monsters* pages, the *My Singing Monsters* wiki,
checked-in reference exports, and the user's Book screenshots when validating
account-visible island rosters.

Roster data should not say whether the user owns a monster, and it should not
say whether a limited-time monster is currently available.

### Availability snapshot index

The availability index answers: what limited-time monsters are available now,
where, and for how long?

Store this under `reference/availability/snapshots/` as dated snapshots. Each
snapshot should record source, lookup time, start time if known, end time or
remaining duration, affected islands, affected variants, and confidence.

Availability data should not say whether the user owns the required parents.

### Player inventory index

The inventory index answers: what does this account currently have on each
island?

Store this under `inventory/islands/`, backed by sorted screenshot evidence under
`training/screenshots/`. Inventory data should record Book discovery, Market
owned counts, castle state, and pending work. Buyback cards are not current
inventory. Discovered monsters with zero current count remain normal inventory
rows with `discovered: true` and `owned: 0`.

### Breeding recipe index

The breeding index answers: how can a target be produced, and what are the
timing consequences?

Store this under `reference/breeding/`. A target may have multiple candidate
recipes. Each candidate recipe should preserve parent names, success timer,
enhanced success timer, likely failure results, failure timers, and any
constraints or source notes.

## Planner join

The planner should join:

```text
island roster
+ current availability snapshot
+ player inventory
+ breeding candidate recipes
+ pending structures and nursery state
= recommended next actions
```

## Recommendation criteria

A recommendation should consider:

- target eligibility for the island
- current limited-time availability window
- number of retry attempts likely before the window closes
- whether required parents are owned and idle
- parent levels when known
- success timer and enhanced success timer
- likely failure timers
- whether failure results are useful inventory progress
- Breeding Structure and Nursery availability
- user goals, such as completing a collection versus chasing a rare window

The best target and best parent combination are contextual decisions. They are
not static properties of a monster.

## First-pass workflow

For a first island batch:

1. Update or create player inventory YAML from screenshots.
2. Add only the roster and breedability scaffolding needed to keep generation
   valid.
3. Defer current availability lookup until planning is requested.
4. Record uncertainty instead of filling gaps from memory.
5. Generate inventory docs and run tests before using the data for planning.
