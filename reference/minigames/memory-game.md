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
3. Tapping the castle, then MEMORY in its action bar, can also start a game.
   On 2026-10-30 that went straight to the level 1 board with no
   confirmation, and the diamond count went from 176 to 174. Treat MEMORY as
   spending diamonds once the free play is used: tap it only when the player
   has agreed to pay.

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

Board sizes and mismatch allowances were the same on every run; layouts were
mostly the same, but level 2 changed shape and tile faces and prizes change
every play.

| Level | Tiles | Mismatches allowed | Run 1 used | Run 2 used | Run 2 prize | Run 3 used | Run 3 prize |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4 | 3 | 0 | 1 | 2,300 XP | 2 | 9 shards |
| 2 | 6 (runs 1, 3), 12 (run 2) | 5 (runs 1, 3), 9 (run 2) | 1 | 2 | 1 diamond | 3 | 2,300 XP |
| 3 | 12 | 9 | 3 | 4 | 9 shards | 4 | 900 food |
| 4 | 14 | 12 | 3 | 3 | 23,000 XP | 7 | 96 shards |
| 5 | 18 | 14 | 5 | 6 | 8,800 food | 9 | 1 key |
| 6 | 20 | 15 | 6 | 5 | 8,800 food | 10 | 900 food |
| 7 | 22 | 17 | 7 | 5 | 230,000 XP | 10 | 3 keys |
| 8 | 26 | 20 | Finished by the player | 8 | 44,000 food | Finished by the player | 362,000 coins |
| 9 | 30 | 23 | Not reached | 10 | 230,000 XP | Finished by the player | 44,000 food |

Run 1 was 2026-10-29 (first, free play); run 2 the same day (2-diamond play),
cleared all nine levels with 44 mismatches used out of 118 allowed. Run 3 was a
second 2-diamond replay that day, played with Strategy 2 through level 7 (45
mismatches out of 75 allowed on those levels); the player finished levels 8
and 9. Prize amounts are from the Rewards Recaps
(`training/screenshots/2026-10-29-memory-game-rewards-recap.jpeg` for run 2,
`training/screenshots/2026-10-29-memory-game-run-3-rewards-recap.jpeg` for
run 3), which list the nine level prizes in reading order.

Run 4 was a 2-diamond replay on 2026-10-30, played by an agent through all
nine levels. It was meant as Strategy 3 but was played as Strategy 2 with a
written map (see Strategy 3 below). Level 2 was the 6-tile board again.
Prizes are from
`training/screenshots/2026-10-30-memory-game-run-4-rewards-recap.jpeg`.

| Level | Tiles | Mismatches allowed | Run 4 used | Run 4 prize |
| --- | --- | --- | --- | --- |
| 1 | 4 | 3 | 2 | 36,200 coins |
| 2 | 6 | 5 | 3 | 36,200 coins |
| 3 | 12 | 9 | 6 | 2,300 XP |
| 4 | 14 | 12 | 6 | 8,800 food |
| 5 | 18 | 14 | 9 | 96 shards |
| 6 | 20 | 15 | 10 | 8,800 food |
| 7 | 22 | 17 | 11 | 362,000 coins |
| 8 | 26 | 20 | 13 | 44,000 food |
| 9 | 30 | 23 | 15 | 2,300 shards |

Run 4 used 75 of 118 mismatches. Level 8 is two full rows of ten with three
rows of edge pairs below; level 9 is five rows of six with gaps (a ragged
grid, 30 tiles).

Run 5 was the free daily play on 2026-10-31, played by an agent with
Strategy 3 through all nine levels. Level 2 was the 6-tile board. Prizes are
from `training/screenshots/2026-10-31-memory-game-run-5-rewards-recap.jpeg`.

| Level | Tiles | Mismatches allowed | Run 5 used | Run 5 prize |
| --- | --- | --- | --- | --- |
| 1 | 4 | 3 | 0 | 900 food |
| 2 | 6 | 5 | 0 | 9 shards |
| 3 | 12 | 9 | 5 | 36,200 coins |
| 4 | 14 | 12 | 6 | 72,400 coins |
| 5 | 18 | 14 | 9 | 23,000 XP |
| 6 | 20 | 15 | 9 | 1 key |
| 7 | 22 | 17 | 10 | 44,000 food |
| 8 | 26 | 20 | 12 | 230,000 XP |
| 9 | 30 | 23 | 15 | 3 keys |

