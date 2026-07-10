# Island-Scoped Breeding Correction

## Mistake

The assistant suggested using Water Island to breed Maw.

That was wrong.

The assistant inferred breedability from monster elements:

```text
Maw = Cold + Water
therefore Water Island can breed Maw
```

## User correction

The user checked the Book of Monsters for Water Island and did not see Mammott or Toe Jammer there.

That correction exposed the real rule:

```text
element composition is not enough
breedability is island-scoped
```

## Correct rule

Do not infer that a monster can be bred on an island merely because one of its elements matches that island.

Use island-scoped breeding data:

```text
island -> available Book of Monsters -> valid parent pair -> possible child
```

## Example

Maw's listed best parents are:

```text
Toe Jammer + Mammott
```

Maw is listed for:

```text
Plant Island
Cold Island
Air Island
Fire Oasis
```

So Maw should not be recommended for Water Island unless a verified source says Water Island can breed it.

## Recognition lesson

When answering breeding questions, the workbench should check structured breeding data before recommending an island.
