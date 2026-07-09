# Training

This directory preserves the learning loop behind MSM Cognition.

The project is not only tracking game state. It is also recording how a domain-specific visual interface is interpreted over time: screenshots, observations, mistakes, corrections, terminology, and recognition rules.

## Why this matters

The game is the testbed, but the deeper project is the training loop.

This directory records how a human teaches an assistant to understand a domain-specific interface:

1. ask the assistant to interpret what it sees
2. correct mistakes directly
3. clarify domain terminology
4. separate visible facts from uncertain interpretation
5. preserve the correction as future operating procedure

That makes the work fun, educational, and enduring. The user gets to play the game, the project records how better teaching happens, and future readers can apply the same pattern to their own domains.

## Purpose

Training material captures how the workbench learns.

A typical loop is:

```text
screenshot
  -> assistant observation
  -> user correction
  -> recognition rule
  -> structured state patch
  -> generated reference documentation
```

Mistakes are preserved when they teach the system something useful.

## Layout

```text
screenshots/    Screenshot files saved locally and committed by the user
observations/   Markdown records of what was seen in a screenshot
corrections/    User corrections and recognition lessons
language/       Domain terminology and naming conventions
```

## Current implementation note

The assistant can help create and update text artifacts such as Markdown and YAML-style records.

Binary screenshot files should be saved into this repo from the user's machine, then committed normally. This keeps the workflow explicit and avoids pretending the assistant can directly manage every local binary artifact.