Run 5 used 66 of 118 mismatches. Two of level 5's nine were an agent slip
(two tile positions swapped in the notes), not misreads. Levels 1 and 2 were
cleared with no mismatches because every sweep pair happened to match.

Before a paid replay, a "Top Rewards Remaining" panel lists the best prizes
still in the pool. Before run 3 it showed 1 diamond, 3 keys, 44,000 food,
362,000 coins, and 1 key; run 3 won everything on it except the diamond.

Tile faces are monsters, Dipsters, and resources (coins, food, XP, shards,
diamonds). Rare and Epic variants of a monster are different faces: a Rare
Drumpler does not match a Common Drumpler, and a white Bowgart does not match
a blue one.

## Is a replay worth it?

Usually not, if diamonds matter. The paid replay on 2026-10-29 cost 2 diamonds
and a full nine-level clear returned only 1 diamond, along with about 485,000
XP, 61,600 food, and 9 shards. The second paid replay (run 3) returned no
diamonds: 362,000 coins, 45,800 food, 105 shards, 4 keys, and 2,300 XP. The
third (run 4, 2026-10-30) also returned no diamonds: 434,400 coins, 61,600
food, 2,396 shards, and 2,300 XP. Two of three paid replays have lost the full
2 diamonds and the third lost 1. Play
the free daily game; do not suggest paying for a replay unless the player wants
the coins, food, shards, or keys more than the diamonds. The "Top Rewards
Remaining" panel shows whether a diamond is still in the pool before paying.

## Strategies

Three strategies are named so runs can be compared. Strategy 1 (run 2),
Strategy 2 (run 3, levels 1 to 7, and run 4, all nine levels), and Strategy 3
(run 5, all nine levels) have all been played.

| | Strategy 1: match as you go | Strategy 2: sweep, then match | Strategy 3: sweep into one map |
| --- | --- | --- | --- |
| Flips | One unseen tile, then its known partner or another unseen tile | Tiles in reading order, two at a time, matching known pairs as they appear | Every tile in reading order, two at a time, with no matching until the whole board is mapped |
| Looks | After every flip | After every pair of flips | After every pair, then one complete map |
| Mismatches | Only first sightings; 44 of 118 on the full run | About half the tiles minus lucky pairs; 45 of 75 on levels 1 to 7 (run 3), 75 of 118 on all nine (run 4) | Same as Strategy 2, plus the forced last pair; 66 of 118 (run 5) |
| Agent round trips | About one per one or two flips | Three to four per level; about 30 for run 4 | Two to four per level; about 30 for run 5 |

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

Run 3 bore this out. Levels 1 to 7 took about 25 calls in all, and no
matching flip ever missed. Every level stayed well inside its allowance; the
tightest was level 6 (10 of 15). Two details made it work:

- Pairs known before the sweep ends can be matched in the next batch, ahead
  of the remaining sweep pairs, since matched flips need no pause.
- The last unseen pair never needs a sweep: once every other face is known,
  the two remaining tiles must match each other.

Strategy 2 used about the same number of mismatches as Strategy 1 (45 on
levels 1 to 7, against 44 for all nine levels of run 2) with roughly a sixth
of the calls.

Run 4 played all nine levels this way and stayed inside every allowance; the
tightest was level 7 (11 of 17).

### Strategy 3: sweep into one map

1. Flip two tiles, record both faces at their positions in a grid, pause so
   they flip back, then flip the next two. Repeat until every tile on the
   board has been recorded, in text or as one stitched screenshot.
2. Only then go back and flip every pair from the map.

Unlike Strategy 2, nothing is matched during the sweep, even when both halves
of a pair have already been seen. The map is the single source for matching,
which matters most for look-alikes such as Common, Rare, and Epic variants.

