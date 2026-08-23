# Availability snapshots

This directory records dated snapshots of limited-time monster availability.

Availability is separate from island eligibility and player inventory. A monster
can be eligible for an island but unavailable today, and a monster can be
available today while the player lacks the required parents.

Future snapshots should live under `reference/availability/snapshots/` and
record source, lookup time, availability window, affected islands, affected
variants, and confidence.

Availability snapshots should be created from an external current lookup, not
from static roster data. When possible, include:

- `observed_at` or lookup timestamp
- source URL or source description
- start time, if known
- end time or remaining duration
- affected full island names
- affected monster names and variants
- confidence and any ambiguity

Inventory files may note visible Market offer timers from screenshots, but a
planner should still use this directory for the current availability state that
drives next-action recommendations.
