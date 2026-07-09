# Reference

This directory is the project knowledge base.

Reference material is grouped by subject instead of by file type. Each group can contain:

```text
*.csv        Spreadsheet-derived tabular snapshot
*.json       Spreadsheet-shaped JSON values
*.md         Human-readable reference page
raw-export.md
             Raw Markdown export preview for audit/debug
```

## Reference groups

```text
eggs/       Visual egg/icon reference
islands/    Island status and structure reference
monsters/   Monster reference data
wublins/    Wublin blueprint reference data
```

## Design intent

These files are meant to serve both people and scripts.

Human-facing files should be readable and curated. Machine-facing files should preserve source data clearly enough that future scripts can normalize and reason over it.
