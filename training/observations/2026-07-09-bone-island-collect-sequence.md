# Bone Island Collect-All Sequence

## Screenshot sequence

This observation records a four-frame Bone Island interaction sequence.

```text
training/screenshots/2026-07-09-bone-island-collect-sequence-01-before.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-02-confirmation.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-03-animation.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-04-after.jpeg
```

## User context

The user identified the island as Bone Island.

The user described the four screenshots as:

1. first visit to the island, with currency available to collect from monsters
2. confirmation screen asking whether to collect all currency
3. collection animation in progress
4. island state after collecting currency

The user also explained remaining actions visible after collection:

- on the right, the Nursery has an egg that has hatched and is ready to be placed or sold
- in the middle, the Castle is offering another wheel roll if a video is watched
- on the left, the heart over the Breeding Structure indicates breeding has succeeded and the result is ready to be zapped to a Wublin or moved to the Nursery

## Observed visible facts

```yaml
island: Bone Island
island_confirmed_by_user: true
capture_type: main_island_interaction_sequence

account:
  level: 28
  diamonds: 47
  treats: 55928

visible_ui:
  top_left_meter: "130/205"
  top_left_timer: "2d 5h"
  top_left_meter_classification: visible_but_unmodeled
```

## Coin sequence

```yaml
coins:
  before_collect_all: 15800395
  confirmation_screen: 15800395
  during_collect_animation: 15807229
  after_collect_all: 15847045

collect_all_confirmation:
  offered_amount: 46626

observed_coin_delta:
  before_to_after: 46650

reconciliation:
  confirmation_amount: 46626
  observed_delta: 46650
  difference: 24
  status: unresolved_small_mismatch
```

## Interpreted UI states

These interpretations come from the user's explanation of the visible action icons.

```yaml
islands:
  Bone Island:
    breeding_structure:
      visible_indicator: heart_icon
      interpreted_state: successful_breed_ready
      action_available: true
      possible_actions:
        - move_to_nursery
        - zap_to_wublin

    nursery:
      visible_indicator: ready_egg_icon
      interpreted_state: egg_ready
      action_available: true
      possible_actions:
        - place
        - sell

    castle:
      visible_indicator: wheel_or_video_offer_icon
      interpreted_state: optional_action_available
      action_available: true
      possible_actions:
        - watch_video_for_wheel_roll
```

## Uncertain / not updated

The following should not be updated from this screenshot sequence alone:

```yaml
castle:
  exact_name: unknown_from_sequence
  capacity: unknown_from_sequence
  upgrade_cost: unknown_from_sequence

monsters:
  exact_inventory: visible_but_not_reliably_extracted
  levels: not_visible

breeding_result:
  exact_monster: not_visible
  target_wublin: not_visible
```

## Recognition lessons

This sequence teaches several important rules:

1. Treat related screenshots as an interaction sequence, not isolated images.
2. Preserve before/after numeric state when the UI shows account totals.
3. Record confirmation amounts separately from observed account deltas.
4. Do not hide small reconciliation mismatches.
5. User explanations of action icons are authoritative training data.
6. Distinguish visible UI facts from interpreted game mechanics.

## Proposed state patch

```yaml
observed_at: manual_screenshot_sequence
source: bone_island_collect_all_sequence
island_confirmed_by_user: true

account:
  level: 28
  coins:
    before: 15800395
    after: 15847045
  diamonds: 47
  treats: 55928

visible_ui:
  top_left_meter: "130/205"
  top_left_timer: "2d 5h"
  top_left_meter_classification: visible_but_unmodeled

collection_event:
  type: collect_all_currency
  confirmation_amount: 46626
  observed_coin_delta: 46650
  reconciliation_status: unresolved_small_mismatch
  reconciliation_difference: 24

islands:
  Bone Island:
    breeding_structure:
      state: successful_breed_ready
      action_available: true
      possible_actions:
        - move_to_nursery
        - zap_to_wublin
    nursery:
      state: egg_ready
      action_available: true
      possible_actions:
        - place
        - sell
    castle:
      action_available: true
      visible_indicator: wheel_or_video_offer
```
