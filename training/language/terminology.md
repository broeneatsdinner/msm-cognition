# Terminology

Use in-game language when modeling My Singing Monsters.

## Confirmed terms

```text
treats      The resource used to feed monsters. Do not call this food.
coins       Coin currency shown in the top UI.
diamonds    Diamond currency shown in the top UI.
```

## Structures

```text
Breeding Structure          Default breeding structure
Bonus Breeding Structure    Purchased additional breeding structure
Nursery                     Default nursery
Bonus Nursery               Purchased additional nursery
Wishing Torch
Mine
Coloss-Eye
Castle
```

## Unclassified UI

Do not call the `130/205` top-left meter "likes."

Until the mechanic is modeled, record it neutrally:

```yaml
visible_ui:
  top_left_meter: "130/205"
  classification: visible_but_unmodeled
```
