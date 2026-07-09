# MSM Cognition

Visual reference, screenshot recognition, and breeding inference for *My Singing Monsters*.

This project starts with a simple question:

> What am I looking at in the breeder, and what is it likely to produce?

The first layer is a human-readable visual reference for Natural monster parent icons. The next layer is intended to use screenshots, local reference assets, and breeding rules to produce confidence-ranked interpretations of an in-progress breeding structure.

## Project idea

The long-term workflow is:

1. collect local reference assets
2. document the visible Natural monster icon set
3. accept a screenshot of a breeding structure
4. identify the two visible parent icons
5. combine detected parents with island context and timer data
6. return likely breeding outcomes with confidence scores

This is intentionally lightweight. The goal is not game automation or modification. The goal is to reduce lookup friction and turn a small visual-recognition problem into a reproducible local tool.

## Current scope

The current reference set covers the 30 Natural monsters used across the core Natural islands:

- Plant
- Cold
- Air
- Water
- Earth

It does not currently include Fire, Magical, Ethereal, Mythical, Seasonal, Rare, or Epic variants.

## Repository layout

```text
assets/
  eggs/                 Local reference egg/icon assets

docs/
  msm-egg-reference.md  Human-readable visual reference table

examples/
  screenshots/          Local screenshots for testing, not committed by default

src/
  vision/               Future screenshot/icon matching code
  rules/                Future breeding rule data
  inference/            Future result-ranking logic
```

## Current status

This repository currently contains:

- local reference assets for the 30 Natural monsters
- a Markdown/HTML reference table for quick visual lookup
- spreadsheet-derived CSV data for islands, monsters, and Wublin blueprints
- JSON versions of that data for future scripts
- Markdown versions of that data for GitHub-readable browsing
- a planned structure for future screenshot recognition and breeding inference

## Data layers

The spreadsheet exports are represented in three forms:

```text
data/raw/*.csv   Snapshot of the spreadsheet-derived tabular data
data/raw/*.json  Script-friendly structured data
docs/data/*.md   Human-readable Markdown tables
```

The intent is to keep the source data easy to inspect by a person while also making it usable by future Python code.

## Disclaimer

Monster names and images belong to Big Blue Bubble / My Singing Monsters.

This is an unofficial personal reference and tooling project. It is not affiliated with or endorsed by Big Blue Bubble.