Run 4 was meant to test this but did not: it matched known pairs between
sweep batches, row by row, as in Strategy 2. Its numbers are Strategy 2
numbers.

Run 5 played it as written, on all nine levels:

- Every level stayed inside its allowance; the tightest was level 5 (9 of
  14, two of them an agent slip).
- Once a map was complete, no matching flip missed on its face. Look-alikes
  were told apart on the map before any matching: a green and a blue
  cyclops (level 6), two orange monsters (level 7), and two horn monsters
  that differ only in the rider (level 9).
- Sweeping the last unseen pair costs one mismatch that Strategy 2 avoids by
  elimination. On level 5 the map already showed what the last two tiles had
  to be.
- The one costly error was in the notes, not the reading: two tiles' tap
  positions were swapped when the pairs were written out. Keying the map by
  tap coordinate, not by a row-letter label, removed it for levels 6 to 9.
- Round trips were about the same as Strategy 2: sweep batches of four pairs
  (about 32 actions), then one batch of all matches per level.

Strategy 3 is as cheap as Strategy 2 and reads look-alikes more safely. A
sensible blend is Strategy 3 with the last pair taken by elimination.

### Agent usage by strategy

Token totals for each agent-played run, measured from the session
transcripts. "Weighted" is a rough single cost figure: context re-read
(cache read) at 0.1, context written (cache write) at 1.25, and output at 5,
in input-token units.

| Run | Strategy | Levels played by agent | Model calls | Context re-read | Context written | Output | Weighted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1 | 9 | 164 | 100.3M | 1.30M | 49.5k | ~11.9M |
| 3 | 2 | 7 | 33 | 5.5M | 0.21M | 26.5k | ~0.9M |
| 4 | 2 | 9 | 59 | 21.9M | 4.89M | 42.5k | ~8.5M |
| 5 | 3 | 9 | 47 | 11.9M | 0.39M | 41.2k | ~1.9M |

- Strategy 1 costs the most by far: every flip waits on the last
  screenshot, so each of 164 calls re-reads the whole conversation.
- Strategies 2 and 3 cost about the same per level. Run 3 was cheapest per
  level (about 0.13M against about 0.21M for run 5).
- Run 4 cost about 4.5 times run 5 for the same nine levels. Most of it was
  context written: a 70-action batch overflowed and had to be recovered from
  disk, and a usage-limit pause fell mid-game.
- Conversation length is the biggest confounder. Run 5 started right after a
  context summary; runs 2 and 4 ran late in long sessions. The gap between
  Strategies 2 and 3 is within that noise; the gap to Strategy 1 is not.

For the lowest usage: Strategy 2 or 3, started in a fresh or recently
summarized session, with batches of about 35 actions.

### Open questions

- Whether unused mismatches affect anything (the prize tier or prizes). If
  they do not, Strategy 1's lower mismatch count has no in-game value and
  Strategies 2 and 3 win on cost. Runs 3, 4, and 5 used more mismatches than
  run 2 and won no diamond, but prizes are drawn per play, so this is not
  settled.

Settled by run 3: flips sent while a mismatched pair is still flipping back
are ignored. See the pause rule under Driving it in BlueStacks.

## Driving it in BlueStacks

- Name tiles by their tap coordinates and keep a running list of known
  faces keyed the same way. Row-letter labels invite swapping two
  positions when the matching batch is written (run 5, level 5).
- Take a `zoom` of the board right after each flip, in the same batch,
  before the tile turns back over. A batch of "flip, zoom, flip, zoom" works.
- After a mismatch, the game ignores taps until the pair has turned back
  over. In a batch, put five `screenshot` actions at 0.1 scale between a
  mismatched pair and the next flip; that pause never missed in run 3.
  `zoom` actions are too quick to serve as the pause. Matched pairs need no
  pause, so a batch of known pairs can be flipped back to back.
- Keep each batch to about 35 actions. A 70-action batch in run 4 overflowed
  the tool output and its zooms were dropped from view. The images were still
  saved under the session's `tool-results` folder and could be read back, but
  a smaller batch avoids the detour.
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
