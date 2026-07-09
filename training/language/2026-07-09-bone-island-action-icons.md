# Bone Island Action Icon Language

This note preserves user-provided interpretation of action icons visible in the Bone Island collect-all sequence.

## User explanation

The user explained the post-collection island state this way:

> Note that in 4, there are still actions to be taken such as, on the right, dealing with the nursery egg that has hatched and is ready to be placed or sold, middle the castle which is offering another roll at the wheel for a video to be watched, and left the heart indicating that a breeding has been successful and it's ready to be zapped to a wublin, or moved to the nursery

## Interpreted terminology

```yaml
nursery_ready_egg_icon:
  meaning: egg has hatched and is ready for action
  possible_actions:
    - place
    - sell

castle_wheel_or_video_icon:
  meaning: optional castle-associated action is available
  possible_actions:
    - watch_video_for_wheel_roll

breeding_structure_heart_icon:
  meaning: breeding has succeeded
  possible_actions:
    - zap_to_wublin
    - move_to_nursery
```

## Recognition rule

When these icons appear, do not only record that an icon is visible. Record the icon as an actionable state.

Also preserve the user's language when available, because the user's explanation is part of the training signal.
