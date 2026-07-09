# Correction: Plant Island Misidentified as Cold Island

## Issue

During initial screenshot intake, the assistant identified a main island screenshot as Cold Island.

## User correction

The user corrected the island identity:

> First of all it's Plant Island.

## Corrected interpretation

The screenshot should be treated as Plant Island.

```yaml
island:
  name: Plant Island
  confirmed_by: user_correction
  confidence: high_after_correction
```

## Recognition lesson

Do not infer island identity from castle/state similarity or from conversational momentum.

Future screenshot intake should require one of:

- user-provided island name
- visible island name in the UI
- distinctive terrain or base shape
- distinctive structures or island context
- explicit capture workflow

If the island name is not visible and not user-confirmed, mark island identity as uncertain.

## Write-discipline lesson

A screenshot-derived update should separate:

```text
Observed       Visible facts in the screenshot
Uncertain      Plausible but untrusted observations
Interpreted    Game mechanics inferred from visible facts
Proposed       Safe state update, if any
```

Do not silently convert uncertain visual guesses into repo state.
