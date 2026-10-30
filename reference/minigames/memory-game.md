# Memory Game

A tile-matching minigame opened from a bubble above the castle. Each level is a
board of face-down tiles; flip two at a time and find every pair. It costs
nothing to play.

First played 2026-10-29 on Plant Island in BlueStacks Air.

## Getting there

1. On the island overview, tap the bubble with a brain on it, above the castle.
2. A confirmation asks "Do you want to play the Memory Game?" with no price.
   Tap the green check. The first play of the day was free; on 2026-10-29 the
   player paid 2 diamonds for a second play the same day.

A neighboring bubble over the castle opens a video-ad Spin Wheel offer; that
one is declined with the red X.

## Rules

- There are 9 levels. Each level shows "Mismatches Remaining"; flipping two
  tiles that do not match spends one. A level is cleared when every pair is
  matched, and the next board appears on its own.
- A matched pair stays face up. A mismatched pair flips back after a moment.
- The last pair of a level shows that level's prize (XP, food, coins, shards,
  or diamonds).
- "Prize Tier" at the top right shows a pink monster whose expression
  improves as levels are cleared.
- After level 9, a GAME OVER screen shows a "Rewards Recap" grid of the nine
  level prizes. EXIT leaves it.
- EXIT, at the bottom right, leaves the game at any time.

What happens when mismatches run out is not yet recorded; no run has come
close.

## Levels seen

Board sizes and mismatch allowances were the same on both runs; layouts were
mostly the same, but level 2 changed shape and tile faces and prizes change
every play.

| Level | Tiles | Mismatches allowed | Run 1 used | Run 2 used | Run 2 prize |
| --- | --- | --- | --- | --- | --- |
| 1 | 4 | 3 | 0 | 1 | 2,300 XP |
| 2 | 6 (run 1), 12 (run 2) | 5 (run 1), 9 (run 2) | 1 | 2 | 1 diamond |
| 3 | 12 | 9 | 3 | 4 | 9 shards |
| 4 | 14 | 12 | 3 | 3 | 23,000 XP |
| 5 | 18 | 14 | 5 | 6 | 8,800 food |
| 6 | 20 | 15 | 6 | 5 | 8,800 food |
| 7 | 22 | 17 | 7 | 5 | 230,000 XP |
| 8 | 26 | 20 | Finished by the player | 8 | 44,000 food |
| 9 | 30 | 23 | Not reached | 10 | 230,000 XP |

Run 1 was 2026-10-29 (first, free play); run 2 the same day (2-diamond play),
cleared all nine levels with 44 mismatches used out of 118 allowed. Prize
amounts are from the Rewards Recap
(`training/screenshots/2026-10-29-memory-game-rewards-recap.jpeg`).

Tile faces are monsters, Dipsters, and resources (coins, food, XP, shards,
diamonds). Rare and Epic variants of a monster are different faces: a Rare
Drumpler does not match a Common Drumpler, and a white Bowgart does not match
a blue one.

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
needed more than half its allowance. A full nine-level run used 44 of 118.

## Driving it in BlueStacks

- Name tiles by position in the current layout (row and column, or a row
  letter and index) and keep a running list of known faces.
- Take a `zoom` of the board right after each flip, in the same batch,
  before the tile turns back over. A batch of "flip, zoom, flip, zoom" works.
- Tile faces are small; zoom the whole board region at about 0.4 scale to
  tell similar monsters apart (Common vs Rare vs Epic).
- After the last pair, take a screenshot: the prize shows briefly, then the
  next level's board appears on its own.
- When an unseen tile turns out to pair with a known tile but was flipped as
  the second tile of a mismatch, it flips back; spend the next two flips on
  that known pair right away, while its position is fresh.
- Clicks wait for a pause while the player types elsewhere; that only slows
  the run, it does not break it.
- If the Mac locks, clicks are refused but the board waits. Take a fresh
  screenshot after unlock to confirm it is unchanged before continuing.
