# Dipster minigame

A Halloween-themed event minigame. It is shaped like Minesweeper, but the
hidden Dipsters are the targets, not hazards. The in-game screen does not show
the minigame's name.

First observed 2026-10-29 in BlueStacks Air. Event timer then read `10d 14h`.

## Rules

From the in-game INFO panel ("How it works"):

1. Spend one Minigame Token to reveal one tile.
2. Each reveal earns a discovery reward. Each Dipster grants a unique reward.
3. Find all hidden Dipsters on the board to win a Top Prize and finish the
   level.

From the level 3 tutorial (Alcordion):

- Rocks are obstacles that take multiple digs to clear; the bigger the rock,
  the more digs. Once a rock is cleared, digging continues as normal.
- Observed: every rock so far cleared with one dig (one token), so a rock
  tile costs two tokens in total: one to clear, one to reveal. Rocks can hide
  Dipsters (levels 3 and 4 each had one under a rock).

Observed behavior:

- A revealed empty tile shows a number: how many Dipsters are in its 8
  neighbors (orthogonal and diagonal). Every reveal so far has matched this.
- The bar at the bottom shows Dipsters found over Dipsters hidden, for example
  `2/7`.
- The token count is in the top-right corner. The green `+` beside it buys
  tokens; never tap it.
- After the last Dipster, "A ProDIGious Find!" shows the level prize with "Tap
  to redeem". Any sticker packs won during the level come next (tap to open,
  tap to continue), then a NEXT LEVEL button.
- Board progress was unchanged when play resumed later the same day.
- The game sometimes reveals a number on its own when a Dipster is found
  (level 3 showed r3 c0 and r2 c1 without a token being spent).

Rewards seen for revealing a Dipster: `+7,800` food, `+750,000` coins,
`+750,000` XP, about `+150,000` XP, sticker packs, `+5` minigame tokens
(token icon), and `+5` with a blue star icon (not tokens; not yet identified).
A token reward can extend a run, so keep the token count in view.

## Levels seen

| Level | Board | Dipsters | Obstacles | Tokens used | Prize |
| --- | --- | --- | --- | --- | --- |
| 1 | 4x4 | 3 | None | 8 | Mi (Tonal Dipster) and a sticker pack |
| 2 | 5x5 | 7 | None | 12 | Terrene Sol and a sticker pack |
| 3 | 5x5 | 7 | Rocks on r4 c3 and r4 c4 | 16 | Re (Tonal Dipster) |
| 4 | 5x5 | 7 | Rocks on r1 c0 to r3 c0 | 13 so far, 6/7 | Not finished |

Possible prizes listed on the TOP PRIZES `i` panel: Superno-Fa, Dipsters
(Royal), Dipsters (Elemental), Zworaffe (Decoration), Dipsters (Tonal),
Legendary Sticker Packs, Epic Sticker Packs, Clubbox Tickets.

## Strategy

The goal is to hit Dipsters with as few tokens as possible.

Hard rule, at any effort level: never dig a tile without running the solver
first, and before each run re-check the solver input against a fresh
screenshot (every number, Dipster, and rock). A guess by eye or a misread
number costs a token. The only exception is the first tile of a new level.

1. Open the center tile first. Its number covers the most neighbors.
2. After every reveal, run the solver with every revealed tile:

    ```bash
    python3 scripts/dipster_solver.py --size 5 --dipsters 7 "2,2=2" "0,3=D"
    ```

    It counts the layouts that fit every number and prints each hidden tile's
    chance of holding a Dipster.
3. Reveal the tile with the highest chance. Among ties, pick the one whose
   number would tell the most about other hidden tiles (it touches more of
   them).
4. When the solver shows `1.00`, reveal those tiles directly.
5. Rock tiles cost two tokens (dig, then reveal). Compare a rock tile's
   chance divided by two with the best plain tile's chance, and take the
   better value per token. The solver treats rocks as ordinary hidden tiles.

Level 2 shows the payoff: 12 tokens for 7 Dipsters, with only 5 tokens spent
on empty tiles.

## Current progress

As of 2026-10-29: level 4, `6/7` found, tokens 0. The last Dipster is
certainly on r1 c0.

Board, rows and columns counted from the top corner of the diamond (row runs
down-left, column runs down-right).

| | c0 | c1 | c2 | c3 | c4 |
| --- | --- | --- | --- | --- | --- |
| r0 | 1 | 0.00 | 1 | 0.00 | 0.00 |
| r1 | 1.00, maybe rock | 0.00 | 0.00 | Dipster | 0.00 |
| r2 | 0.00 rock | 0.00 | 2 | 0.00 | 1 |
| r3 | Dipster | 4 | Dipster | 0.00 | 0.00 |
| r4 | Dipster | Dipster | 3 | Dipster | 0.00 |

Solver input to confirm:

```bash
python3 scripts/dipster_solver.py --size 5 --dipsters 7 "2,2=2" "2,4=1" "0,2=1" "4,2=3" "4,1=D" "4,3=D" "3,1=4" "3,2=D" "4,0=D" "1,3=D" "3,0=D" "0,0=1"
```

Next move: tap r1 c0. If a rock still covers it, the first tap clears the
rock and a second tap reveals the Dipster. Screenshot first to confirm the
board still matches.

## Evidence

Screenshots in `training/screenshots/`:

- `2026-10-29-dipster-minigame-level-2-01-start.jpeg`: level 2 at `1/7` with
  15 tokens.
- `2026-10-29-dipster-minigame-level-2-02-six-found.jpeg`: level 2 at `6/7`.
- `2026-10-29-dipster-minigame-level-2-03-cleared.jpeg`: level 2 at `7/7`.
- `2026-10-29-dipster-minigame-level-3-01-paused.jpeg`: level 3 at `2/7`
  with 0 tokens.
- `2026-10-29-dipster-minigame-level-3-02-cleared.jpeg`: level 3 at `7/7`.
- `2026-10-29-dipster-minigame-level-4-01-paused.jpeg`: level 4 at `6/7`
  with 0 tokens; matches the progress table above.

## Driving it in BlueStacks Air

- Use the background computer-use tools (`app_screenshot`, `app_batch`) on
  BlueStacks; the game has no accessibility elements, so tap by coordinate.
- Screenshot after every reveal and zoom on the new tile to read its number.
  Dipster figures are drawn taller than their tile; their base sits on the
  tile center.
- Tile centers in the 1456x831 frame:
    - 4x4 board: `x = 915 + 100 * (c - r)`, `y = 331 + 49 * (r + c)`.
    - 5x5 board: `x = 795 + 80 * (c - r)`, `y = 268 + 39.8 * (r + c + 1)`.
    - Re-derive from the board's four corners if the layout changes.
- The full-size `app_screenshot` frame can differ from the scaled one (one
  session returned a 1728x986 frame, then 1456x831). Read the frame size
  reported with each screenshot and re-derive tile centers if it changed.
- Tutorial dialogs advance with the green arrow at about (1240, 765).
- INFO (bottom right) shows the rules; EXIT leaves the minigame. On the
  sticker screen, SKIP and SKIP ALL replace those buttons.
- Getting there: on 2026-10-29 the game reloaded and opened straight onto this
  minigame. The usual route in from an island is not yet recorded.
- General BlueStacks navigation (Book, Market, castle panel) is in
  `inventory/BLUESTACKS-WORKFLOW.md`.
