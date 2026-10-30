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

## Is a replay worth it?

Usually not, if diamonds matter. The paid replay on 2026-10-29 cost 2 diamonds
and a full nine-level clear returned only 1 diamond, along with about 485,000
XP, 61,600 food, and 9 shards. Prizes are drawn per play, so a replay may return
no diamonds at all. Play the free daily game; do not suggest paying for a
replay unless the player wants the XP, food, or shards more than the diamonds.

## Strategies

Three strategies are named so runs can be compared. Strategy 1 has been played;
Strategies 2 and 3 are the player's proposals, not yet tried by an agent.

| | Strategy 1: match as you go | Strategy 2: sweep, then match | Strategy 3: sweep into one map |
| --- | --- | --- | --- |
| Flips | One unseen tile, then its known partner or another unseen tile | Tiles in reading order, two at a time | Same as Strategy 2 |
| Looks | After every flip | After every pair of flips | After every pair, then one combined map |
| Mismatches | Only first sightings; 44 of 118 on the full run | About half the tiles minus lucky pairs; fits every level seen | Same as Strategy 2 |
| Agent round trips | About one per one or two flips | About three per level | About three per level, plus building the map |

### Strategy 1: match as you go

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

The cost is on the agent side: each flip depends on the face just seen, so
nearly every flip is its own tool call with its own image. The nine-level run
took roughly 150 calls.

### Strategy 2: sweep, then match (the player's method)

1. Flip tiles in reading order two at a time (1 and 2, 3 and 4, ...) and take a
   screenshot after each pair, before the mismatched pair flips back. Adjacent
   tiles that happen to match stay face up for free.
2. When every tile has been seen, read the screenshots, list the pairs, and
   flip each pair.

Mismatches: at most half the tiles. Every level seen fits with room to spare
(level 9: 30 tiles, at most 15 mismatches, 23 allowed). The matching phase
costs none.

For an agent, the sweep does not depend on what it sees, so a whole level can
be one batch (flip, flip, zoom, repeated), then one reasoning step, then one
batch of all the pairs: about three calls per level instead of twenty or more.

### Strategy 3: sweep into one map

Strategy 2's sweep, but the faces are written into a single board map (a text
grid of names, or one image made by cropping each revealed tile out of the
sweep screenshots) before matching. It costs a little more work than Strategy
2 but makes the comparison less error-prone, which matters most for
look-alikes such as Common, Rare, and Epic variants.

### Open questions

- Whether unused mismatches affect anything (the prize tier or prizes). If
  they do not, Strategy 1's lower mismatch count has no in-game value and
  Strategies 2 and 3 win on cost.
- Whether flips sent back-to-back in one batch land reliably while a
  mismatched pair is still flipping back.

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
