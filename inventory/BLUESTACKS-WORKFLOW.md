# Reading the game in BlueStacks

The player runs My Singing Monsters in BlueStacks Air on the Mac. An agent with
computer-use access can read the Book of Monsters, the Market, and the castle
panel directly, rather than waiting for screenshots. This page is the field
manual for that: where to tap, what each screen proves, and what it cannot.

It complements `inventory/REINDEXING.md`, which says how evidence becomes YAML.
This page covers how to collect the evidence.

First worked through on 2026-10-29 for Plant Island.

## Ground rules

- Read only. Never tap Upgrade, Speed Up, Buy, a price, a green `+` next to a
  currency, Buyback, or anything else that spends coins, diamonds, keys, or
  tokens. If a tap opens a purchase or ad prompt, close it with the red X.
- Ask the player which island is shown if the screen does not name it. The
  castle Bio and the Book page title do name it.
- Report findings as Observed / Uncertain / Interpreted / Proposed, and show
  the YAML diff and bed audit change before committing.
- Save the screenshots that back a YAML change under `training/screenshots/`
  with a dated, descriptive name, and cite them in the island YAML `notes`.

## Driving BlueStacks

- `request_access` for `BlueStacks` (bundle `com.now.gg.BlueStacks`), then use
  the background tools: `app_screenshot`, `app_batch`, `app_zoom`. The player
  keeps working in other apps.
- The game is one canvas with no accessibility elements, so tap by coordinate
  in the 1456x831 screenshot frame. Coordinates below assume the window size
  used on 2026-10-29; re-derive them from a fresh screenshot if it changes.
- Clicks are refused while the player is typing elsewhere. When a batch stops
  for that reason, take a fresh screenshot before continuing: the batch may
  have left a Book entry or panel open.
- `app_batch` has no wait action. Put a `screenshot` or `zoom` between steps
  instead, and zoom on small text (counts, names) before reading it.
- Tapping a spot on the island can hit a bubble rather than the building under
  it. Over the castle, one bubble opens a video-ad Spin Wheel offer (decline
  it with the red X) and the brain bubble opens the free Memory Game. Tap the
  castle body when you want the castle itself.
- The game can reload to its title screen ("Downloading Game Data") and come
  back on a different island or event screen. Re-screenshot and re-orient.

## Island overview

The bottom toolbar (after any panel is closed) has COLLECTION (the Book), MAP,
MAILBOX, FRIENDS, MARKET (about 1124, 740), INFO, and OPTIONS. EXIT at the
bottom right of most full-screen menus (about 1367, 745) returns to the island.

- The island opens zoomed in close. The mouse wheel does not zoom, and the
  round minus button at the bottom left opens a Google Play menu, not zoom.
  Pan by dragging on bare ground or sky, away from monsters; there is no
  known way yet to zoom out from the agent side. When searching for
  something specific, asking the player to center it is much faster.
- COLLECT ALL (bottom right, about 1366, 595) asks for confirmation, then
  gathers coins from every monster and clears the coin bags that hide them.
  It spends nothing. Only use it when the player asks.
- Tapping a monster centers the view on it and opens an action bar after a
  short animation. Take a screenshot after the bar settles before tapping
  again: taps during the animation land on whatever slid under them (a tap
  meant for INFO once opened OPTIONS).
- A monster's action bar holds BOX IT, TELEPORT, FEED (costs coins), MUTE,
  COLLECT, COSTUMES, BIGGIFY, MOVE, and INFO (far right). Only INFO is safe.
  The selected monster's name shows above the bar.
- INFO opens Bio, Likes, and Stats. Stats gives Species, Class, and Beds
  Required, which settles what a monster is when costumes disguise it.
  SELL sits directly left of CLOSE in this panel: tap CLOSE (the red X)
  deliberately.
- Costumes can make one monster look like another. On Plant Island a Noggin
  in a costume with a red button looks like a Wubbox; check INFO before
  trusting artwork.
