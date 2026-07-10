# MSM Cognition

Visual reference, screenshot recognition, and breeding inference for *My Singing Monsters*.

This project starts with a simple question:

> What am I looking at in the breeder, and what is it likely to produce?

The first layer is a human-readable reference system: local egg/icon assets, curated Markdown pages, and spreadsheet-derived reference data. The next layer is intended to use screenshots, local reference assets, and breeding rules to produce confidence-ranked interpretations of an in-progress breeding structure.

## Why this project exists

This project is intentionally built around a game because the game makes the learning loop enjoyable and repeatable.

The work is useful in three ways:

1. **Fun** — the data comes from ordinary gameplay, not from a sterile benchmark.
2. **Educational** — every screenshot, mistake, correction, and terminology fix becomes practice in teaching a model to read a domain-specific interface.
3. **Enduring** — the recorded process can help others understand how to build their own domain-specific LLM workbenches.

The goal is not to pretend the model already knows the game. The goal is to show how a human can teach a model: by preserving examples, corrections, language, uncertainty, and state updates in a form future sessions can reuse.

### Source language

This README preserves polished project language, but the training record also keeps the original user phrasing that produced it:

> It's a very interesting project! And, I'm happy to do it because 1) it's fun (I get to play the game) and 2) it's educational (I get to learn how to train, and keep notes for myself on how to be a better teacher) and 3) it's enduring (if others can see how training of this sort works, they can apply it to their own projects)

That original phrasing is preserved in `training/language/2026-07-09-project-motivation.md` alongside the README interpretation.

## Purpose

MSM Cognition is a small cognition/workbench project for reducing lookup friction during gameplay.

The project is not game automation and does not modify the game. It is a local reference and reasoning aid built around a repeatable workflow:

1. collect reference assets
2. preserve spreadsheet-derived source data
3. generate human-readable reference pages
4. prepare script-readable data for future inference
5. eventually compare breeder screenshots against known visual references
6. combine visual recognition, island context, and timer data to rank likely outcomes

## Current capabilities

The repository currently contains:

- local egg/icon reference assets for the 30 Natural monsters
- a Markdown/HTML egg reference table for quick visual lookup
- spreadsheet-derived reference files for islands, monsters, and Wublin blueprints
- curated island documentation generated from spreadsheet data
- raw export previews preserved for audit/debug
- maintenance scripts for inspecting and rebuilding reference material
- placeholder package structure for future vision, rules, and inference code

## Repository layout

```text
assets/
  eggs/                  Local egg/icon image assets

examples/
  screenshots/           Local screenshots for future vision testing

reference/
  eggs/                  Human-readable egg reference
  islands/               Island CSV/JSON/raw export plus curated island docs
  monsters/              Monster CSV/JSON/raw export plus placeholder docs
  wublins/               Wublin blueprint CSV/JSON/raw export plus placeholder docs

scripts/
  build_curated_docs.py  Generate curated Markdown from reference data
  breeding_lookup.py     Look up island-scoped breeding combinations
  guess_breeder_result.py
                         Build screenshot evidence reports for breeder guesses
  inspect_reference_data.py
                         Inspect spreadsheet-shaped JSON exports

src/
  msm_cognition/         Future importable package code
    vision/              Screenshot/icon matching
    rules/               Breeding and game-rule modeling
    inference/           Result-ranking logic
```

## Reference model

The `reference/` directory is the project knowledge base.

Each reference family keeps human and machine views together:

```text
reference/islands/
  islands.csv       Spreadsheet-derived CSV snapshot
  islands.json      Spreadsheet-shaped JSON values
  islands.md        Curated human-readable island status page
  raw-export.md     Raw Markdown export preview for audit/debug
```

The same pattern is used for monsters and Wublins.

This structure keeps the data close to its documentation instead of splitting related files across separate `data/` and `docs/` trees.

## Human-readable reference pages

Useful starting points:

- [`reference/eggs/msm-egg-reference.md`](reference/eggs/msm-egg-reference.md)
- [`reference/islands/islands.md`](reference/islands/islands.md)
- [`reference/monsters/monsters.md`](reference/monsters/monsters.md)
- [`reference/wublins/wublins.md`](reference/wublins/wublins.md)

The curated pages are intended to be readable by humans. Raw exports are intentionally preserved separately and may still look like spreadsheet artifacts.

## Script-facing data

Scripts should read from `reference/*/*.json` or `reference/*/*.csv`.

The current JSON files preserve the spreadsheet export shape:

```json
{
  "sheet": "...",
  "range": "...",
  "values": [
    ["cell", "cell", "cell"]
  ]
}
```

Future normalization can add cleaner script-facing records once the data model stabilizes.

## Scripts

Inspect the spreadsheet-shaped JSON exports:

```bash
python3 scripts/inspect_reference_data.py
```

Regenerate curated island documentation:

```bash
python3 scripts/build_curated_docs.py
```

Some helper scripts use Pillow for image loading, cropping, upscaling, and comparison. Install the current Python dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

After running generators, check for changes:

```bash
git status --short
git --no-pager diff --stat
```

## Planned work

Near-term:

- polish curated island documentation
- generate curated monster and Wublin documentation
- normalize selected reference data into simpler script-facing records
- add breeding-rule lookup data
- add an inference layer for island + parents + timer

Later:

- accept breeder screenshots as input
- crop parent-icon regions
- compare visible icons against local reference assets
- return confidence-ranked parent matches
- combine detected parents with breeding rules and timer data
- report likely breeding outcomes

## Disclaimer

Monster names and images belong to Big Blue Bubble / *My Singing Monsters*.

This is an unofficial personal reference and tooling project. It is not affiliated with or endorsed by Big Blue Bubble.
