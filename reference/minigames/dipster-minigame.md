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
- Observed: small rock piles clear with one dig, so they cost two tokens in
  total (one to clear, one to reveal). The big boulder on level 6 r0 c0 took
  two digs to clear, so three tokens in total. Rocks can hide Dipsters
  (levels 3 to 6 each had one under a rock).

Observed behavior:

- A revealed empty tile shows a number: how many Dipsters are in its 8
  neighbors (orthogonal and diagonal). Every reveal so far has matched this.
  A tile with no Dipster neighbors stays blank dirt with no number (level 9
  r4 c0); pass it to the solver as `=0`.
- The bar at the bottom shows Dipsters found over Dipsters hidden, for example
  `2/7`.
- The token count is in the top-right corner. The green `+` beside it buys
  tokens; never tap it.
- After the last Dipster, "A ProDIGious Find!" shows the level prize with "Tap
  to redeem". Any sticker packs won during the level come next (tap to open,
  tap to continue), then a NEXT LEVEL button.
- Board progress was unchanged when play resumed later the same day.
- The game sometimes reveals a number on its own when a Dipster is found
  (level 3 showed r3 c0 and r2 c1 without a token being spent). On level 6 it
  also revealed a Dipster on its own (r4 c4), so after any surprise jump in
  the found count, re-read the whole board before the next solver run.
  Levels 8 and 9 did the same: one dig on level 9 went from `5/8` to `7/8`,
  and level 8's second dig also revealed r1 c0 and three numbers.
- On level 10 the dig on r1 c2 revealed r2 c2 and also removed the rocks on
  r0 c2 and r1 c3 with no token spent. Why is not known, so re-read the rocks
  as well after any surprise reveal.

Rewards seen for revealing a Dipster: `+7,800` or `+9,000` food,
`+1,100` purple crystals (the last Dipster of level 7),
`+750,000` or `+850,000` coins,
`+750,000` XP, about `+150,000` XP, sticker packs, `+5` minigame tokens
(token icon), and `+5` with a blue star icon (not tokens; not yet identified).
A token reward can extend a run, so keep the token count in view.

## Levels seen

| Level | Board | Dipsters | Obstacles | Tokens used | Prize |
| --- | --- | --- | --- | --- | --- |
| 1 | 4x4 | 3 | None | 8 | Mi (Tonal Dipster) and a sticker pack |
| 2 | 5x5 | 7 | None | 12 | Terrene Sol and a sticker pack |
| 3 | 5x5 | 7 | Rocks on r4 c3 and r4 c4 | 16 | Re (Tonal Dipster) |
| 4 | 5x5 | 7 | Rocks on r1 c0 to r3 c0 | 14 | Waxen La |
| 5 | 5x5 | 7 | Rocks on r0 c1 and r0 c4 | 15 | Re and a sticker pack |
| 6 | 6 rows x 5 columns | 7 | Boulder on r0 c0, rocks on r1 c0 and r5 c0 | 17 | Re and 3 sticker packs |
| 7 | 6 rows x 5 columns | 7 | Boulder on r1 c0, rocks on r1 c1 and r5 c1 | 17 | Mi |
| 8 | 6 rows x 5 columns | 7 | Boulder on r0 c0, rocks on r2 c2 and r3 c0 | 10 | Fa and 2 sticker packs |
| 9 | 6 rows x 5 columns | 8 | Boulder on r0 c3, rocks on r1 c2, r3 c0, r4 c4 and r5 c3 | 13 | Terrene Sol and 2 sticker packs |
| 10 | 6 rows x 5 columns | 8 | Boulder on r2 c0, rocks on r0 c2, r1 c3, r1 c4 and r5 c4 | 2 so far (2/8) | In progress |

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
2. After every reveal, run the solver with every revealed tile and every rock
   still standing:

    ```bash
    python3 scripts/dipster_solver.py --size 5 --dipsters 7 --rock 0,1 --rock 0,0=2 "2,2=2" "0,3=D"
    ```

    - For a board that is not square, pass `--rows 6 --columns 5` instead of
      `--size`.
    - `--rock ROW,COLUMN=DIGS` gives the digs a rock still needs before a
      further dig reveals the tile: 1 for a small pile (the default), 2 for a
      boulder. After a dig that only shrinks a rock, lower its count; once the
      rock is gone, drop the flag.
3. Dig the tile on the solver's `Next dig:` line. The solver prints each
   hidden tile's chance of holding a Dipster, then picks the dig:
    - When at most 200 layouts fit (`--lookahead-limit` changes this), it
      plans ahead over every layout and picks the dig with the lowest
      expected tokens to finish the level, counting rock digs. It may pick a
      safe tile whose number splits the layouts over a likely Dipster: a
      Dipster it is sure of can wait until the end, since digging it teaches
      nothing.
    - Above that, it picks the best chance per token, and among ties the
      tile touching the most undecided tiles.
4. `Certain Dipsters:` lists tiles at `1.00`. Dig them whenever convenient;
   the order does not change the cost.

The plan lowers the average, not every game. At level 6's `6/7` (one
Dipster among 10 tiles, 3 of them rocks) it expects 3.5 tokens to finish, but
on the real board, with the Dipster under the boulder, its route costs 7; the
route played by hand cost 6.

Level 2 shows the payoff: 12 tokens for 7 Dipsters, with only 5 tokens spent
on empty tiles.

## Current progress

As of 2026-11-04: level 10, `2/8` found, tokens 0. Rows and columns count
from the top corner of the diamond (row runs down-left, column runs
down-right). Resume with:

```bash
python3 scripts/dipster_solver.py --rows 6 --columns 5 --dipsters 8 --rock 2,0=2 --rock 1,4 --rock 5,4 "1,1=3" "1,2=D" "2,2=D"
```

- The boulder on r2 c0 and the rocks on r1 c4 and r5 c4 still stand. The
  rocks on r0 c2 and r1 c3 are gone, but those tiles are still hidden.
- The 35 tokens of 2026-11-04 found 22 Dipsters: the last 5 of level 7, all
  of levels 8 and 9, and 2 on level 10. Rock digs took 2 of the 35.

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
    - 6-row x 5-column board: `x = 860 + 71.3 * (c - r)`,
      `y = 251 + 35.35 * (r + c + 1)`. Levels 6 to 10 all use it.
    - Re-derive from the board's four corners if the layout changes.
- The full-size `app_screenshot` frame can differ from the scaled one (one
  session returned a 1728x986 frame, then 1456x831). Read the frame size
  reported with each screenshot and re-derive tile centers if it changed.
- Tap through sticker packs one tap per call: taps sent while a pack is
  still animating are dropped. SKIP ALL at about (60, 780) clears the rest in
  one tap, but its stickers are not shown, so whether they were granted was
  not checked.
- A tap sent straight after a Dipster's reveal can be dropped too (a rock on
  level 7, no token lost). Check the token count before assuming a dig landed.
- Tutorial dialogs advance with the green arrow at about (1240, 765).
- INFO (bottom right) shows the rules; EXIT leaves the minigame. On the
  sticker screen, SKIP and SKIP ALL replace those buttons.
- Getting there: on 2026-10-29 the game reloaded and opened straight onto this
  minigame. The usual route in from an island is not yet recorded.
- General BlueStacks navigation (Book, Market, castle panel) is in
  `inventory/BLUESTACKS-WORKFLOW.md`.
