# Breeding Rules

This file records breeding semantics that are broader than a single island-scoped parent pair.

The combo table in `common-natural-breeding.json` answers:

```text
Given an island and a parent pair, what known result is listed?
```

This file answers a different question:

```text
Given a parent pattern, is the result guaranteed, probabilistic, or useful for duplicate farming?
```

These rules are useful for zapping, vessel filling, Wublin waking, Celestial inventories, Amber Island planning, and avoiding wasted breeder time.

## Guaranteed or special-case breeding rules

### Common + Rare same-monster clone

If a Common monster is bred with its Rare counterpart, the result is guaranteed to be that same monster family.

```text
Common Furcorn + Rare Furcorn -> Furcorn
Common Maw + Rare Maw -> Maw
```

Use this as a duplicate-farming rule once both forms are available.

Notes:

- The expected duplicate is usually the Common version.
- During availability windows, Rare/Epic behavior may be event-dependent.
- Treat this as a strong duplicate strategy, not a generic new-monster discovery rule.

### Natural single + Natural single -> Natural double

Core Natural double-element monsters bred from two Natural single-element parents are guaranteed.

```text
Noggin + Toe Jammer -> Fwog
Noggin + Mammott    -> Drumpler
Toe Jammer + Mammott -> Maw
Tweedle + Potbelly  -> Dandidoo
Tweedle + Noggin    -> Cybop
Tweedle + Toe Jammer -> Quibble
Tweedle + Mammott   -> Pango
Potbelly + Noggin   -> Shrubb
Potbelly + Toe Jammer -> Oaktopus
Potbelly + Mammott  -> Furcorn
```

Important distinction:

- This guarantee applies to core Natural doubles.
- Do not automatically extend it to Fire or Magical double-element monsters.
- Non-Natural doubles may fail back to a parent.

### Quad + Single -> Single duplicate

A Quad-element monster bred with a Single-element monster produces the Single-element parent.

```text
Entbrat + Potbelly -> Potbelly
Deedge + Tweedle   -> Tweedle
```

Use this as a single-element farming shortcut when the island supports the pair.

### Shugafam + Shugabush clone

This rule is useful but currently marked for verification.

Claim:

```text
Shugafam monster + Shugabush -> same Shugafam monster
```

Example claim:

```text
Shugarock + Shugabush -> Shugarock
```

Status:

```text
needs_verification
```

Do not treat this as a hard guaranteed rule until it is confirmed by source evidence or our own observed training evidence.

## Confidence labels

```text
source_supported:
  Supported by external reference and consistent with observed game behavior.

observed:
  Confirmed directly in our screenshots/session evidence.

needs_verification:
  Plausible or externally suggested, but not yet confirmed enough for hard automation.

do_not_generalize:
  Useful warning that similar-looking logic should not be applied broadly.
```
