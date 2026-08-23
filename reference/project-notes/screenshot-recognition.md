# Screenshot Recognition

This file records how MSM Cognition should interpret screenshots.

## Core principle

Screenshot interpretation should separate observation from interpretation.

Do not silently convert uncertain visual guesses into repo state.

## Recognition layers

Each screenshot read should be organized as:

```text
Observed       Visible facts in the screenshot
Uncertain      Plausible but untrusted observations
Interpreted    Game mechanics inferred from visible facts
Proposed       Safe state update, if any
```

## Island identification

Island identity should be confirmed by one or more of:

- user-provided island name
- visible island name in the UI
- distinctive terrain or base shape
- distinctive structures or island context
- known account state from nearby context

If the island name is not visible and not user-confirmed, mark it uncertain.
Use full island names in notes and repo updates, such as `Water Island` or
`Mirror Water Island`, to avoid natural/Mirror island confusion.

## Inventory screenshots

Inventory screenshots have their own source hierarchy:

1. Book pages determine discovered state and Book totals.
2. Visible Market cards determine current owned counts for that monster and
   variant.
3. Overview screenshots support castle tier, visible placed monsters, and
   state that Market pages cannot show.
4. Breeding Structure, Nursery, and result screens support pending state, not
   owned counts until placement.
5. Buyback cards prove historical ownership only and are ignored for current
   inventory.

Do not treat a missing Market card as `owned: 0`. A monster may be absent from
the Market because it is not currently offered. Every inventory monster row must
still use an explicit non-negative integer `owned` count; unresolved evidence is
recorded through `confidence: low`, notes, and bed audit deltas.

Castle bed panels audit the inventory rows. They can reveal drift, but they
should not silently assign a specific monster count without screenshot evidence,
user confirmation, or an explicit low-confidence note.

## Global top UI

The top UI can include:

- account level badge
- coins
- diamonds
- treats
- event or meter values
- timers

Use in-game terms. Record ambiguous meters neutrally.

Example:

```yaml
account:
  level: 28
  coins: 15800395
  diamonds: 47
  treats: 55928

visible_ui:
  top_left_meter: "130/205"
  top_left_timer: "2d 6h"
  classification: visible_but_unmodeled
```

## Structure naming

Use MSM terminology:

```text
Breeding Structure
Bonus Breeding Structure
Nursery
Bonus Nursery
Wishing Torch
Mine
Coloss-Eye
Castle
```

## Write discipline

Screenshot-derived updates should be proposed first, reviewed second, and
committed only after uncertain fields are excluded, confirmed, or explicitly
recorded as low-confidence integer counts with notes.
