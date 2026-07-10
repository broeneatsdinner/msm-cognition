# Breeding Reference

This directory contains structured breeding-reference data for My Singing Monsters.

The purpose is to prevent the workbench from inferring breedability from monster elements alone.

Breedability is island-scoped:

```text
island -> available Book of Monsters -> valid parent pair -> possible child
```

A monster's elements are not enough to decide where it can be bred.

## Data scope

`common-natural-breeding.json` is a first structured pass covering common Natural monsters and their source-listed best breeding combinations.

This is not yet a complete model of every possible breeding result in the game.

## Source model

The source data records:

- monster
- parent pair
- standard breeding time
- enhanced breeding time, where listed
- islands where the monster is listed as breedable
- mirror-island aliases that share Book of Monsters entries with the original island

## Core rule

Do not answer "can I breed X on island Y?" from elements alone.

Answer from island-scoped data.
