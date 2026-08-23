# MSM Cognition

Visual reference, screenshot recognition, inventory tracking, and breeding
inference for *My Singing Monsters*.

This project starts with a simple question:

> What am I looking at in the breeder, and what is it likely to produce?

The first layer is a human-readable reference system: local egg/icon assets,
curated Markdown pages, spreadsheet-derived reference data, and dated island
inventory files. The next layer uses screenshots, local reference assets,
breeding rules, castle bed audits, availability snapshots, and parent readiness
to produce confidence-ranked recommendations.

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
5. index dated gameplay screenshots into island-scoped inventory YAML
6. audit monster counts against castle bed panels when available
7. compare breeder screenshots against known visual references
8. combine visual recognition, inventory state, availability windows, island context, parent readiness, and timer data to rank likely outcomes

## Current capabilities

The repository currently contains:

- local egg/icon reference assets for the 30 Natural monsters
- a Markdown/HTML egg reference table for quick visual lookup
- spreadsheet-derived reference files for islands, monsters, and Wublin blueprints
- island-scoped player inventory YAML generated into `inventory/README.md`
- castle and monster bed reference data for inventory audits
- screenshot re-indexing rules for Book, Market, castle, pending, and Buyback evidence
- breeding recipe and breedability reference scaffolding used by the inventory planner
- curated island documentation generated from spreadsheet data
- raw export previews preserved for audit/debug
- maintenance scripts for inspecting and rebuilding reference material
- importable inventory generation code plus tests

## Repository layout

```text
assets/
  eggs/                  Local egg/icon image assets

training/
  screenshots/           Reviewed gameplay screenshots and detector inputs
  observations/          Human interpretations tied to screenshots
  corrections/           Recognition and terminology corrections

reference/
  eggs/                  Human-readable egg reference
  islands/               Island CSV/JSON/raw export plus curated island docs
  monsters/              Monster CSV/JSON/raw export plus placeholder docs
  breeding/              Island-scoped breeding and breedability data
  castles/               Castle bed capacity reference
  availability/          Dated limited-time availability snapshots
  wublins/               Wublin blueprint CSV/JSON/raw export plus placeholder docs

inventory/
  islands/               Canonical player inventory YAML, one file per island
  README.md              Generated inventory, castle audit, and planner view
  REINDEXING.md          Screenshot-to-inventory workflow checklist
  SCHEMA.md              Inventory data and generator contract

scripts/
  build_curated_docs.py  Generate curated Markdown from reference data
  breeding_lookup.py     Look up island-scoped breeding combinations
  guess_breeder_result.py
                         Build screenshot evidence reports for breeder guesses
  inspect_reference_data.py
                         Inspect spreadsheet-shaped JSON exports

src/
  msm_cognition/         Importable package code
    inventory.py         Inventory generator, bed audit, and planner join
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

- [`inventory/README.md`](inventory/README.md)
- [`inventory/REINDEXING.md`](inventory/REINDEXING.md)
- [`inventory/SCHEMA.md`](inventory/SCHEMA.md)
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

The canonical player inventory lives under `inventory/islands/*.yaml`. Every
monster row uses a non-negative integer `owned` count. Book screenshots are the
stronger source for discovered state, visible Market cards are the stronger
source for current owned counts, Buyback cards are not current inventory, and
castle bed panels are audits rather than primary monster counters.

## Scripts

Inspect the spreadsheet-shaped JSON exports:

```bash
python3 scripts/inspect_reference_data.py
```

Regenerate curated island documentation:

```bash
python3 scripts/build_curated_docs.py
```

Regenerate the player inventory:

```bash
bin/inventory
```

Check generated inventory and tests:

```bash
bin/inventory --check
python3 -m unittest tests/test_inventory.py
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

- continue indexing unlocked islands from dated screenshot batches
- resolve non-zero castle bed audit deltas with screenshot or user-confirmed evidence
- add missing bed reference data for non-Natural classes such as Magical monsters
- build island roster and availability snapshot data separately from player inventory
- expand breeding recipes to preserve multiple parent combinations and failure timers

Later:

- accept breeder screenshots as input
- crop parent-icon regions
- compare visible icons against local reference assets
- return confidence-ranked parent matches
- combine detected parents with inventory, availability, breeding rules, and timer data
- report likely breeding outcomes and next recommended actions

## Disclaimer

Monster names and images belong to Big Blue Bubble / *My Singing Monsters*.

This is an unofficial personal reference and tooling project. It is not affiliated with or endorsed by Big Blue Bubble.
