# Plant Island Screenshot 02 Observation

## Screenshot

`training/screenshots/2026-07-09-plant-island-02.jpeg`

## User context

The user sent a later screenshot of the same island to compare what changed and to test consistent UI interpretation.

## Observed

```yaml
source: main_island_view
island:
  name: Plant Island
  confirmed_by: user_correction
  confidence: high_after_correction

account_visible_ui:
  level: 28
  coins: 15800395
  diamonds: 47
  treats: 55928

visible_ui:
  top_left_meter: "130/205"
  top_left_timer: "2d 6h"
  classification: visible_but_unmodeled

structures:
  castle:
    visible: true
    apparent_name: Extravagant Castle
    confidence: medium
  breeding_structure:
    visible: true
    state: active_or_occupied
    confidence: high
  nursery:
    visible: true
    state: idle_or_empty
    confidence: medium_high
  wishing_torches:
    visible_count: 10
    confidence: high
  mine:
    visible: true
    apparent_name: Maximum Mine
    confidence: medium_high
  coloss_eye:
    visible: true
    apparent_status: Complete
    confidence: medium
```

## Delta from screenshot 01

```yaml
coins:
  previous_visible: 15437873
  latest_visible: 15800395
  delta: 362522

diamonds:
  previous_visible: 47
  latest_visible: 47

treats:
  previous_visible: 55928
  latest_visible: 55928

top_left_timer:
  previous_visible: "2d 7h"
  latest_visible: "2d 6h"
```

## Uncertain

```yaml
castle_capacity:
  status: not_visible

castle_upgrade_cost:
  status: not_visible

breeding_timer:
  status: not_visible_from_main_island_view

breeding_parents:
  status: not_visible_from_main_island_view

monster_levels:
  status: visible_but_not_reliably_readable
```

## Recognition note

This screenshot reinforces the need to separate visible UI facts from interpreted mechanics. The top-left `130/205` value is visible, but its mechanic should remain unclassified until modeled.
