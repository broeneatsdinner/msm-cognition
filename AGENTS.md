# Agent notes

Start with `README.md` for what this project is.

## Where things live

- `inventory/islands/*.yaml`: the player's island inventories. Edit these, then
  run `bin/inventory` to regenerate `inventory/README.md` and the island pages.
- `inventory/SCHEMA.md`: the YAML shape and the castle bed audit.
- `inventory/REINDEXING.md`: how screenshots and other evidence become YAML.
- `inventory/BLUESTACKS-WORKFLOW.md`: how to read the Book, Market, and castle
  panel directly in BlueStacks with computer use.
- `reference/minigames/dipster-minigame.md`: rules, strategy, and current
  progress for the Dipster minigame, with `scripts/dipster_solver.py`.
- `reference/minigames/memory-game.md`: rules, level table, and matching
  strategy for the castle's Memory Game.
- `training/screenshots/`: dated evidence screenshots cited by the YAML notes.

## Working rules

- Never spend coins, diamonds, keys, or tokens in the game unless the player
  asks. Close purchase and ad prompts with the red X.
- The player confirms which island is shown when the screen does not say.
- Show the YAML diff and the bed audit change before committing inventory
  updates.
- Run the tests after changing inventory or code:
  `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`.
- Keep tests from pinning live counts; they should check behavior relative to
  whatever the YAML holds.
