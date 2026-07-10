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

Builds a local evidence report from a breeder screenshot, parent egg crops, local egg reference assets, and the structured breeding data.

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
