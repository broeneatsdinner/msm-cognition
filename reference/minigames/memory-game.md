# Memory Game

A tile-matching minigame opened from a bubble above the castle. Each level is a
board of face-down tiles; flip two at a time and find every pair. It costs
nothing to play.

First played 2026-10-29 on Plant Island in BlueStacks Air.

## Getting there

1. On the island overview, tap the bubble with a brain on it, above the castle.
2. A confirmation asks "Do you want to play the Memory Game?" with no price.
   Tap the green check.

A neighboring bubble over the castle opens a video-ad Spin Wheel offer; that
one is declined with the red X.

## Rules

- There are 9 levels. Each level shows "Mismatches Remaining"; flipping two
  tiles that do not match spends one. A level is cleared when every pair is
  matched.
- A matched pair stays face up. A mismatched pair flips back after a moment.
- The last pair of a level shows that level's prize (XP, food, coins, shards).
- "Prize Tier" at the top right shows a pink monster whose expression
  improves as levels are cleared.
- EXIT, at the bottom right, leaves the game.

What happens when mismatches run out, and what level 9 and the final prize
look like, is not yet recorded.

## Levels seen

| Level | Tiles | Mismatches allowed | Used | Prize shown |
| --- | --- | --- | --- | --- |
| 1 | 4 | 3 | 0 | XP |
| 2 | 6 | 5 | 1 | Food |
| 3 | 12 | 9 | 3 | Coins |
| 4 | 14 | 12 | 3 | Coins |
| 5 | 18 | 14 | 5 | XP |
| 6 | 20 | 15 | 6 | Coins |
| 7 | 22 | 17 | 7 | Shards |
| 8 | 30 | 20 | Finished by the player | Not recorded |

Layouts change from level to level (grids, rows, and scattered shapes), and the
tile faces are monsters, Dipsters, and resources (coins, food, XP, shards).
Rare and Epic variants of a monster are different faces: a Rare Drumpler does
not match a Common Drumpler.

## Strategy

Remember every face seen, and never spend a flip on a face whose partner is
already known.

1. Flip one unseen tile.
2. If its partner is already known, flip the partner: a guaranteed match.
3. Otherwise flip another unseen tile. If the two match, good; if not, both
   faces are now known.
4. If that second tile completes a known pair, match that pair right away
   with the next two flips.
5. Once every face has been seen once, each remaining unseen tile is the
   partner of a known one, so the rest of the level costs no mismatches.

Used this way, mismatches only come from first sightings, and no level so far
needed more than half its allowance.

## Driving it in BlueStacks

- Name tiles by position in the current layout (row and column, or a row
  letter and index) and keep a running list of known faces.
- Take a `zoom` of the board right after each flip, in the same batch,
  before the tile turns back over. A batch of "flip, zoom, flip, zoom" works.
- Tile faces are small; zoom the whole board region at about 0.4 scale to
  tell similar monsters apart (Common vs Rare vs Epic).
- After the last pair, take a screenshot: the prize shows briefly, then the
  next level's board appears on its own.
- If the Mac locks, clicks are refused but the board waits. Take a fresh
  screenshot after unlock to confirm it is unchanged before continuing.
