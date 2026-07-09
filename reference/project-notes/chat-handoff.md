# Chat Handoff

This file helps future conversations rehydrate the MSM Cognition project context.

## Project intent

MSM Cognition is a public, portfolio-safe workbench for My Singing Monsters reference, screenshot interpretation, and breeding/inventory decision support.

It records both current reference data and the learning process used to interpret the game interface.

## Current repo shape

```text
assets/       Visual reference assets
examples/     Future public examples and fixtures
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
