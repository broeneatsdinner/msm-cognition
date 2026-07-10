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

```text
run_breeder_detector_experiments.py
```

Runs a balanced sweep of detector thresholds, minimum candidate sizes, template sets, and maximum candidate counts against one screenshot. Every experiment gets its own full detector report, original and 4x Breeding Structure crops, parent egg crops, and wider source-context crops with the candidate box visibly outlined. The output root also gets a Markdown comparison table and a large, labeled context contact sheet for quick visual review.

Use `--limit` for a fast initial pass. Limited runs are ordered to sample all configuration dimensions early; omit it to run the full sweep. Paironormal templates are included as a separate template set only when the island name contains `Paironormal`.

Only clean `.webp` structure assets may be used as detector or scoring references. Human-annotated images are visual guidance only: files named as annotated, marked, notes, human markup, guides, or guidance are excluded from reference scoring and must not be used as detector templates. Raw capture folders such as `breeding-structure-grabs/` are not ingested automatically.

```bash
python3 scripts/run_breeder_detector_experiments.py \
  --source training/screenshots/2026-07-09-world-overview-mirror-cold-island.png \
  --island "Mirror Cold Island" \
  --parents Mammott Tweedle \
  --out training/evidence/experiments/mirror-cold-breeder-sweep \
  --limit 50
```

Review `experiment-summary.md` and `contact-sheet.png` first, then open an experiment's `report.md` for all candidates and parent evidence. The summary clusters recurring candidate boxes so repeated false positives can be annotated once. Human labels live in `annotations.json`; reruns preserve those labels, update occurrence metadata, add new detector clusters as `needs_review`, and keep a `breeding_structure` placeholder until a human supplies the real box.

Each detector candidate retains its raw OpenCV template score and also receives a non-definitive breeder-likeness score for ranking. The second-stage score combines masked HSV color similarity, multi-scale edge layout, silhouette/masked shape similarity, local candidate-versus-surroundings separation, and soft world-view size/edge sanity, then subtracts visual-similarity and box-overlap penalties from confirmed false-positive annotations. The summary and per-experiment reports show every component so a human can see why a candidate moved up or down.

Experiment output is generated training evidence; leave it untracked unless it has been deliberately reviewed and selected for promotion.

```text
summarize_detector_training.py
```

Summarizes breeder detector evidence reports from `training/evidence/**/report.md`.

```bash
python3 scripts/summarize_detector_training.py
python3 scripts/summarize_detector_training.py --out training/evidence/detector-training-summary.md
```

## Typical workflow

```bash
python3 scripts/inspect_reference_data.py
python3 scripts/build_curated_docs.py
python3 scripts/breeding_lookup.py --monster T-Rox --island "Plant Island"
python3 scripts/summarize_detector_training.py
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
- OpenCV — Breeding Structure template matching

The scripts expect Python 3.
