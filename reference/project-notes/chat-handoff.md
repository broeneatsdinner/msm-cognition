# Chat Handoff

This file helps future conversations rehydrate the MSM Cognition project context.

## Project intent

MSM Cognition is a public, portfolio-safe workbench for My Singing Monsters reference, screenshot interpretation, and breeding/inventory decision support.

It records both current reference data and the learning process used to interpret the game interface.

## Current repo shape

```text
assets/       Visual reference assets
reference/    Human + machine reference knowledge
scripts/      Repo-maintenance tooling
src/          Future importable cognition engine
training/     Screenshots, observations, corrections, and terminology
```

## Source of truth direction

The Google Sheet was bootstrap material.

Going forward, the repo should become the maintained source of truth. Updates should come from screenshots, quick notes, structured patches, and generated documentation.

## Important terminology

- Use `treats`, not `food`.
- Use `Breeding Structure` for the default breeder.
- Use `Bonus Breeding Structure` for the purchased second breeder.
- Use `Nursery` for the default nursery.
- Use `Bonus Nursery` for the purchased second nursery.
- Do not call the `130/205` top-left meter "likes"; treat it as visible-but-unmodeled until the mechanic is understood.

## Screenshot intake rule

Do not blindly infer island name unless it is visible or user-confirmed.

A screenshot extraction should separate:

- observed visible facts
- uncertain observations
- interpreted game mechanics
- proposed repo updates

## Known correction

A screenshot was previously misidentified as Cold Island. The user corrected it to Plant Island.

Lesson: do not infer island identity from castle/state similarity. Require island confirmation, visible UI text, or distinctive terrain/context.

## Training examples added

### Plant Island screenshot correction

Initial Plant Island screenshots are stored under:

```text
training/screenshots/2026-07-09-plant-island-01.jpeg
training/screenshots/2026-07-09-plant-island-02.jpeg
```

The assistant initially misidentified Plant Island as Cold Island. The user corrected this.

Training lesson:

- Do not infer island identity from castle/state similarity.
- Require user confirmation, visible UI text, or distinctive terrain/context.
- Preserve mistakes when they produce useful recognition rules.

Related records:

```text
training/observations/2026-07-09-plant-island-01.md
training/observations/2026-07-09-plant-island-02.md
training/corrections/2026-07-09-plant-island-misidentified.md
training/corrections/2026-07-09-terminology-corrections.md
training/language/2026-07-09-screenshot-intake-terms.md
```

### Bone Island collect-all sequence

A four-frame Bone Island interaction sequence is stored under:

```text
training/screenshots/2026-07-09-bone-island-collect-sequence-01-before.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-02-confirmation.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-03-animation.jpeg
training/screenshots/2026-07-09-bone-island-collect-sequence-04-after.jpeg
```

The user explicitly identified the island as Bone Island and explained the sequence:

1. currency available to collect
2. collect-all confirmation
3. collection animation
4. post-collection island state with remaining action icons

Training lesson:

- Treat related screenshots as an interaction sequence, not isolated images.
- Preserve before/after resource values.
- Record confirmation amounts separately from observed account deltas.
- Do not hide small reconciliation mismatches.
- User explanations of action icons are authoritative training data.

Related records:

```text
training/observations/2026-07-09-bone-island-collect-sequence.md
training/language/2026-07-09-bone-island-action-icons.md
```

## Current screenshot-intake discipline

Future screenshot reads should produce:

```text
Observed       visible facts
Uncertain      plausible but untrusted observations
Interpreted    game mechanics inferred from visible facts
Proposed       safe state update, if any
```

Use in-game terms:

- treats, not food
- Breeding Structure
- Bonus Breeding Structure
- Nursery
- Bonus Nursery

Do not call the `130/205` top-left meter likes. Record it as visible-but-unmodeled until the mechanic is understood.
