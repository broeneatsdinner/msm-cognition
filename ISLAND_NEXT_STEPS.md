# Island Next Steps

This file used to hold handwritten, time-sensitive breeding recommendations.
Those entries were tied to an August 14, 2026 availability window and are no
longer a current source of truth.

Current next-step recommendations should be generated from separate checked-in
indexes:

1. `inventory/islands/*.yaml` for the player's current island inventory.
2. `reference/rosters/` for each island's full eligible monster roster.
3. `reference/availability/snapshots/` for dated current availability windows.
4. `reference/breeding/` for candidate parent recipes, timers, and failure
   outcomes.
5. `pending` entries in inventory YAML for active breeding, incubation, castle
   upgrades, or other time-gated work.

Use `inventory/README.md` for the current generated inventory view. Before a
planner recommends breeding actions, run:

```bash
bin/inventory --check
python3 -m unittest tests/test_inventory.py
```

As of the current 2026-08-22 inventory batch:

- Plant Island, Cold Island, and Air Island reconcile exactly against their
  checked castle bed panels.
- Water Island has an unresolved `+2` bed audit delta.
- Earth Island has an unresolved `+6` bed audit delta.
- Magical Sanctum needs Magical monster bed requirements before castle-style bed
  auditing can be applied.

