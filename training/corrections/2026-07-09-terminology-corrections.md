# Correction: Terminology and Visible UI Classification

## Treats, not food

The feeding resource should be called `treats`, matching in-game terminology.

Do not model it as `food`.

```yaml
account:
  treats: 55928
```

## Top-left 130/205 meter

The visible `130/205` top-left value should not be called `likes`.

Until the specific mechanic is understood and modeled, record it neutrally:

```yaml
visible_ui:
  top_left_meter: "130/205"
  classification: visible_but_unmodeled
```

## Principle

Use in-game language wherever the game provides a known term. For ambiguous UI elements, record the visible fact without assigning unsupported meaning.
