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
  it. Over the castle, bubbles open a video-ad Spin Wheel offer or the Memory
  Game; decline both with the red X and tap the castle body instead.
- The game can reload to its title screen ("Downloading Game Data") and come
  back on a different island or event screen. Re-screenshot and re-orient.

## Island overview

The bottom toolbar (after any panel is closed) has COLLECTION (the Book), MAP,
MAILBOX, FRIENDS, MARKET (about 1124, 740), INFO, and OPTIONS. EXIT at the
bottom right of most full-screen menus (about 1367, 745) returns to the island.

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
`reference/minigames/dipster-minigame.md`.
