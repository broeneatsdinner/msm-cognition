# Scripts

This directory contains repo-maintenance scripts.

These scripts are not the final cognition engine. They maintain and inspect reference material.

## Scripts

```text
inspect_reference_data.py
```

Reads spreadsheet-shaped JSON files from `reference/` and prints row/column summaries.

```text
build_curated_docs.py
```

Generates curated Markdown documentation from reference data. Currently generates:

```text
reference/islands/islands.md
```

```text
breeding_lookup.py
```

Looks up island-scoped breeding combinations from `reference/breeding/common-natural-breeding.json`.

```text
guess_breeder_result.py
```

Builds a local evidence report from a breeder screenshot, local Breeding Structure reference assets, local egg reference assets, and the structured breeding data. Manual parent names supplied with `--parents` are shown separately from the crude automated egg-reference match table.

Manual/debug crop mode:

```bash
python3 scripts/guess_breeder_result.py \
  --mode manual-crops \
  --source examples/screenshots/plant-island.png \
  --island "Plant Island" \
  --crop-breeder 100,200,300,300 \
  --crop-left-egg 130,220,70,70 \
  --crop-right-egg 250,220,70,70 \
  --parents Noggin Maw \
  --out examples/evidence/manual-test
```

Detector mode:

```bash
python3 scripts/guess_breeder_result.py \
  --mode detect-breeders \
  --source examples/screenshots/plant-island.png \
  --island "Plant Island" \
  --max-candidates 2 \
  --structure-match-threshold 0.80 \
  --structure-min-width 120 \
  --structure-min-height 120 \
  --out examples/evidence/detect-test
```

Detector mode uses OpenCV template matching against `assets/structures/breeding-structure/*.webp`, then crops likely parent egg regions inside each detected Breeding Structure. By default, only `normal-breeding-structure.webp` and `enhanced-breeding-structure.webp` are active. Locked templates are opt-in with `--allow-locked-templates`; Paironormal templates are excluded by default unless the island name contains `Paironormal`, and can be enabled with `--allow-paironormal-templates`. Paironormal locked templates require both the Paironormal family and locked templates to be allowed. `--structure-min-width` and `--structure-min-height` reject tiny scaled template matches before they can become candidates. Zero candidates can be a correct conservative result. The automated egg matches are evidence for review, not authoritative recognition.

Parent crop tuning example:

```bash
python3 scripts/guess_breeder_result.py \
  --mode detect-breeders \
  --source examples/screenshots/plant-island.png \
  --island "Plant Island" \
  --left-parent-rel 0.20,0.06,0.22,0.22 \
  --right-parent-rel 0.58,0.06,0.22,0.22 \
  --out examples/evidence/parent-crop-tuning
```

The relative parent crop boxes are fractions inside each detected Breeding Structure candidate and should be tuned from confirmed training examples.

Detector output can be promoted into `training/evidence/` when it captures a useful success, false positive, missed detection, or parent crop correction. Annotate the report's `training_review` block instead of treating the output as disposable.

## Typical workflow

```bash
python3 scripts/inspect_reference_data.py
python3 scripts/build_curated_docs.py
python3 scripts/breeding_lookup.py --monster T-Rox --island "Plant Island"
git status --short
```

## Python requirements

Some helper scripts use third-party Python packages.

Install them with:

```bash
python3 -m pip install -r requirements.txt
```

Current external dependencies:

- Pillow — image loading, cropping, upscaling, and comparison helpers

The scripts expect Python 3.
