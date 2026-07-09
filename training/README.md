# Training

This directory preserves the learning loop behind MSM Cognition.

The project is not only tracking game state. It is also recording how a domain-specific visual interface is interpreted over time: screenshots, observations, mistakes, corrections, terminology, and recognition rules.

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
