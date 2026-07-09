# Corrections

This directory stores user corrections and recognition lessons.

Corrections are first-class training material. If the assistant misidentifies an island, misnames a resource, or assigns meaning to an unmodeled UI element, the correction should be recorded here.

## Example correction pattern

```text
Issue:
The assistant identified Plant Island as Cold Island.

Correction:
The screenshot was Plant Island.

Recognition lesson:
Do not infer island identity from castle/state similarity. Require user confirmation, visible UI text, or distinctive terrain/context.
```