- A placed Wubbox is a tan box with chimneys, a red button, and a dark
  doorway. Its action bar is INVENTORY, MOVE, INFO, HELP, and an unfilled one
  shows `???` for Rate and Max in its Stats.
- A Wubbox's INVENTORY lists the monsters it needs: boxed ones in color,
  missing ones as black silhouettes. It has two pages; swiping inside the
  panel does nothing, so drag the scroll handle below the grid (about 583,
  668) to the right end (about 870, 668). FILL, left of CLOSE, fills the
  Wubbox with a paid item; never tap it. Boxed monsters are inside the
  Wubbox, not on the island, and do not appear in Market owned counts.
- The Nursery shows a progress bar above it while an egg incubates; record
  that egg under `pending`.

## Castle panel

1. Tap the castle body (not a bubble above it). A bar shows its name with INFO
   and UPGRADE buttons. Tap INFO (bottom right, about 1245, 745), never UPGRADE.
2. The Bio tab names the castle tier and the island.
3. The Stats tab shows Beds Occupied and Max Beds. Record them as
   `castle.observed_beds_occupied` and `castle.observed_beds_available`.
4. Close the panel with the red X.

## Book of Monsters

Open it from COLLECTION. Each island has a Commons, Rares, and Epics page; the
arrow buttons at the bottom left (about 225, 738) and bottom right (about 1203,
738) move between them.

Each page shows three counters: discovered over total, seasonal, and costumes.
Record them under `book` in the island YAML.

Each figure is in one of three states:

| State | Meaning |
| --- | --- |
| In color | Discovered |
| Pulsing between dark and light | Not discovered, but available now to buy or breed |
| Static grey or black | Not discovered and not available now |

- To see pulsing, take four or five `app_zoom` frames of the figure group in a
  single batch and compare them. Very dark figures change only slightly.
- Name every figure by tapping it: its Book entry opens with the name in the
  top-left banner (zoom on region 130,130 to 470,210). Tap BACK (about 1350,
  742) to return. Do not name figures from their artwork.
- The count of lit figures should equal the page's discovered number. If not,
  find the mismatch before editing YAML.
- Anomaly: a Common Wubbox that has been bought but is still being filled
  with monsters shows grey, not lit. It is owned but not yet discovered, and
  should light up once filled.
- On 2026-10-29 almost every unlit Epic silhouette appeared to pulse, unlike
  the Rare page. Treat Epic pulsing as unconfirmed until checked more slowly.

The Book proves discovery, not ownership. Lit does not mean on the island now.

## Market inventory

The Market's Monsters tab is the best source for current owned counts on the
current island.

1. MARKET, then MONSTERS (the green monster tile, about 333, 290).
2. Each card shows the monster name and variant at the top, a price, and the
   owned count in the top-right corner of the card.
3. Scroll right by dragging across the top band of the screen:
   `drag` from (1100, 180) to (450, 180). The list carries some momentum, so
   this gives about two cards of overlap between screenshots. Screenshot after
   every drag and transcribe each card as name + variant + count together.
4. Keep going until the list stops moving. The order seen on 2026-10-29 was
   limited-time offers and prizes first, then Rares and Epics, then Commons,
   Dipsters, and finally Wubbox and Buyback cards.
5. Go BACK and EXIT when done.

What the cards prove:

- A visible count is the current owned count; prefer it over island visual
  counts.
- A missing card does not prove zero (the monster may just not be offered).
- Only one Common Wubbox can be bought per island. Once it is bought, its
  card is greyed out with no count, so a greyed Wubbox card means owned: 1.
- Locked prize cards ("Requires N Prize wins to unlock") still show a count.
- Ignore Buyback cards: they show past sales, not current inventory.

Afterwards, diff the transcribed counts against the island YAML, apply only
the rows that differ, regenerate with `bin/inventory`, and check the castle
bed audit. On Plant Island the Market counts brought the audit delta to 0.

## Minigames

The Dipster minigame has its own guide in
`reference/minigames/dipster-minigame.md`, and the Memory Game in
`reference/minigames/memory-game.md`.
