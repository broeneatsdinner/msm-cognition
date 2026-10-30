# Dipster minigame

A Halloween-themed event minigame. It is shaped like
Minesweeper, but the hidden Dipsters are the targets, not hazards. The in-game
screen does not show the minigame's name.

Observed 2026-10-29 in BlueStacks Air. Event timer then read `10d 14h`.

## Rules

From the in-game INFO panel ("How it works"):

1. Spend one Minigame Token to reveal one tile.
2. Each reveal earns a discovery reward. Each Dipster grants a unique reward.
3. Find all hidden Dipsters on the board to win a Top Prize and finish the
   level.

Observed behavior:

- A revealed empty tile shows a number: how many Dipsters are in its 8
  neighbors (orthogonal and diagonal). The numbers matched this rule on every
  reveal so far.
- A revealed Dipster shows its monster or a tombstone and pays `+7,800` food
  (both Dipsters found that way paid the same).
- The bar at the bottom shows Dipsters found over Dipsters hidden, for example
  `1/7`.
- The token count is in the top-right corner. The green `+` beside it buys
  tokens; never tap it.
- After the last Dipster, "A ProDIGious Find!" shows the level prize with "Tap
  to redeem", then a sticker pack (if awarded), then a NEXT LEVEL button.

## Levels seen

| Level | Board | Dipsters | Tokens used | Prize |
| --- | --- | --- | --- | --- |
| 1 | 4x4 | 3 | 8 | Mi (Tonal Dipster) and a sticker pack |
| 2 | 5x5 | 7 | 2 so far | Not finished |

Possible prizes listed on the TOP PRIZES `i` panel: Superno-Fa, Dipsters
(Royal), Dipsters (Elemental), Zworaffe (Decoration), Dipsters (Tonal),
Legendary Sticker Packs, Epic Sticker Packs, Clubbox Tickets.

## Strategy

The goal is to hit Dipsters with as few tokens as possible.

1. Open a center tile first. Its number covers the most neighbors.
2. Split the unknown tiles into groups by which numbers they touch, and count
   the layouts that satisfy every number. A tile's chance is the share of
   layouts that put a Dipster on it.
3. Reveal the tile with the highest chance. Prefer, among equal chances, the
   one whose number would split the remaining layouts most evenly.
4. Once only one layout fits, reveal its Dipsters directly.

Level 1 worked this way: center tiles showed `1` and `2`, two edge tiles showed
`2` and `1`, which left three layouts. One reveal hit a Dipster, one more number
picked the layout, and the last two reveals were both Dipsters.

## Current progress

As of 2026-10-29: level 2, tokens 0.

Level 2 board, rows and columns counted from the top corner of the diamond
(row runs down-left, column runs down-right):

| | c0 | c1 | c2 | c3 | c4 |
| --- | --- | --- | --- | --- | --- |
| r0 | ? | ? | Dipster | ? | ? |
| r1 | ? | ? | ? | ? | ? |
| r2 | ? | ? | 1 | ? | ? |
| r3 | ? | ? | ? | ? | ? |
| r4 | ? | ? | ? | ? | ? |

What this means for the next tokens:

- The center `1` puts exactly one Dipster among the 8 tiles around it, and none
  of those 8 is the Dipster at r0 c2.
- The other 5 hidden Dipsters are among the remaining 15 outer-ring tiles,
  about 33% each, against 12.5% for a tile next to the center.
- Keep revealing outer-ring tiles. Tiles next to r0 c2 (r0 c1, r0 c3) are not
  favored by anything yet; numbers from new reveals should drive the next
  choice.
- Recheck the board from a screenshot before playing: the game may reset or
  reshuffle between sessions.

## Driving it in BlueStacks Air

- Use the background computer-use tools (`app_screenshot`, `app_batch`) on
  BlueStacks; the game has no accessibility elements, so tap by coordinate.
- Screenshot after every reveal and zoom on the new tile to read its number.
- Tile centers in the 1456x831 frame:
    - 4x4 board: `x = 915 + 100 * (c - r)`, `y = 331 + 49 * (r + c)`.
    - 5x5 board: `x = 795 + 80 * (c - r)`, `y = 270 + 39.7 * (r + c + 1)`.
    - Re-derive from the board's four corners if the layout changes.
- INFO (bottom right) shows the rules; EXIT leaves the minigame.
- Getting there: on 2026-10-29 the game reloaded and opened straight onto this
  minigame. The usual route in from an island is not yet recorded.
