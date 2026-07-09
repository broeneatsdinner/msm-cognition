# Islands reference

This directory contains island reference material.

## Files

```text
islands.csv       Spreadsheet-derived CSV snapshot
islands.json      Spreadsheet-shaped JSON values
islands.md        Curated human-readable island status page
raw-export.md     Raw Markdown export preview
```

## Human-facing page

`islands.md` is the page intended for normal reading.

It is generated from `islands.csv` by:

```bash
python3 scripts/build_curated_docs.py
```

The curated page is organized as compact status cards rather than preserving the spreadsheet's side-by-side layout.
