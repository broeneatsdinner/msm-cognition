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

Screenshot-derived updates should be proposed first, reviewed second, and committed only after uncertain fields are excluded or confirmed.
